"""
Конфигурация логгирования ArcSight
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import cached_property
from inspect import Signature, signature
from logging import getLevelNamesMapping
from typing import Callable, Literal
from uuid import uuid4

from pydantic_settings import BaseSettings, SettingsConfigDict

from aiokafka_agent.infra.context.globals import g


LEVEL_MAPPING = getLevelNamesMapping()


class LoggerConfig(BaseSettings):
    """
    Настройки постгреса
    """

    model_config = SettingsConfigDict(env_prefix="APP_LOG_")

    LEVEL: Literal[
        "CRITICAL",
        "FATAL",
        "ERROR",
        "WARNING",
        "WARN",
        "INFO",
        "DEBUG",
        "NOTSET",
    ] = "DEBUG"
    NAME: str = "consumer"

    ARC_SIGHT_ENABLED: bool = True
    JSON_FORMATTER_ENABLED: bool = True
    PLAINSTR_ENABLED: bool = True
    PLATFORM_ENABLED: bool = True

    @cached_property
    def log_level_int(self) -> int:
        """
        Интовое представление уровня логирования
        """
        return LEVEL_MAPPING[self.LEVEL]


logger_conf = LoggerConfig()


class ConfigJournalEntry(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_JOURNAL_ENTRY_")
    CEF_VERSION: str = "CEF:0"
    VENDOR: str = "VENDOR"
    PRODUCT: str = "PRODUCT"
    PRODUCT_ID: str = "PRODUCT_ID"
    VERSION: str = "1.0"


config_journal_entry = ConfigJournalEntry()


class EventClass(str, Enum):
    view = "view"
    create = "create"
    edit = "edit"
    calc = "calc"
    calc_self = "calc_self"
    logout = "logout"
    login = "login"
    login_successful = "login_successful"
    file_upload = "file_upload"
    calc_other = "calc_other"
    file_download = "file_download"
    delete = "delete"
    login_unsuccessful = "login_unsuccessful"
    error = "error"


event_class_to_severity: dict[EventClass, int] = {
    EventClass.view: 3,
    EventClass.create: 3,
    EventClass.edit: 3,
    EventClass.calc_self: 3,
    EventClass.logout: 3,
    EventClass.login_successful: 6,
    EventClass.file_upload: 6,
    EventClass.calc_other: 6,
    EventClass.file_download: 6,
    EventClass.delete: 8,
    EventClass.login_unsuccessful: 8,
    EventClass.error: 8,
}


@dataclass
class JournalEntry:
    """
    Объект для логгирования (CEF/JSON).
    На compute-сервисе нет FastAPI Request, поэтому заполняемся из g['journal_context'].
    """

    event_class: EventClass
    name: str
    message: str

    success: bool = True
    level: str = "INFO"
    status_code: int = 200

    # тела выключены по умолчанию: их на compute обычно нет
    request_body: str | None = None
    response_body: str | None = None
    traceback_str: str | None = None
    object_id: str | None = None
    object_type: str | None = None
    file_name: str | None = None

    severity: int = field(init=False)

    # сеть
    source_host_name: str | None = field(default=None, init=False)
    source_address: str | None = field(default=None, init=False)
    destination_address: str | None = field(default=None, init=False)

    # пользователь/роль
    user_id: str | None = field(default=None, init=False)
    username: str | None = field(default=None, init=False)
    ad_roles: set[str] | None = field(default_factory=set, init=False)
    human_readable_roles: list[str] | None = field(default_factory=list, init=False)

    # session/jwt
    session_id: str | None = field(default=None, init=False)

    # platform meta
    company: str | None = field(default=None, init=False)
    project_name: str | None = field(default=None, init=False)
    project_id: str | None = field(default=None, init=False)

    # роли уже в виде строк (табличные имена)
    role: str | None = field(default=None, init=False)
    role_AD: str | None = field(default=None, init=False)

    # correlation id
    correlation_id: str | None = field(default=None, init=False)

    # HTTP шапка
    http_method: str | None = field(default=None, init=False)
    endpoint: str | None = field(default=None, init=False)

    audit_date_time: str = field(default=None, init=False)

    log_id: str = field(default_factory=lambda: str(uuid4()), init=False)

    def __post_init__(self):
        self.severity = event_class_to_severity[self.event_class]
        self._normalize_event_class()
        self._fill_from_context()
        self._fill_platform_meta()

    def _normalize_event_class(self) -> None:
        if self.event_class in (EventClass.calc_self, EventClass.calc_other):
            self.event_class = EventClass.calc
        if self.event_class in (
            EventClass.login_successful,
            EventClass.login_unsuccessful,
        ):
            self.event_class = EventClass.login

    def _fill_from_context(self) -> None:
        """
        Берём всё, что пришло из бэка в g['journal_context'].
        """
        ctx: dict = g.get("journal_context", {}) or {}
        # correlation
        self.correlation_id = ctx.get("correlation_id") or g.get("correlation_id")

        # http
        self.http_method = ctx.get("http_method")
        self.endpoint = ctx.get("endpoint")

        # network
        self.source_host_name = ctx.get("source_host_name")
        self.source_address = ctx.get("source_address")
        self.destination_address = ctx.get("destination_address")
        # session
        self.session_id = ctx.get("session_id")

        # user
        self.user_id = ctx.get("user_id")
        self.username = ctx.get("username")
        ad_roles = ctx.get("ad_roles") or []
        human_roles = ctx.get("human_readable_roles") or []
        self.ad_roles = set(ad_roles)
        self.human_readable_roles = list(human_roles)

        # роль/строковые агрегаты для платформенного формата (если нужны)
        self.role = (
            ",".join(self.human_readable_roles) if self.human_readable_roles else None
        )
        self.role_AD = ",".join(sorted(self.ad_roles)) if self.ad_roles else None

        self.audit_date_time = self.current_datetime_str()

    def _fill_platform_meta(self) -> None:
        self.company = config_journal_entry.VENDOR
        self.project_name = config_journal_entry.PRODUCT
        self.project_id = config_journal_entry.PRODUCT_ID

    @staticmethod
    def get_annotations(endpoint: Callable) -> tuple[str | None, str | None]:
        signature_ = signature(endpoint)
        param_annotation = None
        if "params" in signature_.parameters:
            param_annotation = str(signature_.parameters["params"].annotation)
        return_annotation = None
        if signature_.return_annotation is not Signature.empty:
            return_annotation = str(signature_.return_annotation)
        return param_annotation, return_annotation

    @staticmethod
    def current_datetime_str() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

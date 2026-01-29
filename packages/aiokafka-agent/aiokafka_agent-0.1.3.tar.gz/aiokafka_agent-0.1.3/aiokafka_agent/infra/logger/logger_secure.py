"""
Логгер Arcsight
"""

from typing import Any

from aiokafka_agent.infra.logger.config import EventClass, JournalEntry
from aiokafka_agent.infra.logger.formatter import (
    additional_formatter,
    long_formatter,
    short_formatter,
)
from aiokafka_agent.infra.logger.formatters.base_formatter import BaseFormatter
from aiokafka_agent.infra.logger.logger import print_json_log, print_log


class LoggerSecure:
    """
    Логгер, формирующий CEF-строку и JSON-лог.
    """

    def __init__(self, formatters: list[BaseFormatter]) -> None:
        self.formatters = formatters

    def _prepare_log_data(self, entry: JournalEntry) -> dict[str, Any]:
        log_data = {}
        for formatter in self.formatters:
            log_data[formatter.key] = formatter.as_log_data(entry)
        return log_data

    @print_log
    @print_json_log
    def view(
        self,
        name: str,
        value: Any,
        object_id: str | None = None,
        object_type: str | None = None,
    ) -> dict[str, Any]:
        return self._prepare_log_data(
            JournalEntry(
                event_class=EventClass.view,
                name=f"View {short_formatter(name, value)}",
                message=f"Просмотрен {long_formatter(name, value)} = {value}",
                object_id=object_id,
                object_type=object_type,
            ),
        )

    @print_log
    @print_json_log
    def create(self, name: str, value: Any) -> dict[str, Any]:
        return self._prepare_log_data(
            JournalEntry(
                event_class=EventClass.create,
                name=f"Create {short_formatter(name, value)}",
                message=f"Создан {long_formatter(name, value)} = {value}",
            ),
        )

    @print_log
    @print_json_log
    def edit(
        self,
        name: str,
        value: Any,
        param_name: str,
        param_old: Any | None = None,
        param_new: Any | None = None,
    ) -> dict[str, Any]:
        return self._prepare_log_data(
            JournalEntry(
                event_class=EventClass.edit,
                name=f"Edit {short_formatter(name, value)}",
                message=f"Изменен параметр {param_name} в {long_formatter(name, value)}"
                f" = {value}{additional_formatter(param_new, param_old)}",
            ),
        )

    @print_log
    @print_json_log
    def calc_self(
        self,
        name: str,
        value: Any,
        param_name: str,
        param_old: Any | None = None,
        param_new: Any | None = None,
    ) -> dict[str, Any]:
        return self._prepare_log_data(
            entry=JournalEntry(
                event_class=EventClass.calc_self,
                name=f"Calculate {short_formatter(name, value)}",
                message=f"Запущен расчет {param_name} {long_formatter(name, value)}"
                f" = {value}{additional_formatter(param_new, param_old)}",
            ),
        )

    @print_log
    @print_json_log
    def logout(self) -> dict[str, Any]:
        return self._prepare_log_data(
            JournalEntry(
                event_class=EventClass.logout,
                name="System logout",
                message="Выполнен выход из системы",
            ),
        )

    @print_log
    @print_json_log
    def login_successful(self) -> dict[str, Any]:
        return self._prepare_log_data(
            JournalEntry(
                event_class=EventClass.login_successful,
                name="System login",
                message="Выполнен вход в систему",
            ),
        )

    @print_log
    @print_json_log
    def file_upload(
        self,
        name: str,
        value: Any,
        param_name: str,
        file_name: str,
    ) -> dict[str, Any]:
        return self._prepare_log_data(
            JournalEntry(
                event_class=EventClass.file_upload,
                name=f"Upload file to {short_formatter(name, value)}",
                message=f"В параметр {param_name} в {long_formatter(name, value)} = {value} загружен файл {file_name}",
                file_name=file_name,
            ),
        )

    @print_log
    @print_json_log
    def calc_other(
        self,
        name: str,
        value: Any,
        param_name: str,
        param_old: Any | None = None,
        param_new: Any | None = None,
    ) -> dict[str, Any]:
        return self._prepare_log_data(
            JournalEntry(
                event_class=EventClass.calc_other,
                name=f"Calculate {short_formatter(name, value)}",
                message=f"Запущен расчет {param_name} {long_formatter(name, value)}"
                f"  = {value}{additional_formatter(param_new, param_old)}",
            ),
        )

    @print_log
    @print_json_log
    def file_download(
        self,
        name: str,
        value: Any,
        file_name: str,
    ) -> dict[str, Any]:
        msg = f"Выгружен файл {file_name} {long_formatter(name, value)} = {value}"
        return self._prepare_log_data(
            JournalEntry(
                event_class=EventClass.file_download,
                name=f"Download {short_formatter(name, value)}",
                message=msg,
                file_name=file_name,
            ),
        )

    @print_log
    @print_json_log
    def delete(self, name: str, value: Any) -> dict[str, Any]:
        return self._prepare_log_data(
            JournalEntry(
                event_class=EventClass.delete,
                name=f"Delete {short_formatter(name, value)}",
                message=f"Удален {long_formatter(name, value)} = {value}",
            ),
        )

    @print_log
    @print_json_log
    def login_unsuccessful(self) -> dict[str, Any]:
        return self._prepare_log_data(
            JournalEntry(
                event_class=EventClass.login_unsuccessful,
                name="System login",
                message="Неудачная попытка входа в систему",
                success=False,
                level="WARNING",
            ),
        )

    @print_json_log
    def log_error(
        self,
        name: str,
        message: str,
        status_code: int = 500,
        request_body: str | None = None,
        response_body: str | None = None,
        traceback_str: str | None = None,
    ) -> dict[str, Any]:
        return self._prepare_log_data(
            JournalEntry(
                event_class=EventClass.error,
                name=name,
                message=message,
                success=False,
                level="ERROR",
                status_code=status_code,
                request_body=request_body,
                response_body=response_body,
                traceback_str=traceback_str,
            ),
        )

from json import dumps

from aiokafka_agent.infra.logger.config import ConfigJournalEntry, JournalEntry
from aiokafka_agent.infra.logger.formatters.base_formatter import BaseFormatter


class PlatformJsonFormatter(BaseFormatter):
    """
    JSON для платформы контейнеризации.
    Читает готовые поля из JournalEntry.
    """

    KEY = "platform_json"

    @property
    def key(self) -> str:
        return self.KEY

    def __init__(self, config: ConfigJournalEntry):
        self.config = config

    def as_log_data(self, entry: JournalEntry) -> str:
        data = {
            "user_id": str(entry.user_id) if entry.user_id else None,
            "role": entry.role,
            "role_AD": entry.role_AD,
            "company": entry.company,
            "project_name": entry.project_name,
            "file_name": entry.file_name,
            "project_id": entry.project_id,
            "msg": entry.name,
            "details": entry.message,
            "session_id": entry.session_id,
            "level": entry.level,
            "traceback": entry.traceback_str,
            "http_method": entry.http_method,
            "endpoint": entry.endpoint,
            "status_code": entry.status_code,
            "request_body": entry.request_body,
            "response_body": entry.response_body,
            "corellationID": entry.correlation_id,
            "json_valid": True,
        }
        data = {k: v for k, v in data.items() if v is not None}
        return dumps(data, ensure_ascii=False)

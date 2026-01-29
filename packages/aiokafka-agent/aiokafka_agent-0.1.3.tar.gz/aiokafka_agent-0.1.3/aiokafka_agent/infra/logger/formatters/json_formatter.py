from json import dumps

from aiokafka_agent.infra.logger.config import ConfigJournalEntry, JournalEntry
from aiokafka_agent.infra.logger.formatters.base_formatter import BaseFormatter


class JsonFormatter(BaseFormatter):
    """
    Формирует JSON-структуру для вывода в лог.
    """

    KEY = "json"

    @property
    def key(self) -> str:
        return self.KEY

    def __init__(self, config: ConfigJournalEntry):
        self.config = config

    def as_log_data(self, entry: JournalEntry) -> str:
        data = {
            "id": entry.log_id,
            "audit_date_time": entry.audit_date_time,
            "user_id": str(entry.user_id) if entry.user_id else None,
            "user_name": entry.username,
            "login": entry.username,
            "role": entry.role,
            "role_AD": entry.role_AD,
            "company": entry.company,
            "project_name": entry.project_name,
            "project_id": entry.project_id,
            "msg": entry.name,
            "details": entry.message,
            "level": entry.level,
            "source_address": entry.source_address,
            "source_host_name": entry.source_host_name,
            "destination_address": entry.destination_address,
            "http_method": entry.http_method,
            "endpoint": entry.endpoint,
            "success": entry.success,
            "session_id": entry.session_id,
            "status_code": entry.status_code,
            "request_body": entry.request_body,
            "response_body": entry.response_body,
            "traceback": entry.traceback_str,
            "object_id": entry.object_id,
            "object_type": entry.object_type,
            "json_valid": True,
        }
        data = {k: v for k, v in data.items() if v is not None}
        return dumps(data, ensure_ascii=False)

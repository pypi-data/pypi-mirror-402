from datetime import UTC, datetime

from aiokafka_agent.infra.logger.config import ConfigJournalEntry, JournalEntry
from aiokafka_agent.infra.logger.formatters.base_formatter import BaseFormatter


class ArcsightFormatter(BaseFormatter):
    """
    Формирует строку в формате CEF для ArcSight.
    """

    KEY = "cef"

    @property
    def key(self) -> str:
        return self.KEY

    def __init__(self, config: ConfigJournalEntry):
        self.config = config

    def as_log_data(self, entry: JournalEntry) -> str:
        """
        Возвращает сформированную CEF-строку.
        """
        now_utc = datetime.now(UTC)
        now_iso = now_utc.replace(tzinfo=UTC).isoformat()
        now_timestamp = now_utc.timestamp()

        part_required = (
            f"{self.config.CEF_VERSION}|{self.config.VENDOR}|"
            f"{self.config.PRODUCT}|{self.config.VERSION}|"
            f"{entry.event_class.value}|{entry.name}|{entry.severity}"
        )

        hosts_part = f"src={entry.source_address} dst={entry.destination_address}"

        user_part = ""
        if entry.user_id:
            user_part = f"suid={entry.user_id} suser={entry.username}"

        part_additional = (
            f"{hosts_part} {user_part} msg={entry.message} end={now_timestamp}"
        )

        return f"{now_iso} {part_required}|{part_additional}|"

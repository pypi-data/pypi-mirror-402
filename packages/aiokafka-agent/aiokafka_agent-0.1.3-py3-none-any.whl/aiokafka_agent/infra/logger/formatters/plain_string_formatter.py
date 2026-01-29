from aiokafka_agent.infra.logger.config import ConfigJournalEntry, JournalEntry
from aiokafka_agent.infra.logger.formatters.base_formatter import BaseFormatter


class PlainFormatter(BaseFormatter):
    """
    Формирует структуру для вывода в лог.
    """

    KEY = "plain"

    @property
    def key(self) -> str:
        return self.KEY

    def __init__(self, config: ConfigJournalEntry):
        self.config = config

    def as_log_data(self, entry: JournalEntry) -> str:
        return entry.message

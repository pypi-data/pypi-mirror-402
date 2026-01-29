from abc import ABC, abstractmethod

from aiokafka_agent.infra.logger.config import JournalEntry


class BaseFormatter(ABC):
    @property
    @abstractmethod
    def key(self) -> str:
        """Имя (ключ) форматтера, например 'cef' или 'json'."""

    @abstractmethod
    def as_log_data(self, entry: JournalEntry) -> str:
        """Преобразует объект журнала в форматируемые данные."""

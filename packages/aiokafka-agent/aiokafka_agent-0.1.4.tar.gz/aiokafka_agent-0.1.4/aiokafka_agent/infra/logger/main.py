import logging
from typing import ClassVar, Optional


class LibraryLogger:
    """Класс-контейнер для логгера (без глобальных переменных)"""

    _logger_ref: ClassVar[Optional[logging.Logger]] = None

    @classmethod
    def setup_logger(cls, custom_logger: logging.Logger) -> None:
        """Установить логгер для всей библиотеки"""
        cls._logger_ref = custom_logger
        custom_logger.debug("aiokafka-agent: логгер установлен")

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """Получить логгер (или заглушку)"""
        if cls._logger_ref is not None:
            return cls._logger_ref

        base_logger = logging.getLogger('aiokafka_agent')
        base_logger.addHandler(logging.NullHandler())
        base_logger.propagate = False
        return base_logger


setup_logger = LibraryLogger.setup_logger
get_logger = LibraryLogger.get_logger
logger = get_logger()
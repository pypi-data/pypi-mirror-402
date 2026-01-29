"""
Представление логирования
"""

from logging import Logger

from aiokafka_agent.infra.logger.config import logger_conf
from aiokafka_agent.infra.logger.handler import platform_handler


logger = Logger(name=logger_conf.NAME, level=logger_conf.LEVEL)
logger.propagate = False
logger.handlers = [platform_handler]

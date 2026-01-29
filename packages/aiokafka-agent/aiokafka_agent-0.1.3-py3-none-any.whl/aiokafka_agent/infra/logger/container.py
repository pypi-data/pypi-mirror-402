from aiokafka_agent.infra.logger.config import config_journal_entry, logger_conf
from aiokafka_agent.infra.logger.formatters.arc_sight_formatter import ArcsightFormatter
from aiokafka_agent.infra.logger.formatters.json_formatter import JsonFormatter
from aiokafka_agent.infra.logger.formatters.plain_string_formatter import PlainFormatter
from aiokafka_agent.infra.logger.formatters.platform_json_formatter import (
    PlatformJsonFormatter,
)
from aiokafka_agent.infra.logger.logger_secure import LoggerSecure


CONFIG_FLAGS = [
    (logger_conf.ARC_SIGHT_ENABLED, ArcsightFormatter(config_journal_entry)),
    (logger_conf.JSON_FORMATTER_ENABLED, JsonFormatter(config_journal_entry)),
    (logger_conf.PLATFORM_ENABLED, PlatformJsonFormatter(config_journal_entry)),
    (logger_conf.PLAINSTR_ENABLED, PlainFormatter(config_journal_entry)),
]

logger_secure = LoggerSecure(
    formatters=[
        formatter_class for enabled, formatter_class in CONFIG_FLAGS if enabled
    ],
)

from functools import wraps
from logging import INFO, Formatter, Logger, StreamHandler
from typing import Any, Callable, Union

from aiokafka_agent.infra.logger.config import logger_conf
from aiokafka_agent.infra.logger.formatters.arc_sight_formatter import ArcsightFormatter
from aiokafka_agent.infra.logger.formatters.json_formatter import JsonFormatter
from aiokafka_agent.infra.logger.formatters.plain_string_formatter import PlainFormatter
from aiokafka_agent.infra.logger.formatters.platform_json_formatter import (
    PlatformJsonFormatter,
)


KeysType = Union[str, tuple[str, ...], list[str]]


def display_formatter_log(keys: KeysType, display_function: Callable[[str], None]):
    """
    Логирует payload(ы) из результата по указанному(ым) ключу(ключам).
    """
    # нормализуем кортеж ключей
    if isinstance(keys, str):
        keys_tuple: tuple[str, ...] = (keys,)
    else:
        keys_tuple = tuple(keys)

    def wrapper(func: Callable[..., dict[str, Any]]):
        @wraps(func)
        def wrapped(*args, **kwargs) -> dict[str, Any]:
            result = func(*args, **kwargs)
            for key in keys_tuple:
                value = result.get(key)
                if value:  # не печатаем None/пустое
                    display_function(value)
            return result

        return wrapped

    return wrapper


handler = StreamHandler()
handler.formatter = Formatter(fmt="%(message)s")

logger = Logger(name=logger_conf.NAME, level=INFO)
logger.propagate = False
logger.handlers = [handler]

print_log = display_formatter_log(
    keys=(PlainFormatter.KEY, ArcsightFormatter.KEY),
    display_function=logger.info,
)
print_json_log = display_formatter_log(
    keys=(JsonFormatter.KEY, PlatformJsonFormatter.KEY),
    display_function=logger.info,
)

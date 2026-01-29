from functools import wraps
from typing import Callable, Coroutine

from asyncio.event_loop import safe_get_or_create_event_loop


def async_to_sync(func: Callable | Coroutine) -> Callable:
    """
    Запустить корутину синхронно
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        Обертка
        """
        event_loop = safe_get_or_create_event_loop()

        return event_loop.run_until_complete(func(*args, **kwargs))

    return wrapper

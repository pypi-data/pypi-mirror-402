import asyncio
from datetime import timedelta
from functools import wraps


def human_readable_timedelta(seconds_total: int) -> str:
    """
    Преобразует количество секунд в формат "X д. Y ч. Z мин. W с."
    """
    if seconds_total <= 0:
        return "0 c."

    days, remainder = divmod(seconds_total, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days} д.")
    if hours > 0:
        parts.append(f"{hours} ч.")
    if minutes > 0:
        parts.append(f"{minutes} мин.")
    if seconds > 0:
        parts.append(f"{seconds} с.")

    return " ".join(parts).strip()


def time_limit(limit: timedelta, friendly_name: str | None = None):
    """
    Универсальный декоратор, ограничивающий время выполнения асинхронной функции.
    :param limit: максимальное время (timedelta), отведённое на выполнение.
    :param friendly_name: опционально - человекочитаемое имя,
                          если хотим в сообщении об ошибке выводить
                          что-то более приятное, чем func.__name__.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=limit.total_seconds(),
                )
            except TimeoutError:
                human_readable = human_readable_timedelta(limit.total_seconds())
                raise ValueError(
                    f"{friendly_name or func.__name__}: "
                    f"превышен лимит времени {human_readable}",
                )

        return wrapper

    return decorator

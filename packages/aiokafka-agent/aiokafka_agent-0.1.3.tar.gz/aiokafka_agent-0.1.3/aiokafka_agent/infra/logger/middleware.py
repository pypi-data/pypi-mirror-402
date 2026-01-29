from functools import wraps

from aiokafka_agent.infra.context import g


def journal_context(func):
    """
    Декоратор для добавления в глобальную g journal_context для логирования.
    Для использования необходимо обернуть функцию, которая в теле имеет ключ journal_context
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if kwargs.get("data"):
            if kwargs.get("data").get("journal_context"):
                g.set("journal_context", kwargs.get("data").get("journal_context") or {})
        result = await func(*args, **kwargs)

        return result

    return wrapper
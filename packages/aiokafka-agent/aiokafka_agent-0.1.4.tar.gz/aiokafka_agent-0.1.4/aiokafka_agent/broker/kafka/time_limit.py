import asyncio
from datetime import timedelta
from functools import wraps

from aiokafka_agent.infra.asyncio.time_limit import human_readable_timedelta
from aiokafka_agent.broker.kafka.consumer.types import Topic
from aiokafka_agent.broker.kafka.topic_info import topic_info_config


def time_limit_for_topic(topic: Topic):
    """
    Фабрика декораторов, возвращающая декоратор, который применит таймаут,
    определённый в конфигурации для данного топика.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            topic_info = getattr(topic_info_config, topic.name)
            limit_seconds = topic_info.timeout_seconds
            limit = timedelta(seconds=limit_seconds)

            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=limit.total_seconds(),
                )
            except TimeoutError:
                human_readable = human_readable_timedelta(limit_seconds)
                raise ValueError(
                    f"{topic_info.title}: "
                    f"превышен лимит времени {human_readable} "
                    f"Измените параметры что бы уменьшить время вычисления.",
                )

        return wrapper

    return decorator

from __future__ import annotations

from collections import defaultdict

from aiokafka.structs import ConsumerRecord

from aiokafka_agent.broker.kafka.consumer.descriptor.stream import (
    consumer_record_descriptor,
)
from aiokafka_agent.broker.kafka.consumer.metadata import AppCusterMetadata
from aiokafka_agent.broker.kafka.consumer.types import Group, GroupTopics, Handler
from aiokafka_agent.infra.logger.main import logger


class AgentGroup:
    """
    Инструмент взаимодействия с пулом обработчиков событий из разных топиков
    """

    def __init__(self, consumer_group: str | None = None):
        self._record_handler = None
        self._topics = None
        self._consumer_group = consumer_group

    @property
    def record_handler(self) -> GroupTopics:
        if self._record_handler is None:
            self._record_handler = defaultdict(lambda: defaultdict(set))
        return self._record_handler

    def append_group(self, inst: AgentGroup):
        """
        Добавить значения из другого инстанса
        """
        for group, topic_handlers in inst.record_handler.items():
            for topic, handlers in topic_handlers.items():
                self.record_handler[group][topic].update(handlers)

    def register(self, topic: str):
        """
        Зарегистрировать обработчики топика
        """

        def wrapper(fun: Handler):
            self.record_handler[self._consumer_group][topic].add(fun)

        return wrapper

    async def get_topics(self, consumer_group: Group, cluster_metadata: AppCusterMetadata) -> tuple[str, ...]:
        """
        Получить список зарегистрированных топиков
        """
        registered_topics = set(self.record_handler[consumer_group].keys())
        cluster_topics = set(cluster_metadata.topics)
        intersect_topics = registered_topics.intersection(cluster_topics)

        if len(intersect_topics) != len(registered_topics):
            logger.warning(
                f"Соотношение существующих топиков для группы {consumer_group} к зарегистрированным отличается.\n"
                f"В кластере:{cluster_topics}.\nЗарегистрированные:{registered_topics}.\nПересечение:{intersect_topics}.",
            )

        return tuple(intersect_topics)

    async def call_handlers(self, consumer_group: Group, record: ConsumerRecord):
        """
        Позвать обработчики топика
        """
        handlers = self.record_handler[consumer_group][record.topic]

        for handler in handlers:
            await consumer_record_descriptor.set_group_task(group=consumer_group, record=record)

            logger.info(f"Делигирую обработчику {handler} обработку события {record}")
            await handler(record=record)

            await consumer_record_descriptor.delete_group_task(group=consumer_group)

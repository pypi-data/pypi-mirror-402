from asyncio import gather
from pprint import pformat

from aiokafka import AIOKafkaConsumer

from aiokafka_agent.broker.kafka.client import get_kafka_consumer
from aiokafka_agent.broker.kafka.config import KafkaConfig, kafka_conf
from aiokafka_agent.broker.kafka.consumer.dispatcher import AgentGroup
from aiokafka_agent.broker.kafka.consumer.lifecycle import LifecycleHandler
from aiokafka_agent.broker.kafka.consumer.metadata import get_cluster_metadata
from aiokafka_agent.broker.kafka.consumer.partition import ConsumerStreamHandler
from aiokafka_agent.broker.kafka.consumer.reballance_listner import (
    ConsumerRebalanceListener,
)
from aiokafka_agent.broker.kafka.consumer.schemas import AppCusterMetadata
from aiokafka_agent.broker.kafka.consumer.types import Group
from aiokafka_agent.infra.logger.main import logger


class ConsumerApp:
    """
    Приложение - прикладная часть консьюмера
    """

    def __init__(self):
        self.agents = AgentGroup()
        self.rebalance_listener = ConsumerRebalanceListener()
        self.lifecycle_handler = LifecycleHandler()
        self.kafka_conf: KafkaConfig = kafka_conf

    async def _get_consumer(self, cluster_metadata: AppCusterMetadata, consumer_group: Group) -> AIOKafkaConsumer:
        """
        Создать консьмер
        """
        topics = await self.agents.get_topics(cluster_metadata=cluster_metadata, consumer_group=consumer_group)

        consumer: AIOKafkaConsumer = await get_kafka_consumer(
            kafka_conf=self.kafka_conf, topics=topics, group_id=consumer_group,
        )
        consumer.subscribe(topics=topics, listener=self.rebalance_listener)
        logger.info(
            f"Для группы {consumer_group} зарегистрированы следуюющие топики и им соответствующие обработчики: \n"
            f"{pformat(dict(self.agents.record_handler[consumer_group]), indent=2)}.",
        )

        return consumer

    async def run(self) -> None:
        """
        Запустить
        """
        await self.lifecycle_handler.on_before_start()

        await self.process_streams()

        await self.lifecycle_handler.on_after_stop()

    async def process_streams(self) -> None:
        """
        Обработчик стрима
        """
        cluster_metadata = await get_cluster_metadata(self.kafka_conf)

        streams = []

        for group in self.agents.record_handler.keys():
            consumer = await self._get_consumer(cluster_metadata=cluster_metadata, consumer_group=group)

            streams.append(
                ConsumerStreamHandler(
                    consumer=consumer, group=group, handler_dispatcher=self.agents.call_handlers,
                ).run(),
            )

        await gather(*streams)

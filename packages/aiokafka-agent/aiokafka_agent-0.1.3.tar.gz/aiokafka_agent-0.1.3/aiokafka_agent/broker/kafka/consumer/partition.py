from typing import Awaitable, Callable, Sequence

from aiokafka import AIOKafkaConsumer, ConsumerRecord, TopicPartition

from aiokafka_agent.broker.kafka.consumer.types import Group, HandlerDispatcher
from aiokafka_agent.infra.logger.presenter import logger


class ConsumerStreamHandler:
    def __init__(
        self,
        consumer: AIOKafkaConsumer,
        group: Group,
        handler_dispatcher: HandlerDispatcher,
        record_handlers: Sequence[Callable[[ConsumerRecord], Awaitable[None]] | Callable[[ConsumerRecord], Awaitable]] | None = None,
    ):
        self.consumer = consumer
        self.group = group
        self.handler_dispatcher = handler_dispatcher
        self.record_handlers: list[Callable[[ConsumerRecord], Awaitable]] = list(record_handlers or [])

    async def _process_record(self, record: ConsumerRecord):
        """
        Обработать запись из стрима
        """
        logger.info(f"Получено событие: {record}. Для обработчика группы {self.group}")

        for record_handler in self.record_handlers:
            await record_handler(record)

        tp = TopicPartition(topic=record.topic, partition=record.partition)

        if self.group and tp in self.consumer.assignment():
            self.consumer.pause(tp)

        try:
            await self.handler_dispatcher(consumer_group=self.group, record=record)
        except Exception:
            logger.exception("Ошибка при обработке события")

        if self.group and tp in self.consumer.assignment():
            self.consumer.resume(tp)
            try:
                await self.consumer.commit(offsets={tp: record.offset + 1})
            except Exception:
                logger.exception("Offset не закоммичен – партицию уже забрали")

        logger.info(f"Обработано событие: {record}")

    async def _process_stream(self):
        """
        Обработать стрим
        """
        async for record in self.consumer:
            await self._process_record(record=record)

    async def run(self):
        """
        Запустить обработку стрима
        """
        try:
            await self.consumer.start()
            await self._process_stream()
        finally:
            await self.stop()

    async def stop(self):
        """
        Остановить обработку стрима
        """
        await self.consumer.stop()

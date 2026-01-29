from aiokafka_agent.infra.asyncio import Future

from aiokafka import AIOKafkaProducer
from aiokafka.structs import RecordMetadata

from aiokafka_agent.infra.datatype.json import safe_dumps
from aiokafka_agent.infra.logger.decorator import CoroutineLogger


@CoroutineLogger()
async def send_topic_message(faust_producer: AIOKafkaProducer, topic: str, data: dict) -> RecordMetadata:
    """
    Инверсия метода на эмит события в кафку
    :param data:
    :param topic:
    :param faust_producer:
    :return:
    """
    message: bytes = (safe_dumps(data)).encode("UTF-8")

    event: Future = await faust_producer.send(topic=topic, value=message)

    return await event

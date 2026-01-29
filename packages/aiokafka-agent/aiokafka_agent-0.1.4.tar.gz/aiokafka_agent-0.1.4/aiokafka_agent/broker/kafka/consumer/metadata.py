from aiokafka import AIOKafkaClient
from aiokafka.cluster import ClusterMetadata

from aiokafka_agent.broker.kafka.client import get_kafka_client
from aiokafka_agent.broker.kafka.config import KafkaConfig
from aiokafka_agent.broker.kafka.consumer.schemas import AppCusterMetadata
from aiokafka_agent.infra.logger.main import logger


async def get_cluster_metadata(kafka_conf: KafkaConfig) -> AppCusterMetadata:
    """
    Получить метаданные кластера
    """
    client: AIOKafkaClient = await get_kafka_client(kafka_conf=kafka_conf)

    await client.bootstrap()

    logger.info("Начитываю метаданные кластера кафки")
    cluster_metadata: ClusterMetadata = await client.fetch_all_metadata()

    await client.close()

    return AppCusterMetadata(topics=cluster_metadata.topics())

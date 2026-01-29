"""
Модуль с клиентом кафки
"""

from os import getpid
from typing import Iterable

from aiokafka import AIOKafkaClient, AIOKafkaConsumer, AIOKafkaProducer

from aiokafka_agent.broker.kafka.config import KafkaConfig
from aiokafka_agent.broker.kafka.serializer import json_deserializer, json_serializer
from aiokafka_agent.infra.logger.presenter import logger


async def get_kafka_producer(kafka_conf: KafkaConfig) -> AIOKafkaProducer:
    """
    Инверсия Кафка клиента
    :return:
    """
    logger.info(f"Прогреваю продьюсер кафки на воркере с pid {getpid()}")

    return AIOKafkaProducer(
        bootstrap_servers=kafka_conf.get_connection_uri,
        client_id=kafka_conf.CLIENT_ID,
        value_serializer=json_serializer,
        security_protocol=kafka_conf.SECURITY_PROTOCOL,
        sasl_mechanism=kafka_conf.SASL_MECHANISM,
        sasl_kerberos_service_name=kafka_conf.SASL_KERBEROS_SERVICE_NAME,
        sasl_kerberos_domain_name=kafka_conf.SASL_KERBEROS_DOMAIN_NAME,
        ssl_context=kafka_conf.get_ssl_context,
    )


async def get_kafka_consumer(
    kafka_conf: KafkaConfig, topics: Iterable[str], group_id: str | None = None,
) -> AIOKafkaConsumer:
    """
    Инверсия Кафка клиента
    :return:
    """
    logger.info(f"Прогреваю консьюмер кафки на воркере с pid {getpid()}")

    return AIOKafkaConsumer(
        *topics,
        auto_offset_reset="earliest" if group_id else "latest",
        session_timeout_ms=kafka_conf.SESSION_TIMEOUT_MS,
        heartbeat_interval_ms=kafka_conf.HEARTBEAT_INTERVAL_MS,
        max_poll_interval_ms=kafka_conf.MAX_POLL_INTERVAL_MS,
        max_poll_records=kafka_conf.MAX_POLL_RECORDS,
        enable_auto_commit=kafka_conf.ENABLE_AUTO_COMMIT,
        request_timeout_ms=kafka_conf.REQUEST_TIMEOUT_MS,
        bootstrap_servers=kafka_conf.get_connection_uri,
        client_id=kafka_conf.CLIENT_ID,
        group_id=group_id,
        value_deserializer=json_deserializer,
        security_protocol=kafka_conf.SECURITY_PROTOCOL,
        sasl_mechanism=kafka_conf.SASL_MECHANISM,
        sasl_kerberos_service_name=kafka_conf.SASL_KERBEROS_SERVICE_NAME,
        sasl_kerberos_domain_name=kafka_conf.SASL_KERBEROS_DOMAIN_NAME,
        ssl_context=kafka_conf.get_ssl_context,
    )


async def get_kafka_client(kafka_conf: KafkaConfig) -> AIOKafkaClient:
    """
    Получить клиента кафки
    """
    logger.info(f"Прогреваю клиента кафки на воркере с pid {getpid()}")

    return AIOKafkaClient(
        client_id=kafka_conf.CLIENT_ID,
        bootstrap_servers=kafka_conf.get_connection_uri,
        security_protocol=kafka_conf.SECURITY_PROTOCOL,
        sasl_mechanism=kafka_conf.SASL_MECHANISM,
        sasl_kerberos_service_name=kafka_conf.SASL_KERBEROS_SERVICE_NAME,
        sasl_kerberos_domain_name=kafka_conf.SASL_KERBEROS_DOMAIN_NAME,
        ssl_context=kafka_conf.get_ssl_context,
    )

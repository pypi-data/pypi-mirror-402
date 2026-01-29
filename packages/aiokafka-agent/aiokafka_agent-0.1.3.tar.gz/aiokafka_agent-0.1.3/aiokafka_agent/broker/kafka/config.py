from datetime import timedelta
from functools import cached_property
from os import environ
from ssl import CERT_NONE, PROTOCOL_TLS_CLIENT, SSLContext
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

from aiokafka_agent.infra.datatype.timedelta import td_to_miliseconds


class KafkaConfig(BaseSettings):
    """
    Конфигурация кафки
    """

    model_config = SettingsConfigDict(env_prefix="APP_KAFKA_", extra="allow")

    HOST: str = "localhost"
    PORT: str | None = "9092"

    # или "SASL_PLAINTEXT" для интеграции с КЛАД
    SECURITY_PROTOCOL: Literal["PLAINTEXT", "SASL_PLAINTEXT", "SASL_SSL"] = "PLAINTEXT"
    # для интеграции с КЛАД если включен SASL_PLAINTEXT или SASL_SSL
    SASL_MECHANISM: Literal["GSSAPI", "PLAIN"] = "PLAIN"
    # для интеграции с КЛАД если включен SASL_PLAINTEXT или SASL_SSL
    SASL_KERBEROS_SERVICE_NAME: str | None = None
    # для интеграции с КЛАД если включен SASL_PLAINTEXT или SASL_SSL
    SASL_KERBEROS_DOMAIN_NAME: str | None = None
    # для интеграции с КЛАД если включен SASL_PLAINTEXT или SASL_SSL
    SASL_KEYTAB_PATH: str | None = None
    # для интеграции с КЛАД если включен SASL_SSL
    SASL_SSL_CA_BUNDLE_PATH: str | None = None

    # Идентификаторы клиентов
    CLIENT_ID: str = "test_client"

    SESSION_TIMEOUT_MS: int = td_to_miliseconds(timedelta(seconds=10))
    HEARTBEAT_INTERVAL_MS: int = td_to_miliseconds(timedelta(seconds=3))
    MAX_POLL_INTERVAL_MS: int = td_to_miliseconds(timedelta(minutes=5))
    MAX_POLL_RECORDS: int = 1
    ENABLE_AUTO_COMMIT: bool = False
    REQUEST_TIMEOUT_MS: int = td_to_miliseconds(timedelta(seconds=40))

    TOPIC_NAME_PREFIX: str | None = None

    def model_post_init(self, ctx):
        """
        Пост инициализация
        """
        if self.SASL_KEYTAB_PATH:
            environ["KRB5_CLIENT_KTNAME"] = self.SASL_KEYTAB_PATH  # для пакета gssapi

    @cached_property
    def get_ssl_context(self) -> SSLContext:
        """
        Получить ssl context
        """
        ssl_ctx = SSLContext(protocol=PROTOCOL_TLS_CLIENT)
        if self.SASL_SSL_CA_BUNDLE_PATH:
            ssl_ctx.load_verify_locations(cafile=self.SASL_SSL_CA_BUNDLE_PATH)
        else:
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = CERT_NONE
        return ssl_ctx

    @cached_property
    def get_connection_uri(self) -> str:
        """
        Получить строку подключения
        """
        return f"{self.HOST}:{self.PORT}" if self.PORT else f"{self.HOST}"


kafka_conf = KafkaConfig()

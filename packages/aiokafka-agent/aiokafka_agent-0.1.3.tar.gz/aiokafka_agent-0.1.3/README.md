# aiokafka-agent

Продвинутый асинхронный клиент для Apache Kafka, построенный на asyncio и aiokafka. 
Библиотека упрощает обработку сообщений и предоставляет готовые инструменты для создания 
отказоустойчивых consumers и producers в асинхронных приложениях

## Features

Асинхронность: Полностью построен на asyncio и aiokafka для современных Python-приложений.

Готовые агенты: Предоставляет базовых агентов с встроенной логикой жизненного цикла (запуск, остановка, повторное подключение).

Автоматическая сериализация: Интеграция с pydantic для автоматической валидации и сериализации/десериализации сообщений.

Управление зависимостями: Поддержка Dependency Injection для чистого и тестируемого кода.

Гибкая конфигурация: Настройка через pydantic-settings, поддержка переменных окружения.

## Installation

Установка из PyPi

```commandline
pip install aiokafka-agent
```

## Configuration

Для конфигурации ConsumerApp необходимо создать config-класс

```python
class KafkaConfig(BaseSettings):
    """
    Конфигурация кафки
    """

    model_config = SettingsConfigDict(env_prefix="APP_KAFKA_")

    HOST: str = "kafka-0.kafka"
    PORT: str | None = "9092"

    # Идентификаторы клиентов
    CLIENT_ID: str

    SESSION_TIMEOUT_MS: int = td_to_miliseconds(timedelta(seconds=10))
    HEARTBEAT_INTERVAL_MS: int = td_to_miliseconds(timedelta(seconds=3))
    MAX_POLL_INTERVAL_MS: int = td_to_miliseconds(timedelta(minutes=5))
    MAX_POLL_RECORDS: int = 1
    ENABLE_AUTO_COMMIT: bool = False
    REQUEST_TIMEOUT_MS: int = td_to_miliseconds(timedelta(seconds=40))
    

    SECURITY_PROTOCOL: Literal["PLAINTEXT", "SASL_PLAINTEXT", "SASL_SSL"] = "PLAINTEXT"
    SASL_MECHANISM: Literal["GSSAPI", "PLAIN"] = "PLAIN"
    SASL_KERBEROS_SERVICE_NAME: str | None = None
    SASL_KERBEROS_DOMAIN_NAME: str | None = None
    SASL_KEYTAB_PATH: str | None = None
    SASL_SSL_CA_BUNDLE_PATH: str | None = None

    TOPIC_NAME_PREFIX: str | None = None

    # Группы консьюмеров
    GRAPH_GROUP_ID: str = "graph_group"

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

kafka_config = KafkaConfig()
```

## Get started

Добавьте свой конфиг Kafka в ConsumerApp

```python
from asyncio import run
from aiokafka_agent import ConsumerApp
from your_app import your_agent_group
from .config import kafka_config


app = ConsumerApp()
app.kafka_conf = kafka_config

app.agents.append_group(your_agent_group)


if __name__ == "__main__":
    run(app.run())
```


## License
Распространяется под лицензией MIT.

Поддержка
Issues: GitLab Issues

Вопросы и обсуждения: Открывайте issue для багов и запросов функций

Проект в активной разработке. API может меняться 
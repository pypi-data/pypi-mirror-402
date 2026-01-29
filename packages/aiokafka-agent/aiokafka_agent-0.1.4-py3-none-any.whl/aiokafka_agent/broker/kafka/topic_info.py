from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TopicInfo(BaseModel):
    """Модель для хранения информации о топике."""

    title: str  # Человеческое название по-русски
    timeout_seconds: int  # Таймаут в секундах


class TopicInfoConfig(BaseSettings):
    """Основной класс настроек для всех топиков."""

    model_config = SettingsConfigDict(
        env_prefix="APP_TOPIC_INFO_",
        env_nested_delimiter="__",
    )

    MESSAGE_INFERENCE: TopicInfo = Field(
        default=TopicInfo(
            title="Обработчик сообщений",
            timeout_seconds=3000,
        ),
    )
    ATTACHMENT_PARSING: TopicInfo = Field(
        default=TopicInfo(
            title="Парсер вложений",
            timeout_seconds=3000,
        ),
    )
    OPERATIONS: TopicInfo = Field(
        default=TopicInfo(
            title="Обновление статуса операции",
            timeout_seconds=3000,
        ),
    )
    INFERENCE_CHUNKS: TopicInfo = Field(
        default=TopicInfo(
            title="Обработчик чанков сообщений",
            timeout_seconds=3000,
        ),
    )


topic_info_config = TopicInfoConfig()

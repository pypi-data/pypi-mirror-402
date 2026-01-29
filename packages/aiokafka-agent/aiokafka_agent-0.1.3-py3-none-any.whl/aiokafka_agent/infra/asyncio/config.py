from pydantic_settings import BaseSettings, SettingsConfigDict


class ProcessPoolConfig(BaseSettings):
    """
    Настройки пула процессов
    """

    model_config = SettingsConfigDict(env_prefix="APP_PROCESS_POOL_")

    MAX_RETRIES: int = 3


process_pool_config = ProcessPoolConfig()

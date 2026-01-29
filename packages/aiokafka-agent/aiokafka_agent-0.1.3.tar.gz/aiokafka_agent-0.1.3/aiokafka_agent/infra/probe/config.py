"""
Конфигурация liveness и rediness probe
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class ProbeConfig(BaseSettings):
    """
    Consumer probe config
    """

    ENABLED: bool
    NAME: str
    INTERVAL: int
    FILE_PATH: str | Path


class ReadinessProbe(ProbeConfig):
    """
    Readiness probe config
    """

    model_config = SettingsConfigDict(env_prefix="APP_READINESS_PROBE")

    ENABLED: bool = True
    NAME: str = "readiness"
    INTERVAL: int = 30
    FILE_PATH: str | Path = Path("/tmp", "/readiness")


class LivenessProbe(ProbeConfig):
    """
    Liveness probe config
    """

    model_config = SettingsConfigDict(env_prefix="APP_LIVENESS_PROBE")

    ENABLED: bool = True
    NAME: str = "liveness"
    INTERVAL: int = 30
    FILE_PATH: str | Path = Path("/tmp", "liveness")


readiness_config, liveness_config = ReadinessProbe(), LivenessProbe()

probe_configs = (readiness_config, liveness_config)

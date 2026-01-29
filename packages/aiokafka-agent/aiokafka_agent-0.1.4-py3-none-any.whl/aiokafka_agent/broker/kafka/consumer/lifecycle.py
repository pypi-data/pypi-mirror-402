from typing import Coroutine

from aiokafka_agent.infra.logger.main import logger
from aiokafka_agent.infra.probe.liveness import Probe


class LifecycleHandler:
    """
    Обработчик жизненного цикла
    """

    def __init__(self) -> None:
        self.probe = Probe()
        self.on_before_start_app_handler: Coroutine | None = None
        self.on_after_stop_app_handler: Coroutine | None = None

    async def on_before_start(self):
        """
        Вызывается перед запуском сервиса
        """
        if self.on_before_start_app_handler is not None:
            await self.on_before_start_app_handler

        logger.info("Консьюмер запущен. Готов к обработке стрима.")

        await self.probe.start()

    async def on_after_stop(self):
        """
        Вызывается после остановки сервиса
        """
        if self.on_after_stop_app_handler is not None:
            await self.on_after_stop_app_handler

        logger.info("Консьюмер остановлен. Обработка стрима прекращена.")

        await self.probe.stop()

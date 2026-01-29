from asyncio import CancelledError, Task, create_task, sleep
from dataclasses import dataclass, field
from pathlib import Path

from aiokafka_agent.infra.logger.presenter import logger
from aiokafka_agent.infra.probe.config import ProbeConfig, probe_configs


@dataclass
class Probe:
    """
    Реализация пробы жизнеспособности
    """

    probe_tasks: set[Task] = field(default_factory=set)

    async def start(self) -> None:
        """
        Запустить
        """
        for probe_conf in probe_configs:
            if not probe_conf.ENABLED:
                continue

            probe_task: Task = create_task(coro=self._probe_task(probe_conf), name=probe_conf.NAME)
            self.probe_tasks.add(probe_task)

    async def stop(self) -> None:
        """
        Остановить
        """
        for task in self.probe_tasks:
            task.cancel()
            try:
                await task
            except CancelledError:
                logger.info(f"{task.get_name()} probe остановлен.")

        self.probe_tasks = set()

    async def _probe_task(self, config: ProbeConfig) -> None:
        """
        Создать файл с текущим временем
        """
        logger.info(f"Инициализирую {config.NAME} probe.")

        while True:
            file = Path(config.FILE_PATH)

            # file.write_text(f"File created at {datetime.now()}")
            logger.info(f"Пишу {config.NAME} probe по пути {config.FILE_PATH}.")

            await sleep(config.INTERVAL)

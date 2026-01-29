"""
Рассчет времени выполнения
"""

from time import perf_counter
from typing import Callable, Coroutine

from aiokafka_agent.infra.logger.main import logger


class CoroutineLogger:
    """
    Классовый декоратор на детальное логгирование Callable объектов
    """

    def __init__(self, log_results: bool = True, log_params: bool = True):
        self.log_results = log_results
        self.log_params = log_params

    def __call__(self, func: Callable | Coroutine):
        self.func = func

        return self.wrapper

    async def wrapper(self, *args, **kwargs):
        """
        Декоратор
        """
        func_name = self.func.__name__
        args_logs = f"Args: {args} Kwargs: {kwargs}" if self.log_params else "скрыты"

        req_start = perf_counter()
        logger.info(f"Вызов объекта {func_name} запущен. Аргументы - {args_logs}.")

        func_res = await self.func(*args, **kwargs)

        req_end = perf_counter()
        logger.info(
            f"Вызов объекта {func_name} окончен. Время выполнения = {(req_end - req_start) * 1000:.2f} мс. "
            f"Аргументы - {args_logs}. "
            f"Результат {func_res if self.log_results else 'скрыт'}. ",
        )

        return func_res

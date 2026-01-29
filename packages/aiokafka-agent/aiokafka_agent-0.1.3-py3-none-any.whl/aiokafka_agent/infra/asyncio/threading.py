from __future__ import annotations

from asyncio import wrap_future
from concurrent.futures import Future, ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from multiprocessing import get_context
from os import kill
from signal import Signals
from typing import Any, Callable, Coroutine

from aiokafka_agent.infra.asyncio.config import process_pool_config
from aiokafka_agent.infra.asyncio.event_loop import safe_get_or_create_event_loop
from aiokafka_agent.infra.datatype.singleton import SingletonMeta
from aiokafka_agent.infra.logger.config import logger_config


class ProcessPoolManager(metaclass=SingletonMeta):
    """
    Синглтон-класс для управления пулом процессов. В нашем случае одним процессом в пуле.
    """

    _executor: ProcessPoolExecutor | None = None
    _executor_alive: bool = False

    def init_process_pool(self) -> None:
        """
        Инициализирует пул процессов, если он еще не создан или был завершен.
        """
        if self._executor is None or not self._executor_alive:
            self._executor = ProcessPoolExecutor(max_workers=1, mp_context=get_context("spawn"), max_tasks_per_child=1)
            self._executor_alive = True

    def shutdown_process_pool(self, force: bool = False) -> None:
        """
        Завершает пул процессов, если он существует и активен.
        """
        if not self._executor:
            return None

        for process in list(self._executor._processes.values()):
            try:
                if process.is_alive():
                    kill(process.pid, Signals.SIGKILL)
            except ProcessLookupError:
                pass
            except Exception as exc:
                logger_config.logger.warning(
                    "Не удалось послать SIGKILL дочернему процессу %s: %s",
                    process.pid,
                    exc,
                )

        self._executor.shutdown(wait=not force, cancel_futures=force)
        self._executor = None
        self._executor_alive = False

    def restart_process_pool(self, force: bool = True):
        """
        Убивает и поднимает пул субпроцессов
        """
        self.shutdown_process_pool(force=force)
        self.init_process_pool()

    def submit_task(
        self, coroutine_func: Callable[..., Coroutine], args: tuple[Any, ...], kwargs: dict[str, Any],
    ) -> Future:
        """
        Отправляет задачу на выполнение в пул процессов.

        :param coroutine_func: Корутинная функция для выполнения.
        :param args: Позиционные аргументы для корутины.
        :param kwargs: Именованные аргументы для корутины.
        :return: Объект Future, представляющий выполнение задачи.
        """
        if self._executor is None:
            self.init_process_pool()
        return self._executor.submit(task, coroutine_func, args, kwargs)


def task(coroutine_func: Callable[..., Coroutine], args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
    """
    Обертка над задачей, выполняемой в отдельном процессе.

    :param coroutine_func: Корутинная функция для выполнения.
    :param args: Позиционные аргументы для корутины.
    :param kwargs: Именованные аргументы для корутины.
    :return: Результат выполнения корутины.
    """
    executor_process_loop = safe_get_or_create_event_loop()
    return executor_process_loop.run_until_complete(coroutine_func(*args, **kwargs))


async def run_in_subprocess(coroutine_func: Callable[..., Coroutine], *args, exception_handler: Callable[..., Coroutine] = None, **kwargs) -> Any:
    """
    Метод, позволяющий выполнить корутину в отдельном процессе.
    Принимает корутину и выполняет ее в отдельном процессе.

    Возвращает результат выполнения корутины.
    Корутина будет считаться выполненной только после завершения процесса и переданной задачи.

    Метод полезен в случаях, когда в основном асинхронном цикле
    категорически запрещено блокировать операции, связанные с использованием CPU.

    :param coroutine_func: Корутинная функция для выполнения.
    :param args: Позиционные аргументы для корутины.
    param exception_handler: Необязательная асинхронная функция-обработчик исключений.
                              Вызывается, если после нескольких попыток запуска процесса
                              возникает исключение BrokenProcessPool.
                              Принимает саму ошибку, а также все переданные в корутину аргументы.
    :param kwargs: Именованные аргументы для корутины.
    :return: Результат выполнения корутины.
    :raise BrokenProcessPool: Если пул процессов не удалось восстановить после
                             максимального количества попыток.
    """
    manager = ProcessPoolManager()
    max_retries = process_pool_config.MAX_RETRIES  # В случае задержек с выделением квоты кубера по лимитам
    exception = None

    for attempt in range(max_retries):
        manager.init_process_pool()

        try:
            future: Future = manager.submit_task(coroutine_func, args, kwargs)
            return await wrap_future(future)

        except (BrokenProcessPool, ProcessLookupError) as exc:
            exception = exc
            manager.restart_process_pool()
    try:
        logger_config.logger.exception("Ошибка при обработке события в run_in_subprocess")
        raise BrokenProcessPool(f"Не удалось запустить расчет после {max_retries} попыток запуска процесса.") from exception
    except BrokenProcessPool as exc:
        if exception_handler:
            await exception_handler(exc, *args, **kwargs)
        else:
            raise exc

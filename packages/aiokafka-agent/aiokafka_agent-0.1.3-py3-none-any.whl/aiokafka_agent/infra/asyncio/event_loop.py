from asyncio import AbstractEventLoop, get_event_loop, new_event_loop, set_event_loop

from aiokafka_agent.infra.logger.presenter import logger


def safe_get_or_create_event_loop() -> AbstractEventLoop:
    r"""
    Безопасное получение ивент лупа текущего потока.
    При работе за пределами основного потока ивент лупа по умолчанию нет.
    Этот метод решает проблему безопасного создания\получения лупа в любом из потоков.
    :return:
    """
    try:
        return get_event_loop()
    except RuntimeError as ex:
        logger.info(f"Поднимаю новый ивент луп. В текущем потоке его нет. Обработано исключение: {ex}.")
        loop = new_event_loop()
        set_event_loop(loop)
        return loop

from asyncio import Lock
from collections import defaultdict

from aiokafka_agent.broker.kafka.consumer.types import ConsumerRecord, Group
from aiokafka_agent.infra.datatype.singleton import SingletonMeta


class ConsumerRecordDescriptor(metaclass=SingletonMeta):
    """
    Задача текущего субпроцесса по группам
    """

    def __init__(self) -> None:
        self._current_tasks: dict = defaultdict(lambda: None)
        self._group_locks: dict = defaultdict(Lock)

    @property
    def current_tasks(self) -> dict[Group, ConsumerRecord]:
        """
        Получить текущие активные задачи
        """
        return {group: record for group, record in (self._current_tasks.copy()).items() if record is not None}

    def get_group_task(self, group: Group) -> ConsumerRecord | None:
        """
        Получить текущую задачу для группы
        """
        return self._current_tasks.get(group)

    async def set_group_task(self, group: Group, record: ConsumerRecord | None) -> None:
        """
        Задать текущую задачу для группы. Если группа заблокирована, метод будет ждать разблокировки.
        """
        async with self._group_locks[group]:
            self._current_tasks[group] = record

    async def delete_group_task(self, group: Group) -> None:
        """
        Удалить задачу для группы. Если группа заблокирована, метод будет ждать разблокировки.
        """
        async with self._group_locks[group]:
            self._current_tasks[group] = None

    async def lock_group(self, group: Group) -> None:
        """
        Заблокировать группу для изменения или удаления задачи
        """
        await self._group_locks[group].acquire()

    def unlock_group(self, group: Group) -> None:
        """
        Разблокировать группу для изменения или удаления задачи
        """
        if self._group_locks[group].locked():
            self._group_locks[group].release()


consumer_record_descriptor = ConsumerRecordDescriptor()

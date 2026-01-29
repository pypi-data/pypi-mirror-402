from collections import defaultdict
from typing import Protocol, TypeAlias

from aiokafka.structs import ConsumerRecord


Group: TypeAlias = str | None
Topic: TypeAlias = str


class Handler(Protocol):
    async def __call__(self, record: ConsumerRecord) -> None: ...


TopicHandlers = defaultdict[Topic, set[Handler]]
GroupTopics = defaultdict[Group, TopicHandlers]


class HandlerDispatcher(Protocol):
    async def __call__(self, consumer_group: Group, record: ConsumerRecord) -> None: ...


GroupRecords = defaultdict[Topic, set[ConsumerRecord]]

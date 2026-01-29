from collections import defaultdict
from pprint import pformat
from typing import Callable

from aiokafka import TopicPartition
from aiokafka.abc import ConsumerRebalanceListener as KafkaRebalanceListener

from aiokafka_agent.infra.logger.presenter import logger


class ConsumerRebalanceListener(KafkaRebalanceListener):
    """
    A callback interface that the user can implement to trigger custom actions
    when the set of partitions assigned to the consumer changes.
    """

    def __init__(self) -> None:
        super().__init__()
        self.on_partitions_revoked_app_handler: Callable | None = None
        self.on_partitions_assigned_app_handler: Callable | None = None

    def on_partitions_revoked(self, revoked: list[TopicPartition]):
        grouped_partitions = self.group_partitions(revoked)
        logger.info(
            f"Реплике консьюмера ОТОЗВАНЫ партиции следующих топиков: \n {pformat(grouped_partitions, indent=2)}",
        )

        if self.on_partitions_revoked_app_handler is not None:
            self.on_partitions_revoked_app_handler(revoked=grouped_partitions)

    def on_partitions_assigned(self, assigned: list[TopicPartition]):
        grouped_partitions = self.group_partitions(assigned)
        logger.info(
            f"Реплике консьюмера ПРИСВОЕНЫ партиции следующих топиков: \n {pformat(grouped_partitions, indent=2)}",
        )

        if self.on_partitions_assigned_app_handler is not None:
            self.on_partitions_assigned_app_handler(assigned=grouped_partitions)

    def group_partitions(self, partitions: list[TopicPartition]) -> dict[str, list[int]]:
        """
        Формирует словарь с группировкой топик: партиции для красивого вывода
        """
        topic_partitions = defaultdict(list)
        for tp in partitions:
            topic_partitions[tp.topic].append(tp.partition)

        for partitions_list in topic_partitions.values():
            partitions_list.sort()

        return dict(topic_partitions)

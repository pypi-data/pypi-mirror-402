from typing import Sequence

from aiokafka_agent.infra.datatype.types import DefaultT, IncomingT


def safe_idx_get(list_: Sequence[IncomingT], idx: int, default: DefaultT) -> IncomingT | DefaultT:
    """
    Метод для безопасного получения значения по индексу
    """
    try:
        return list_[idx]
    except (IndexError, TypeError):
        return default

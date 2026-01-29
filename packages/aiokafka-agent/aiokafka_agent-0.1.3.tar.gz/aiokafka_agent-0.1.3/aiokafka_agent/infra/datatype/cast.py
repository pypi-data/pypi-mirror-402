from typing import Any, Callable, Sequence

from aiokafka_agent.infra.datatype.types import DefaultT, IncomingT


def safe_cast(value: Any, to_type: type[IncomingT] | Callable, default: DefaultT = None) -> IncomingT | DefaultT:
    """
    Вспомогательный метод для безопасного прокаста типов
    """
    try:
        return to_type(value)
    except Exception:
        pass

    return default


def list_cast(value: list, to_type: type[IncomingT] | None, force: bool = False) -> list[IncomingT]:
    """
    Приведение элементов списка к определенному типу
    :param value: список
    :param to_type: тип
    :type to_type: type
    :param force: пропускать значения, которые не получается привести
    """
    if not to_type:
        return value

    result = []
    for item in value:
        item = safe_cast(value=item, to_type=to_type)
        if item:
            result.append(item)

    return result


def as_array(value: Sequence | None, force: bool = True) -> list:
    """
    Привести значение к списку.
    :param value: исходное значение
    :param force: пропускать значенние, если невозможно привести к типу
    :return:
    """
    if isinstance(value, (list, tuple, set)):
        return list(value)
    if value is None and force:
        return []
    return [value]


def to_array(value: Sequence, to_type: type[IncomingT] | None = None, force: bool = False) -> list[IncomingT]:
    """
    Привести значение к массиву (определенного типа)
    :param value: исходное значение
    :param to_type: тип
    :type to_type: type
    :param force: пропускать значенние, если невозможно привести к типу
    """
    result = as_array(value)
    result = list_cast(result, to_type, force)
    return result

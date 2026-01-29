from typing import Any

from aiokafka_agent.infra.datatype.json import safe_dumps, safe_loads


def json_serializer(value: dict[Any, Any]) -> bytes:
    """
    Сериалзиатор из словаря в байте
    """
    val = safe_dumps(value)

    return val.encode("UTF-8")


def json_deserializer(value: bytes) -> dict[Any, Any]:
    """
    Десериализатор из байтов в словарь
    """
    value_str = value.decode(encoding="utf-8")

    return safe_loads(value_str)

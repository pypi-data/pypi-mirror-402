from functools import partial
from json import dumps, loads

from aiokafka_agent.infra.datatype.cast import safe_cast


def safe_dumps(data: dict, **kwargs) -> str:
    """
    Безопасный вызов json.dumps
    :param default:
    :param data:
    :return:
    """
    return safe_cast(
        value=data,
        to_type=partial(dumps, ensure_ascii=False, default=str, **kwargs),
        default="",
    )


def safe_loads(data: str, default=None, **kwargs) -> dict:
    """
    Безопасный вызов json.loads
    :param indent:
    :param default:
    :param data:
    :return:
    """
    return safe_cast(
        value=data,
        to_type=partial(loads, **kwargs),
        default={} if default is None else default,
    )

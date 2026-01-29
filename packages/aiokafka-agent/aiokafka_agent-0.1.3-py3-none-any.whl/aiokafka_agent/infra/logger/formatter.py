from typing import Any


def short_formatter(key: Any, value: Any) -> str:
    def __type(__value: Any) -> str:
        return type(__value).__name__

    return f"{key}: {__type(value)}"


def long_formatter(key: str, value: Any) -> str:
    def __type(__value: Any) -> str:
        return str(type(__value))[8:-2]  # <class '...'> -> ...

    if isinstance(value, list):
        value_type = "List"
        if len(value) > 0:
            value_type += f"[{__type(value[0])}]"
    elif isinstance(value, dict):
        value_type = "Dict"
        if len(value) > 0:
            dict_key, dict_value = list(value.items())[0]
            value_type += f"[{__type(dict_key)}, {__type(dict_value)}]"
    else:
        value_type = __type(value)

    return f"{key}: {value_type}"


def additional_formatter(param_new: Any, param_old: Any) -> str:
    message_additional: str = " "

    if param_old is not None:
        message_additional += f"старое значение {param_old}"
    if param_new is not None:
        message_additional += f"новое значение {param_new}"

    return message_additional

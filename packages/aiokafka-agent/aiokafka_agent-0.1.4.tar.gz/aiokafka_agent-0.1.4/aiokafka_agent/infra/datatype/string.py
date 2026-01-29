"""
Методы для работы со строками
"""
from re import split, sub
from typing import Callable

from aiokafka_agent.infra.datatype.list import safe_idx_get


def docstring_to_string(docstring: str) -> str:
    """
    Преобразует докстринг к строке
    """
    if not docstring:
        return ""

    return docstring.replace("\n", "").replace("    ", "")


def get_right_by_substr(str_: str, substr_: str) -> str:
    """
    Получает правую часть строки после подстроки
    """
    return safe_idx_get(str_.split(sep=substr_, maxsplit=1), idx=-1, default="")


def to_snake_case(name: str) -> str:
    """
    Привести строку к снейккейзу
    """
    name = sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def normalize_cls_name(value: Callable) -> str:
    """
    Нормализует название исключения
    """
    cls_name = to_snake_case(value.__name__)

    return str.upper(cls_name)


def fix_encoding(string: str, target_encoding: str = "cp1251") -> str:
    """
    Исправить кодировку строки (откидывает непечатные символы)
    """
    encoded_string = string.encode(target_encoding, "ignore")
    decoded_string = encoded_string.decode(target_encoding)

    return decoded_string


def split_clearfy(string: str, regexp: str = r"[\\:\'()&!?|<*]+") -> list[str]:
    """
    Разделить строку откинув символы переноса и прочий мусор
    """
    return split(r"\s+", sub(regexp, " ", string))


def transit(string: str, mappings: dict[str, str]) -> str:
    """
    Выполняет транслитерацию на основе мапингов
    """
    for symbol, translation in mappings.items():
        string = string.replace(symbol, translation)

    return string

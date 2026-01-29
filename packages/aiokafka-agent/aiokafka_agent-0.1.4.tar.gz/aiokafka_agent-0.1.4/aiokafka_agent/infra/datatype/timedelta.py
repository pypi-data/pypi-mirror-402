from datetime import timedelta


def td_to_miliseconds(td: timedelta):
    """
    Перевод timedelta в миллисекунды
    :param td: timedelta
    :return: int
    """
    return int(td.total_seconds() * 1000)

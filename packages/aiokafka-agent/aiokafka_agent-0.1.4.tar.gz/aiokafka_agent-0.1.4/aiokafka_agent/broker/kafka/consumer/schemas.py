from dataclasses import dataclass, field


@dataclass
class AppCusterMetadata:
    """
    Метаданные кластера кафки необходимые для работы приложения

    Расширять под потребности
    """

    topics: set = field(default_factory=set)

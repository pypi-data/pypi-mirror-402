from contextvars import ContextVar
from typing import Any


ContextData = ContextVar[dict[str, Any]]

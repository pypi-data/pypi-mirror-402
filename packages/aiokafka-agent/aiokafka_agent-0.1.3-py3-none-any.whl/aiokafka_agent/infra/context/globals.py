from contextvars import ContextVar
from typing import Any

from aiokafka_agent.infra.context.types import ContextData
from aiokafka_agent.infra.datatype.singleton import SingletonMeta


class Globals(metaclass=SingletonMeta):
    """
    A thread-safe, context-aware global variables manager with singleton pattern.

    Provides methods to set, get, and manage variables in a request-specific context.
    All operations are atomic within the current context.
    """

    CONTEXTVAR_KEY = "context_data"

    _context_data: ContextData | None = None

    @property
    def context(self) -> dict[str, Any]:
        """Get the current context dictionary."""
        if self._context_data is None:
            self._context_data = ContextVar(self.CONTEXTVAR_KEY, default={})

        return self._context_data.get()

    @context.setter
    def context(self, new_dict: dict[str, Any]) -> None:
        """
        Set a new dictionary as the current context.
        """
        if self._context_data is None:
            self._context_data = ContextVar(self.CONTEXTVAR_KEY, default=new_dict)

        self._context_data.set(new_dict)

    @context.deleter
    def context(self):
        """Clear all context variables from the store."""
        self.context = {}

    def get(self, name: str, default: Any | None = None) -> Any:
        """
        Retrieve the value of a variable with an optional default value.

        Args:
            name: The name of the variable.
            default: The value to return if the variable is not found.

        Returns:
            The value of the variable or the default value.
        """
        return self.context.get(name, default)

    def set(self, name: str, value: Any) -> None:
        """
        Set the value of a variable.

        Args:
            name: The name of the variable.
            value: The value to set.
        """
        context_dict = self.context
        context_dict[name] = value
        self.context = context_dict

    def pop(self, name: str, default: Any | None = None) -> Any:
        """
        Retrieve and remove the value of a variable, with an optional default.

        Args:
            name: The name of the variable.
            default: The value to return if the variable is not found.

        Returns:
            The value of the variable or the default value.
        """
        context_dict = self.context
        value = context_dict.pop(name, default)
        self.context = context_dict
        return value


# Global instance of the Globals manager
g = Globals()

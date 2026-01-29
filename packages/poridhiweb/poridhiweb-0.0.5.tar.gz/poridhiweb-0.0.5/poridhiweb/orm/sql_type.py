from abc import ABC, abstractmethod
from typing import Any


class SQLType(ABC):
    def __init__(self, python_type: type, cast_fn=None):
        self.python_type = python_type
        self.cast_fn = cast_fn or self.python_type

    def to_python_type(self, column_value: Any) -> Any:
        return self.cast_fn(column_value)

    @property
    @abstractmethod
    def value(self) -> str:
        raise NotImplementedError

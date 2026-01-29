from abc import ABC, abstractmethod
from typing import TypeVar, List

from poridhiweb.orm.table import Table

T = TypeVar("T", bound=Table)


class Database(ABC):
    connection = None

    @property
    @abstractmethod
    def tables(self):
        raise NotImplementedError

    @abstractmethod
    def create(self, table_type: type[T]):
        raise NotImplementedError

    @abstractmethod
    def save(self, table_instance: T):
        raise NotImplementedError

    @abstractmethod
    def get_all(self, table_type: type[T]) -> List[T]:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, table_type: type[T], id: int) -> T:
        raise NotImplementedError

    @abstractmethod
    def update(self, table_to_update: T) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, table_type: type[T], id: int) -> None:
        raise NotImplementedError


from enum import Enum

from poridhiweb.orm.sqlite.database import SqliteDatabase


class Dialect(Enum):
    SQLITE = "sqlite"


class DatabaseFactory:
    def __init__(self, dialect: Dialect = Dialect.SQLITE):
        self.dialect = dialect

    def get_connection(self, *args, **kwargs):
        if self.dialect == Dialect.SQLITE:
            return SqliteDatabase(*args, **kwargs)

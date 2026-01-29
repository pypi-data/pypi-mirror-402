from poridhiweb.orm.sql_type import SQLType


class INTEGER(SQLType):
    def __init__(self):
        super().__init__(python_type=int)

    @property
    def value(self) -> str:
        return 'INTEGER'


class BOOLEAN(SQLType):
    def __init__(self):
        super().__init__(python_type=bool)

    @property
    def value(self) -> str:
        return 'INTEGER'


class FLOAT(SQLType):
    def __init__(self):
        super().__init__(python_type=float)

    @property
    def value(self) -> str:
        return 'REAL'


class STRING(SQLType):
    def __init__(self):
        super().__init__(python_type=str)

    @property
    def value(self) -> str:
        return 'TEXT'


class BYTES(SQLType):
    def __init__(self):
        super().__init__(python_type=bytes)

    @property
    def value(self) -> str:
        return 'BLOB'


SQL_TYPE_MAP = {
    int: INTEGER(),
    float: FLOAT(),
    str: STRING(),
    bytes: BYTES(),
    bool: BOOLEAN(),
}

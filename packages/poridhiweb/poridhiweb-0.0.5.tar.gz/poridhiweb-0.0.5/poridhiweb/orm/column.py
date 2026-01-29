from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from poridhiweb.orm.table import Table


class Column:
    def __init__(self, column_type):
        self.type = column_type


class PrimaryKey(Column):
    def __init__(self, column_type=int, auto_increment=True):
        self.auto_increment = auto_increment
        super().__init__(column_type)


class ForeignKey(Column):
    def __init__(self, table: type["Table"], column_type=int):
        self.table = table
        super().__init__(column_type)

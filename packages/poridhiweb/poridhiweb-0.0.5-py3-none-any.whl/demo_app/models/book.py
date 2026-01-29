from poridhiweb.orm.column import PrimaryKey, Column
from poridhiweb.orm.table import Table


class Author(Table):
    id = PrimaryKey()
    name = Column(str)
    age = Column(int)


class Book(Table):
    id = PrimaryKey()
    name = Column(str)
    author = Column(str)

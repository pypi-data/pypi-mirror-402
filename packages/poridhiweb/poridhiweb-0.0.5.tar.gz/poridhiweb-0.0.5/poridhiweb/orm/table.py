from poridhiweb.orm.column import Column


class TableMeta(type):
    def __new__(cls, name, bases, attrs):
        columns = {}  # Collect fields in declaration order
        for key, value in attrs.items():
            if isinstance(value, Column):
                columns[key] = value
        table_cls = super().__new__(cls, name, bases, attrs)
        table_cls._columns = columns
        return table_cls


class Table(metaclass=TableMeta):
    def __init__(self, **kwargs):
        self._data = {
            "id": None,
        }
        for key, value in kwargs.items():
            self._data[key] = value
        self.id = self._data["id"]

    def __getattribute__(self, key):
        # A python magic method that gets invoked when an instance field is accessed.
        # such as any defined author.name attribute or dynamic attribute like author.id

        # whenever any field is called we first try to return it from our data dictionary
        # or directly from the instance

        # can't use self._data as it will call __getattribute__ again and again leading to an infinite recursion call
        _data = super().__getattribute__("_data")
        if key in _data:
            return _data[key]

        return super().__getattribute__(key)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if key in self._data:
            self._data[key] = value

    @property
    def __dict__(self):
        return self._data



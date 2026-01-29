import sqlite3
from typing import TypeVar

from poridhiweb.orm.database import Database
from poridhiweb.orm.sql_type import SQLType
from poridhiweb.orm.column import Column, ForeignKey
from poridhiweb.orm.exceptions import RecordNotFound
from poridhiweb.orm.sqlite.query_builder import QueryBuilder


from poridhiweb.orm.sqlite.sqlite_types import SQL_TYPE_MAP
from poridhiweb.orm.table import Table

T = TypeVar("T", bound=Table)


class SqliteDatabase(Database):
    def __init__(self, path):
        self.path = path
        self.connection = sqlite3.Connection(self.path)

    @property
    def tables(self):
        result_set = self.connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return [rs[0] for rs in result_set]

    def create(self, table_type: type[T]):
        raw_sql = QueryBuilder.build_create_table_sql(table_type)
        self.connection.execute(raw_sql)

    def save(self, table_instance: T):
        sql, values = QueryBuilder.build_insert_sql(table_instance)
        cursor = self.connection.execute(sql, values)
        table_instance._data["id"] = cursor.lastrowid
        self.connection.commit()

    def get_all(self, table_type: type[T]) -> list[T]:
        sql, column_names = QueryBuilder.build_select_all_sql(table_type)
        rows = self.connection.execute(sql).fetchall()
        results = []
        for row in rows:
            # Map to Python type class
            instance = self._to_instance(
                table_type=table_type,
                column_names=column_names,
                row=row,
            )
            results.append(instance)
        return results

    def get_by_id(self, table_type: type[T], id: int) -> T:
        sql, column_names, params = QueryBuilder.build_select_by_id_sql(table_type, id)
        row = self.connection.execute(sql, params).fetchone()
        if not row:
            raise RecordNotFound(f"Table {table_type.__name__.lower()} with id {id} not found")

        return self._to_instance(
            table_type=table_type,
            column_names=column_names,
            row=row,
        )

    def update(self, table_to_update: T) -> None:
        update_sql, column_names, params = QueryBuilder.build_update_sql(table_to_update)
        self.connection.execute(update_sql, params)
        self.connection.commit()

    def delete(self, table_type: type[T], id: int) -> None:
        delete_sql, params = QueryBuilder.build_delete_sql(table_type, id)
        self.connection.execute(delete_sql, params)
        self.connection.commit()

    def _get_fk_by_id(
        self,
        parent_table_type: type[T],
        fk_field_name: str,
        fk_id: int
    ) -> T:
        fk: ForeignKey = parent_table_type._columns[fk_field_name]
        fk_instance = self.get_by_id(fk.table, id=fk_id)
        return fk_instance

    def _to_field_name(self, column_name: str) -> str:
        if column_name.endswith("_id"):
            return column_name[:-3]
        return column_name

    def _to_instance(self, table_type: type[T], column_names: list[str], row: tuple) -> T:
        kwargs = {}
        for column_name, col_value in zip(column_names, row):
            field_name = self._to_field_name(column_name)
            column: Column = table_type._columns[field_name]
            if isinstance(column, ForeignKey):
                fk_instance = self._get_fk_by_id(
                    parent_table_type=table_type,
                    fk_field_name=field_name,
                    fk_id=col_value
                )
                kwargs[field_name] = fk_instance
            else:
                sql_type: SQLType = SQL_TYPE_MAP[column.type]
                kwargs[field_name] = sql_type.to_python_type(col_value)
        instance = table_type(**kwargs)
        return instance

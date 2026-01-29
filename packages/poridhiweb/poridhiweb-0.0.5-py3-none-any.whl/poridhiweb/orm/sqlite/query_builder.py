from poridhiweb.orm.column import PrimaryKey, ForeignKey, Column
from poridhiweb.orm.sqlite.sqlite_types import SQL_TYPE_MAP
from poridhiweb.orm.table import Table


class QueryBuilder:
    @classmethod
    def build_create_table_sql(cls, table_type: type[Table]):
        CREATE_TABLE_SQL = "CREATE TABLE IF NOT EXISTS {name} ({fields});"
        fields = []
        table_name = table_type.__name__.lower()
        for name, column in table_type._columns.items():
            sql_type = SQL_TYPE_MAP[column.type]
            if isinstance(column, PrimaryKey):
                sql = f"{name} {sql_type.value} PRIMARY KEY"
                if column.auto_increment:
                    sql += " AUTOINCREMENT"
                fields.append(sql)
            elif isinstance(column, ForeignKey):
                fields.append(f"{name}_id {sql_type.value}")
            elif isinstance(column, Column):
                fields.append(f"{name} {sql_type.value}")

        fields = ", ".join(fields)
        return CREATE_TABLE_SQL.format(name=table_name, fields=fields)

    @classmethod
    def build_insert_sql(cls, table_instance: Table) -> tuple[str, list]:
        # "INSERT INTO author (age, name) VALUES (?, ?);"
        INSERT_SQL = "INSERT INTO {name} ({fields}) VALUES ({placeholders});"

        fields = []
        placeholders = []
        values = []

        table_name = table_instance.__class__.__name__.lower()
        columns: dict[str, Column] = table_instance._columns

        for name, field in columns.items():
            if isinstance(field, ForeignKey):
                fields.append(name + "_id")
                field_value: Table = getattr(table_instance, name)
                values.append(field_value.id)
                placeholders.append("?")
            elif isinstance(field, Column):
                fields.append(name)
                values.append(getattr(table_instance, name))
                placeholders.append("?")

        fields = ", ".join(fields)
        placeholders = ", ".join(placeholders)

        query = INSERT_SQL.format(
            name=table_name,
            fields=fields,
            placeholders=placeholders,
        )
        return query, values

    @classmethod
    def build_select_all_sql(cls, table_type: type[Table]):
        # SELECT id, name, age from author
        SELECT_ALL_SQL = 'SELECT {fields} FROM {name};'

        fields = []

        table_name = table_type.__name__.lower()
        columns = table_type._columns
        for field_name, field in columns.items():
            if isinstance(field, ForeignKey):
                fields.append(field_name + "_id")
            elif isinstance(field, Column):
                fields.append(field_name)

        sql = SELECT_ALL_SQL.format(name=table_name, fields=", ".join(fields))
        return sql, fields

    @classmethod
    def build_select_by_id_sql(cls, table_type: type[Table], id: int):
        SELECT_BY_ID_SQL = "SELECT {fields} FROM {name} WHERE id = ?;"
        table_name = table_type.__name__.lower()

        fields = []
        columns = table_type._columns

        for field_name, field in columns.items():
            if isinstance(field, ForeignKey):
                fields.append(field_name + "_id")
            elif isinstance(field, Column):
                fields.append(field_name)

        params = [id]
        sql = SELECT_BY_ID_SQL.format(name=table_name, fields=", ".join(fields))
        return sql, fields, params

    @classmethod
    def build_update_sql(cls, table_instance: Table):
        # UPDATE author SET name = ?, age = ? WHERE id = ?;
        UPDATE_SQL_TEMPLATE = "UPDATE {name} SET {fields} WHERE id = ?;"

        fields = []
        params = []

        table_name = table_instance.__class__.__name__.lower()
        columns = table_instance._columns

        for field_name, field in columns.items():
            if isinstance(field, PrimaryKey):
                continue
            if isinstance(field, ForeignKey):
                fields.append(field_name + "_id = ?")
                fk_instance: Table = getattr(table_instance, field_name)
                params.append(fk_instance.id)
            elif isinstance(field, Column):
                fields.append(field_name + " = ?")
                field_value = getattr(table_instance, field_name)
                params.append(field_value)

        params.append(getattr(table_instance, 'id'))

        sql = UPDATE_SQL_TEMPLATE.format(
            name=table_name,
            fields=", ".join(fields),
        )
        return sql, fields, params

    @classmethod
    def build_delete_sql(cls, table_type: type[Table], id: int):
        # DELETE FROM author WHERE id = 1;
        DELETE_SQL_TEMPLATE = "DELETE FROM {name} WHERE id = ?;"
        table_name = table_type.__name__.lower()
        params = [id]
        sql = DELETE_SQL_TEMPLATE.format(name=table_name)
        return sql, params

import os
import sqlite3

import pytest

from poridhiweb.orm.database import Database
from poridhiweb.orm.exceptions import RecordNotFound
from poridhiweb.orm.sqlite.query_builder import QueryBuilder
from poridhiweb.orm.sqlite.sqlite_types import SQL_TYPE_MAP
from tests.test_orm.conftest import Author, Book
from poridhiweb.utils.json_util import JSONUtils
from poridhiweb.orm.db_factory import DatabaseFactory, Dialect

db_factory = DatabaseFactory(dialect=Dialect.SQLITE)


class TestSqliteORMCreation:
    def setup_class(self):
        self.db: Database = db_factory.get_connection(path="./test.db")

    def teardown_class(self):
        os.remove("./test.db")

    def test_db_conn(self):
        assert isinstance(self.db.connection, sqlite3.Connection)

    def test_define_tables(self):
        assert Author.name.type == str
        assert SQL_TYPE_MAP[Author.name.type].value == "TEXT"

        assert Author.age.type == int
        assert SQL_TYPE_MAP[Author.age.type].value == "INTEGER"

    def test_create_table(self):
        self.db.create(Author)
        self.db.create(Book)
        db_tables = self.db.tables
        assert "author" in db_tables
        assert "book" in db_tables

    def test_table_creation_sql(self):
        assert QueryBuilder.build_create_table_sql(Author) == "CREATE TABLE IF NOT EXISTS author (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER);"
        assert QueryBuilder.build_create_table_sql(Book) == "CREATE TABLE IF NOT EXISTS book (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, published INTEGER, author_id INTEGER);"


class TestSqliteORMInsert:
    def setup_class(self):
        self.db: Database = db_factory.get_connection(path="./test.db")
        self.db.create(Author)
        self.db.create(Book)

    def teardown_class(self):
        os.remove("./test.db")

    def test_row_insertion_sql(self):
        author = Author(name="Author 1", age="25")
        book = Book(title="Test Book", published=1, author=author)

        insert_author_sql, a_params = QueryBuilder.build_insert_sql(author)
        insert_book_sql, b_params = QueryBuilder.build_insert_sql(book)

        assert insert_author_sql == 'INSERT INTO author (id, name, age) VALUES (?, ?, ?);'
        assert insert_book_sql == 'INSERT INTO book (id, title, published, author_id) VALUES (?, ?, ?, ?);'

    def test_row_insertion(self):
        author = Author(name="Garry C.", age=45)
        self.db.save(author)
        assert author.id is not None
        assert author.name == "Garry C."
        assert author.age == 45

        book = Book(title="The house of dragon", published=1, author=author)
        self.db.save(book)
        assert book.id is not None
        assert book.author == author
        assert book.title == "The house of dragon"


class TestSqliteORMRead:
    def setup_class(self):
        self.db: Database = db_factory.get_connection(path="./test.db")
        self.db.create(Author)
        self.db.create(Book)

    def teardown_class(self):
        os.remove("./test.db")

    def test_get_all_sql(self):
        # sql, fields = Author._get_select_all_sql()
        sql, fields = QueryBuilder.build_select_all_sql(Author)
        assert sql == "SELECT id, name, age FROM author;"
        assert fields == ["id", "name", "age"]

        sql, fields = QueryBuilder.build_select_all_sql(Book)
        assert sql == "SELECT id, title, published, author_id FROM book;"
        assert fields == ["id", "title", "published", "author_id"]

    def test_get_all(self):
        author = Author(name="Garry C.", age=45)
        self.db.save(author)
        book = Book(title="The house of dragon", published=True, author=author)
        self.db.save(book)

        author = Author(name="Kathy Sierra", age=60)
        self.db.save(author)
        book = Book(title="Headfirst Design Pattern", published=True, author=author)
        self.db.save(book)

        authors = self.db.get_all(Author)
        assert len(authors) == 2

        books = self.db.get_all(Book)
        assert len(books) == 2

    def test_get_by_id(self):
        author = Author(name="Garry C.", age=45)
        self.db.save(author)

        book = Book(title="The house of dragon", published=True, author=author)
        self.db.save(book)

        author_fetched: Author = self.db.get_by_id(Author, author.id)
        assert author_fetched._data == author._data

        book_fetched: Book = self.db.get_by_id(table_type=Book, id=book.id)

        assert book_fetched.id == book.id
        assert book_fetched.title == book.title
        assert book_fetched.published == book.published

        assert book_fetched.author._data == author._data

        # Dictionary Comparison
        book_fetched_data: dict = JSONUtils.to_dict(book_fetched)
        book_data: dict = JSONUtils.to_dict(book)

        assert book_data == book_fetched_data


class TestSqliteORMUpdate:
    def setup_method(self):
        self.db: Database = db_factory.get_connection(path="./test.db")
        self.db.create(Author)
        self.db.create(Book)

    def teardown_method(self):
        os.remove("./test.db")

    def test_update_sql(self):
        author = Author(name="Garry C.", age=45)
        self.db.save(author)

        book = Book(title="The house of dragon", published=True, author=author)
        self.db.save(book)

        autor_to_update: Author = self.db.get_by_id(Author, author.id)
        autor_to_update.name = "Garry C. Mertin"
        autor_to_update.age = 50
        update_sql, column_names, params = QueryBuilder.build_update_sql(autor_to_update)
        assert update_sql == "UPDATE author SET name = ?, age = ? WHERE id = ?;"
        assert column_names == ["name = ?", "age = ?"]
        assert params == ["Garry C. Mertin", 50, autor_to_update.id]

        book_to_update: Book = self.db.get_by_id(Book, book.id)
        update_sql, column_names, params = QueryBuilder.build_update_sql(book_to_update)
        assert update_sql == "UPDATE book SET title = ?, published = ?, author_id = ? WHERE id = ?;"
        assert column_names == ["title = ?", "published = ?", "author_id = ?"]

    def test_update_author(self):
        author = Author(name="Garry C.", age=45)
        self.db.save(author)

        autor_to_update: Author = self.db.get_by_id(Author, author.id)
        autor_to_update.name = "Garry C. Mertin"
        autor_to_update.age = 50
        self.db.update(autor_to_update)

        updated_author_fetched: Author = self.db.get_by_id(Author, author.id)
        assert JSONUtils.to_dict(updated_author_fetched) == JSONUtils.to_dict(autor_to_update)

    def test_update_book(self):
        author = Author(name="Garry C.", age=45)
        self.db.save(author)

        author_2 = Author(name="Robert C Martin", age=60)
        self.db.save(author_2)

        book = Book(title="The house of dragon", published=True, author=author)
        self.db.save(book)

        book_to_update: Book = self.db.get_by_id(Book, book.id)
        book_to_update.title = "Teach Yourself C"
        book_to_update.author = author_2
        self.db.update(book_to_update)

        updated_book_fetched: Book = self.db.get_by_id(Book, book.id)
        assert updated_book_fetched.title == "Teach Yourself C"
        assert updated_book_fetched.author.name == "Robert C Martin"
        assert JSONUtils.to_dict(updated_book_fetched.author) == JSONUtils.to_dict(author_2)
        assert JSONUtils.to_dict(updated_book_fetched) == JSONUtils.to_dict(book_to_update)


class TestSqliteORMDelete:
    def setup_method(self):
        self.db: Database = db_factory.get_connection(path="./test.db")
        self.db.create(Author)
        self.db.create(Book)

    def teardown_method(self):
        os.remove("./test.db")

    def test_delete_sql(self):
        author = Author(name="Garry C.", age=45)
        self.db.save(author)

        sql, params = QueryBuilder.build_delete_sql(Author, author.id)
        assert sql == "DELETE FROM author WHERE id = ?;"
        assert params == [author.id]

    def test_delete_author(self):
        author = Author(name="Garry C.", age=45)
        self.db.save(author)

        self.db.delete(Author, author.id)

        with pytest.raises(
            RecordNotFound,
            match=f"Table author with id {author.id} not found"
        ):
            self.db.get_by_id(Author, author.id)

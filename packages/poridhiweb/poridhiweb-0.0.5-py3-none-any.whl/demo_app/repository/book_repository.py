from demo_app.models.book import Book
from demo_app import db
from demo_app.repository.author_repository import AuthorRepository


class BookRepository:
    def __init__(self):
        self.author_repository = AuthorRepository()

    def insert(self, book: Book) -> Book:
        db.save(book)
        return book

    def all(self) -> list[Book]:
        return db.get_all(Book)

    def get_by_id(self, id: int) -> Book | None:
        return db.get_by_id(Book, id)

    def delete(self, id):
        book = self.get_by_id(id)
        db.delete(Book, book.id)

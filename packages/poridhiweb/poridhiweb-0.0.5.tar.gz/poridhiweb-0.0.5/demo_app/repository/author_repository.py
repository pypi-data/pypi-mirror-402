from demo_app import db
from demo_app.models.book import Author


class AuthorRepository:
    def insert(self, name: str, age: int) -> Author:
        author = Author(name=name, age=age)
        db.save(author)
        return author

    def all(self) -> list[Author]:
        return db.get_all(Author)

    def get_by_id(self, id: int) -> Author:
        return db.get_by_id(Author, id)

    def delete(self, id):
        book = self.get_by_id(id)
        db.delete(Author, book.id)
        return True

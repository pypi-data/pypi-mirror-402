from demo_app.exceptions import ResourceNotFoundException
from demo_app.models.book import Book
from demo_app.repository.book_repository import BookRepository
from poridhiweb.orm.exceptions import RecordNotFound


class BookService:
    def __init__(self):
        self.repository = BookRepository()
        self.seed_data(seed=False)

    def seed_data(self, seed=True):
        if seed:
            self.repository.insert(
                Book(name="The Great Gatsby", author="F. Scott Fitzgerald")
            )
            self.repository.insert(
                Book(name="Life of Pi", author="Yann Martel")
            )

    def get_all(self) -> list[Book]:
        return self.repository.all()

    def create(self, schema: dict) -> Book:
        book_schema = Book(**schema)
        return self.repository.insert(
            book_schema
        )

    def delete(self, book_id: int) -> None:
        try:
            self.repository.delete(book_id)
        except RecordNotFound:
            raise ResourceNotFoundException(f"Book associated with id: {book_id} not found")

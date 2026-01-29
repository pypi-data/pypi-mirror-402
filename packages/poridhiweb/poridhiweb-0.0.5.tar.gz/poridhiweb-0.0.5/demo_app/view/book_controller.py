from http import HTTPStatus

from webob.request import Request

from demo_app import app
from demo_app.decorators import login_required
from demo_app.models.book import Book
from demo_app.service.book_service import BookService
from poridhiweb.models.responses import JSONResponse, HTMLResponse, Response

service = BookService()


@app.route('/books/all', allowed_methods=["GET"])
def get_all_books(request: Request) -> Response:
    books: list[Book] = service.get_all()
    html_content = app.template("books.html", context={"books": books})
    return HTMLResponse(html_content)


@app.route('/books', allowed_methods=["POST"])
@login_required
def create_book(request: Request) -> Response:
    book_created: Book = service.create(request.json)
    return JSONResponse(book_created, status=HTTPStatus.CREATED)


@app.route('/books/{book_id:d}', allowed_methods=["DELETE"])
@login_required
def delete_book(request: Request, book_id: int) -> Response:
    service.delete(book_id)
    return JSONResponse({
        "message": f"Book associated with {book_id} was deleted"
    })

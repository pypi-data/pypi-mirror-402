from webob.response import Response

from poridhiweb.middlewares import ErrorHandlerMiddleware
from tests.constants import BASE_URL


def test_class_based_handler_get(app, client):
    response_text = "This is a {} request"

    @app.route("/books")
    class BookResource:
        def get(self, req):
            return Response("This is a GET request")

        def post(self, req):
            return Response("This is a POST request")

    response = client.get("http://testserver/books")
    assert response.text == response_text.format("GET")

    response = client.post("http://testserver/books")
    assert response.text == response_text.format("POST")


def test_class_based_handler_method_not_allowed(app, client):
    app.add_middleware(ErrorHandlerMiddleware)
    exp_response = {
        "message": "POST request is not allowed for /books"
    }

    @app.route("/books")
    class BookResource:
        def get(self, req):
            return Response("This is a GET request")

    response = client.post(f"{BASE_URL}/books")
    assert response.status_code == 405
    assert response.json() == exp_response


def test_class_based_handler_with_explicit_routing(app, client):
    @app.route("/books")
    class BookResource:
        def get(self, req):
            return Response("Get all books")

        def get_by_id(self, req, book_id: int):
            return Response(text=f"Book found by id: {book_id}")

    app.add_route("/books/{book_id:d}", BookResource().get_by_id)

    response = client.get(f"{BASE_URL}/books/1")
    assert response.status_code == 200
    assert response.text == "Book found by id: 1"

    response = client.get(f"{BASE_URL}/books")
    assert response.status_code == 200
    assert response.text == "Get all books"

from dataclasses import dataclass

import pytest
from webob.response import Response

from poridhiweb.common_handlers import CommonHandlers
from poridhiweb.constants import ContentType
from poridhiweb.exceptions import MethodNotAllowed
from poridhiweb.middlewares import ErrorHandlerMiddleware
from poridhiweb.models.responses import TextResponse, JSONResponse
from tests.constants import BASE_URL
from tests.utils.test_framework import TestFrameworkBuilder


def test_client_can_send_requests(app, client):
    RESPONSE_TEXT = "Hello from test client"

    @app.route("/test")
    def test_handler(req):
        return TextResponse(RESPONSE_TEXT)

    response = client.get(f"{BASE_URL}/test")
    assert response.text == RESPONSE_TEXT
    assert "text/plain" in response.headers["Content-Type"]


@pytest.mark.parametrize(
    "name, exp_result",
    [
        pytest.param(
            "Alice", {"username": "Alice"}, id="Alice",
        ),
        pytest.param(
            "Bob", {"username": "Bob"}, id="Bob",
        ),
        pytest.param(
            "Charlie", {"username": "Charlie"}, id="Charlie",
        )
    ]
)
def test_json_response_from_dict_based_data(app, client, name, exp_result):
    @app.route("/hello/{name}")
    def hello(req, name: str):
        return JSONResponse({"username": name})

    response = client.get(f"{BASE_URL}/hello/{name}")
    assert response.json() == exp_result
    assert ContentType.JSON in response.headers["Content-Type"]


@pytest.mark.parametrize(
    "name, exp_result",
    [
        pytest.param(
            "Alice", {"username": "Alice"}, id="Alice",
        ),
        pytest.param(
            "Bob", {"username": "Bob"}, id="Bob",
        ),
        pytest.param(
            "Charlie", {"username": "Charlie"}, id="Charlie",
        )
    ]
)
def test_json_response_from_class_based_data(app, client, name, exp_result):
    @dataclass
    class Person:
        username: str

    @app.route("/hello/{name}")
    def hello(req, name: str):
        person = Person(name)
        return JSONResponse(person)

    response = client.get(f"{BASE_URL}/hello/{name}")
    assert response.json() == exp_result
    assert ContentType.JSON in response.headers["Content-Type"]


def test_json_response_with_list_of_objects(app, client):
    @dataclass
    class Address:
        long: float
        lat: float

    @dataclass
    class Person:
        username: str
        address: Address

    @app.route("/hello")
    def hello(req):
        persons = [
            Person("Bob", address=Address(long=5.5, lat=5.5)),
            Person("Charlie", address=Address(long=4.5, lat=4.5)),
        ]
        return JSONResponse(persons)

    response = client.get(f"{BASE_URL}/hello")
    assert ContentType.JSON in response.headers["Content-Type"]


def test_url_not_found(app, client):
    RESPONSE_TEXT = "Hello from test client"
    exp_response = {
        "message": f"Requested path: /hello does not exist"
    }

    @app.route("/test")
    def test_handler(req):
        return TextResponse(RESPONSE_TEXT)

    response = client.get(f"{BASE_URL}/hello")
    assert response.status_code == 404
    assert response.json() == exp_response


def test_generic_exception_handler(app, client):
    app.add_exception_handler(handler=CommonHandlers.generic_exception_handler)
    msg = "A test exception"
    exp_response = {
        "message": f"Unhanded Exception Occurred: {msg}"
    }

    @app.route("/test")
    def test_handler(req):
        raise RuntimeError(msg)

    response = client.get(f"{BASE_URL}/test")
    assert response.status_code == 500
    assert response.json() == exp_response


def test_explicitly_registered_route(app, client):
    RESPONSE_TEXT = "Hello from test client"

    def test_handler(req):
        return Response(text=RESPONSE_TEXT)

    app.add_route("/test", test_handler)

    response = client.get(f"{BASE_URL}/test")
    assert response.text == RESPONSE_TEXT


def test_method_not_allowed_request():
    app = TestFrameworkBuilder().build()
    client = app.test_session()

    @app.route("/home", allowed_methods=["post"])
    def home(req):
        return Response("Hello")

    with pytest.raises(MethodNotAllowed):
        client.get(f"{BASE_URL}/home")


def test_method_not_allowed_request_handled():
    app = TestFrameworkBuilder().build()
    app.add_middleware(ErrorHandlerMiddleware)
    client = app.test_session()

    @app.route("/home", allowed_methods=["post"])
    def home(req):
        return Response("Hello")

    response = client.get(f"{BASE_URL}/home")
    response.status_code = 405


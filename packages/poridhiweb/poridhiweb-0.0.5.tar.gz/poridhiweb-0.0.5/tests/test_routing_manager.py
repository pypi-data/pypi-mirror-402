import pytest
from webob.response import Response

from tests.conftest import TestFramework


def test_basic_route_adding(app: TestFramework):
    @app.route("/home")
    def home(req):
        return Response(
            text="Hello World"
        )


def test_duplicate_routing_exception(app: TestFramework):
    @app.route("/test")
    def first(req):
        return Response(
            text="First Handler"
        )

    with pytest.raises(
        RuntimeError,
        match="Path: /test already bind to another handler"
    ):
        @app.route("/test")
        def second(req):
            return Response(
                text="Second Handler"
            )

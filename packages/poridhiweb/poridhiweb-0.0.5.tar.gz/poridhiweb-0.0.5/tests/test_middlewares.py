from webob.request import Request
from webob.response import Response

from poridhiweb.middlewares import Middleware
from tests.constants import BASE_URL


def test_middleware_methods_are_called(app, client):
    class CustomMiddleware0(Middleware):
        def process_request(self, req: Request):
            assert "X-REQUEST-PROCESSING" not in req.headers
            req.headers["X-REQUEST-PROCESSING"] = 0

        def process_response(self, req: Request, res: Response):
            assert "X-RESPONSE-PROCESSING" in res.headers
            assert res.headers["X-RESPONSE-PROCESSING"] == "1"
            value = int(res.headers["X-RESPONSE-PROCESSING"]) + 1
            res.headers["X-RESPONSE-PROCESSING"] = str(value)

    class CustomMiddleware1(Middleware):
        def process_request(self, req: Request):
            assert "X-REQUEST-PROCESSING" in req.headers
            assert req.headers["X-REQUEST-PROCESSING"] == 0
            req.headers["X-REQUEST-PROCESSING"] = req.headers["X-REQUEST-PROCESSING"] + 1

        def process_response(self, req: Request, res: Response):
            assert "X-RESPONSE-PROCESSING" in res.headers
            assert res.headers["X-RESPONSE-PROCESSING"] == "0"
            value = int(res.headers["X-RESPONSE-PROCESSING"]) + 1
            res.headers["X-RESPONSE-PROCESSING"] = str(value)

    class CustomMiddleware2(Middleware):
        def process_request(self, req: Request):
            assert "X-REQUEST-PROCESSING" in req.headers
            assert req.headers["X-REQUEST-PROCESSING"] == 1
            req.headers["X-REQUEST-PROCESSING"] = req.headers["X-REQUEST-PROCESSING"] + 1

        def process_response(self, req: Request, res: Response):
            assert "X-RESPONSE-PROCESSING" not in res.headers
            res.headers["X-RESPONSE-PROCESSING"] = "0"

    app.add_middleware(CustomMiddleware2)
    app.add_middleware(CustomMiddleware1)
    app.add_middleware(CustomMiddleware0)

    @app.route('/hello')
    def index(req: Request) -> Response:
        assert "X-REQUEST-PROCESSING" in req.headers
        assert req.headers["X-REQUEST-PROCESSING"] == 2
        return Response("Hello World")

    response: Response = client.get(f'{BASE_URL}/hello')
    assert response.status_code == 200
    assert "X-RESPONSE-PROCESSING" in response.headers
    assert response.headers["X-RESPONSE-PROCESSING"] == "2"

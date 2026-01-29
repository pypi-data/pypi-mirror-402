import time
from typing import TYPE_CHECKING

from webob import Request
from webob.response import Response

from poridhiweb.common_handlers import CommonHandlers
from poridhiweb.exceptions import ResponseError
from poridhiweb.logger import create_logger

if TYPE_CHECKING:
    from poridhiweb.framework import PoridhiFrame


# logger = create_logger(__name__, level="DEBUG")
logger = create_logger(__name__)


class Middleware:
    def __init__(self, app: "PoridhiFrame"):
        self.app = app

    def __call__(self, environ, start_response):
        http_request = Request(environ)
        response = self.handle_request(http_request)
        return response(environ, start_response)

    def add(self, middleware_cls) -> None:
        logger.debug(f"{middleware_cls.__name__}(app={self.app.__class__.__name__})")
        self.app = middleware_cls(app=self.app)

    def process_request(self, req: Request) -> None:
        logger.debug(f"{self.__class__.__name__}::process_request")

    def process_response(self, req: Request, resp: Response) -> None:
        logger.debug(f"{self.__class__.__name__}::process_response")

    def handle_request(self, request: Request) -> Response:
        self.process_request(request)
        response = self.app.handle_request(request)
        self.process_response(request, response)
        return response


class ErrorHandlerMiddleware(Middleware):
    def handle_request(self, request: Request) -> Response:
        try:
            return super().handle_request(request)
        except ValueError as e:
            return CommonHandlers.handle_value_error(request, e)
        except ResponseError as e:
            return CommonHandlers.handle_response_error(request, e)
        except Exception as e:
            return CommonHandlers.generic_exception_handler(request, e)


class ReqResLoggingMiddleware(Middleware):
    def process_request(self, req: Request) -> None:
        super().process_request(req)
        logger.info("[%s] Requested URL: %s", req.method, req.path)


class ExecutionTimeMiddleware(Middleware):
    def process_request(self, req):
        super().process_request(req)
        req.start_time = time.time()

    def process_response(self, req, resp):
        super().process_response(req, resp)
        if hasattr(req, 'start_time'):
            duration = time.time() - req.start_time
            resp.headers['X-Response-Time'] = f"{duration:.4f}s"
            logger.info(f"Total Processing Time: {duration:.4f}")

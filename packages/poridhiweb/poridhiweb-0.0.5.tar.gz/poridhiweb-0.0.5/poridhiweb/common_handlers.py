import logging
from http import HTTPStatus

from webob import Request

from poridhiweb.exceptions import ResponseError
from poridhiweb.models.responses import Response, JSONResponse

logger = logging.getLogger(__name__)


class CommonHandlers:
    @staticmethod
    def generic_exception_handler(request: Request, excp: Exception) -> Response:
        logger.exception(excp)
        response = {
            "message": f"Unhanded Exception Occurred: {str(excp)}"
        }
        return JSONResponse(
            content=response,
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    @staticmethod
    def handle_value_error(request: Request, exc: ValueError) -> Response:
        logger.exception(exc)
        return JSONResponse(
            content={"message": str(exc)},
            status=HTTPStatus.BAD_REQUEST
        )

    @staticmethod
    def handle_response_error(request: Request, exc: ResponseError) -> Response:
        logger.exception(exc)
        return JSONResponse(
            content={"message": exc.message},
            status=exc.http_status
        )

    @staticmethod
    def url_not_found_handler(request: Request) -> Response:
        response = {
            "message": f"Requested path: {request.path} does not exist"
        }
        return JSONResponse(
            content=response,
            status=HTTPStatus.NOT_FOUND
        )

    @staticmethod
    def method_not_allowed_handler(request: Request) -> Response:
        response = {
            "message": f"{request.method} request is not allowed for {request.path}"
        }
        return Response(
            content=response,
            status=HTTPStatus.METHOD_NOT_ALLOWED
        )

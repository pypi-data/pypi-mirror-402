from http import HTTPStatus
from typing import Any

from webob.response import Response as BaseResponse

from poridhiweb.constants import ContentType
from poridhiweb.utils.common_utils import StatusUtils
from poridhiweb.utils.json_util import JSONUtils


class Response(BaseResponse):
    def __init__(self, status: HTTPStatus = HTTPStatus.OK, **kwargs):
        super().__init__(
            status=StatusUtils.to_str(status),
            **kwargs
        )


class TextResponse(Response):
    def __init__(self, content: str, status: HTTPStatus = HTTPStatus.OK, **kwargs):
        super().__init__(
            text=content,
            status=status,
            content_type=ContentType.TEXT,
            **kwargs
        )


class JSONResponse(Response):
    def __init__(self, content: dict | Any, status: HTTPStatus = HTTPStatus.OK, **kwargs):
        super().__init__(
            json=JSONUtils.to_dict(content),
            status=status,
            content_type=ContentType.JSON,
            **kwargs
        )


class HTMLResponse(Response):
    def __init__(self, content: str, status: HTTPStatus = HTTPStatus.OK, **kwargs):
        super().__init__(
            body=content,
            status=status,
            content_type=ContentType.HTML,
            **kwargs
        )

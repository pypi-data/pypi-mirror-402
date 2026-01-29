from webob.request import Request

from demo_app import app
from demo_app.models.token import Token
from demo_app.service.auth_service import AuthService
from poridhiweb.models.responses import JSONResponse

service = AuthService()


@app.route('/token', allowed_methods=["POST"])
def get_token(request: Request) -> JSONResponse:
    token: Token = service.get_auth_token(**request.json)
    return JSONResponse(token)

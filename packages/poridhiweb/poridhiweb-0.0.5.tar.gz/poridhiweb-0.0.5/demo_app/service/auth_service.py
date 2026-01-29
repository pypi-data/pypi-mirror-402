from demo_app.constants import STATIC_TOKEN
from demo_app.models.token import Token


class AuthService:

    def get_auth_token(self, **kwargs) -> Token:
        return Token(token=STATIC_TOKEN)

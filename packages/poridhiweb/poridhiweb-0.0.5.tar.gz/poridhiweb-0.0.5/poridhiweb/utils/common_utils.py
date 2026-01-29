from http import HTTPStatus


class StatusUtils:
    @staticmethod
    def to_str(status: HTTPStatus) -> str:
        return f"{status.value} {status.phrase}"

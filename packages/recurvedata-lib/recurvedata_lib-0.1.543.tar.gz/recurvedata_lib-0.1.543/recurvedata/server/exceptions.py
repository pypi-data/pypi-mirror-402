from recurvedata.server.error_code import ERR


class RecurveException(Exception):
    _default_code: ERR = ERR.UNKNOWN_ERROR
    _default_status_code: int = 200

    def __init__(self, code: ERR = None, data: dict | str = None, status_code: int = None):
        self.code = code or self._default_code
        self.data = data
        self.status_code = status_code or self._default_status_code

    def to_dict(self) -> dict:
        return self.code.to_dict() | {"data": self.data}


class InternalServerError(RecurveException):
    _default_code = ERR.INTERNAL_SERVER_ERROR
    _default_status_code = 500

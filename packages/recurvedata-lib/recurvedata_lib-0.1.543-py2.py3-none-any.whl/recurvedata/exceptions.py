from functools import wraps

from recurvedata.error_codes import ERR, BaseErrorCode


class RecurveException(Exception):
    _default_code: ERR = ERR.UNKNOWN_ERROR

    def __init__(self, data: dict | str = None, code: BaseErrorCode = None):
        self.code = code or self._default_code
        self.data = data

    def to_dict(self) -> dict:
        return self.code.to_dict() | {"data": self.data}


class InvalidArgument(RecurveException):
    _default_code: ERR = ERR.INVALID_ARGUMENT


class APIError(RecurveException):
    """Raised when an API request fails."""

    _default_code: ERR = ERR.API_REQUEST_FAILED


class UnauthorizedError(RecurveException):
    """Raised when an unauthorized request is made."""

    _default_code = ERR.UNAUTHORIZED


class MaxRetriesExceededException(RecurveException):
    """Raised when the maximum number of retries is exceeded."""

    _default_code: ERR = ERR.MAX_RETRIES_EXCEEDED


class TimeoutException(RecurveException):
    """Raised when a timeout occurs."""

    _default_code: ERR = ERR.TIMEOUT


class WrapRecurveException(RecurveException):
    """
    raised in wrap_error function
    """

    def __init__(self, code: ERR, exception: Exception, data: dict | str = None):
        super().__init__(data=data, code=code)
        self.exception: Exception = exception

    def to_dict(self) -> dict:
        return self.code.to_dict() | {"data": self.data, "exception": str(self.exception)}


def wrap_error(err_code: ERR):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except RecurveException:
                raise
            except Exception as e:
                wrapped_error = WrapRecurveException(err_code, e)
                raise wrapped_error

        return wrapper

    return decorator

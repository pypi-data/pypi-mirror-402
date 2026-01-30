import os
from traceback import format_exc
from typing import Any, Self

from pydantic import BaseModel

from recurvedata.exceptions import RecurveException, WrapRecurveException
from recurvedata.executors.schemas import ConnectionItem


class ConnectionAndVariables(BaseModel):
    connection: ConnectionItem
    variables: dict


class ResponseError(BaseModel):
    code: str
    reason: str | None
    exception: str | None = None
    traceback: str | None = None
    data: dict | str | None = None

    @classmethod
    def from_recurve_exception(cls, recurve_exception: RecurveException) -> Self:
        if recurve_exception.data:
            reason = f"{recurve_exception.code.message} {recurve_exception.data}"
        else:
            reason = recurve_exception.code.message
        if isinstance(recurve_exception, WrapRecurveException):
            exception = str(recurve_exception.exception)
        else:
            exception = None
        return cls(
            code=recurve_exception.code.code,
            reason=reason,
            exception=exception,
            traceback=format_exc(),
            data=recurve_exception.data,
        )


class ResponseModel(BaseModel):
    ok: bool
    error: ResponseError | None = None
    data: Any = None

    def model_dump_json_file(self, filename: str):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            f.write(self.model_dump_json(indent=2))

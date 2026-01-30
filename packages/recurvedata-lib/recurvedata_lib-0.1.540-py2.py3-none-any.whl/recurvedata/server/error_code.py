from enum import Enum, EnumMeta


class ErrorCodeMeta(EnumMeta):
    _error_codes = set()

    def __new__(metacls, clsname, bases, classdict):
        enum_members = {k: v for k, v in classdict.items() if not k.startswith("_")}
        for name, code in enum_members.items():
            if type(code) is not tuple:
                continue
            for error_code in metacls._error_codes:
                if code[0] == error_code[1][0]:
                    raise ValueError(f"Error code {code[0]} in {clsname} already exists globally")
            metacls._error_codes.add((name, code))
        return super().__new__(metacls, clsname, bases, classdict)

    @classmethod
    def error_codes(cls):
        return sorted(list(cls._error_codes), key=lambda x: x[1][0])


class BaseErrorCode(Enum, metaclass=ErrorCodeMeta):
    @property
    def code(self):
        return self.value[0]

    @property
    def message(self):
        return self.value[1]

    def to_dict(self):
        return {"code": self.code, "msg": self.message}

    def exception(self, data: dict | None = None, status_code: int | None = None):
        from recurvedata.server.exceptions import RecurveException

        return RecurveException(self, data, status_code)


class ErrorCode(BaseErrorCode):
    # 00: General
    INTERNAL_SERVER_ERROR = ("B0001", "Internal Server Error")
    NOT_IMPLEMENTED = ("B0002", "Not Implemented")

    UNKNOWN_ERROR = ("D0001", "Unknown Error")


ERR = ErrorCode  # shortcut

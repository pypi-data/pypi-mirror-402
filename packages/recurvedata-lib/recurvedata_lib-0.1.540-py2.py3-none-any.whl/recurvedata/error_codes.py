"""
copied from recurve-server
"""

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

    def exception(self, data: dict | None = None):
        from recurvedata.exceptions import RecurveException

        return RecurveException(data=data, code=self)


class ErrorCode(BaseErrorCode):
    # 00: General
    UNAUTHORIZED = ("A0001", "Unauthorized")
    PERMISSION_DENIED = ("A0003", "Permission Denied")
    NOT_FOUND = ("A0004", "Not Found")
    ALREADY_EXISTS = ("A0008", "Already Exists")
    INVALID_ARGUMENT = ("A0010", "Invalid Argument")
    MAX_FILE_SIZE_EXCEEDED = ("A0011", "Max File Size Exceeded")
    INVALID_FILE_FORMAT = ("A0012", "Invalid File Format")
    INVALID_READONLY_QUERY = ("A0013", "Query Should be Read Only")
    INTERNAL_SERVER_ERROR = ("B0001", "Internal Server Error")
    NOT_IMPLEMENTED = ("B0002", "Not Implemented")
    FAILED_TO_PARSE_QUERY = ("B0003", "Failed to Parse Query")

    UNKNOWN_ERROR = ("D0001", "Unknown Error")
    GUANYUAN_BI_API_ERROR = ("D0002", "Guanyuan BI API Error")

    # agent task
    API_REQUEST_FAILED = ("A1202", "API request failed")
    MAX_RETRIES_EXCEEDED = ("A1203", "max retries exceeded")
    TIMEOUT = ("A1204", "time out")

    # data service
    DP_FETCH_CONNECTION_FAILED = ("A1401", "DP fetch connection failed")
    PREVIEW_DATA_FAILED = ("A1402", "Preview data failed")


ERR = ErrorCode  # shortcut

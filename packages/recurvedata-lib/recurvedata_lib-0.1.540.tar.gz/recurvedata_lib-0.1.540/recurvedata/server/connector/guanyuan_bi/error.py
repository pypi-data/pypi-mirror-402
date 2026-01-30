from recurvedata.error_codes import ERR
from recurvedata.exceptions import RecurveException


class GuanyuanApiError(RecurveException):
    _default_code = ERR.GUANYUAN_BI_API_ERROR

import json
from enum import Enum

from recurvedata.utils.date_time import as_local_datetime


def str_2_bool(val: str):
    val = val.lower()
    if val in ("true", "1"):
        return True
    elif val in ("false", "0"):
        return False
    return val


def str_2_int(val: str):
    if val.isdigit():
        return int(val)
    if val[0] == "-" and val[1:].isdigit():
        return int(val)
    return val


def str_2_float(val: str):
    try:
        return float(val)
    except Exception:
        return val


class VariableType(str, Enum):
    INT = "INT"
    FLOAT = "FLOAT"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    DATETIME = "DATETIME"
    JSON = "JSON"
    PYTHON_CODE = "PYTHON_CODE"


VAR_CONVERT_STRING_FUNCS = {
    VariableType.INT: str_2_int,
    VariableType.FLOAT: str_2_float,
    VariableType.BOOLEAN: str_2_bool,
    VariableType.STRING: lambda x: x,
    VariableType.DATE: lambda x: as_local_datetime(x).date(),
    VariableType.DATETIME: lambda x: as_local_datetime(x),
    VariableType.JSON: json.loads,
}

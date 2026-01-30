import datetime
import decimal
import json
import uuid
from typing import Any

try:
    import orjson
except ImportError:
    orjson = None


def _json_default(obj: Any) -> str:
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    if isinstance(obj, datetime.timedelta):
        return str(obj)
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, decimal.Decimal):
        return str(obj)
    raise TypeError(f"Object of type '{obj.__class__.__name__}' is not JSON serializable")


def _orjson_default(obj: Any) -> str:
    if isinstance(obj, datetime.timedelta):
        return str(obj)
    if isinstance(obj, decimal.Decimal):
        return str(obj)
    raise TypeError(f"Object of type '{obj.__class__.__name__}' is not JSON serializable")


def pretty_print(v):
    print(dumps(v, indent=2, ensure_ascii=False))


def dumps(data: Any, **kwargs) -> str:
    """Serialize ``data`` to JSON. Uses orjson if available."""

    if orjson is None:
        if not kwargs.get("indent", False):
            kwargs.setdefault("separators", (",", ":"))
        return json.dumps(data, default=_json_default, **kwargs)

    # orjson does not support all the same kwargs as json.dumps
    option = orjson.OPT_NON_STR_KEYS
    if kwargs.pop("indent", False):
        option |= orjson.OPT_INDENT_2
    if kwargs.pop("sort_keys", False):
        option |= orjson.OPT_SORT_KEYS

    return orjson.dumps(data, default=_orjson_default, option=option).decode()


def loads(data: str) -> Any:
    """Deserialize ``data`` from JSON. Uses orjson if available."""

    if orjson is None:
        return json.loads(data)

    return orjson.loads(data)


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.date):
            return obj.isoformat()

        if isinstance(obj, datetime.timedelta):
            return str(obj)

        super(JSONEncoder, self).default(obj)


def json_dumps(data, **kwargs):
    return json.dumps(data, cls=JSONEncoder, **kwargs)


def json_loads(content: str, **kwargs):
    return json.loads(content, **kwargs)

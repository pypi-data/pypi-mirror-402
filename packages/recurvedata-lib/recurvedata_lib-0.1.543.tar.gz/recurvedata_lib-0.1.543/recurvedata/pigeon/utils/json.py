import datetime
import decimal
import json


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)

        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()

        if isinstance(obj, datetime.timedelta):
            return str(obj)

        return super().default(obj)


def json_dumps(obj, **kwargs):
    kwargs.setdefault('cls', JSONEncoder)
    return json.dumps(obj, **kwargs)


def dump_json(obj, fp=None, **kwargs):
    kwargs.setdefault('indent', 4)
    kwargs.setdefault('ensure_ascii', False)
    kwargs.setdefault('sort_keys', True)
    kwargs.setdefault('cls', JSONEncoder)
    if fp is None:
        return json.dumps(obj, **kwargs)
    else:
        if isinstance(fp, str):
            with open(fp, 'w') as fp:
                return json.dump(obj, fp, **kwargs)
        return json.dump(obj, fp, **kwargs)


def load_json(fp, **kwargs):
    if isinstance(fp, str):
        with open(fp, 'r') as fp:
            return json.load(fp, **kwargs)
    else:
        return json.load(fp, **kwargs)

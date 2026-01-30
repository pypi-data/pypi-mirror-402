import json

import dateutil.parser

from recurvedata.pigeon.schema import types


class Field(object):
    def __init__(self, name, type, size=None, comment=None, extra=None):
        self.name = name
        self.type = type
        self.size = size
        self.comment = comment
        self.extra = extra

        self._cast_func = {
            types.INT8: self._cast_to_int,
            types.INT16: self._cast_to_int,
            types.INT32: self._cast_to_int,
            types.INT64: self._cast_to_int,
            types.FLOAT32: self._cast_to_float,
            types.FLOAT64: self._cast_to_float,
            types.BOOLEAN: self._cast_to_boolean,
            types.DATETIME: self._cast_to_datetime,
            types.DATE: self._cast_to_date,
            types.JSON: self._cast_to_json,
        }.get(self.type, self._cast_pass)

    def cast(self, value):
        if value is None:
            return None
        if value == "NULL":
            return None
        return self._cast_func(value)

    def _cast_pass(self, value):
        return value

    def _cast_to_int(self, value: str):
        if value == "":
            return 0
        return int(value)

    def _cast_to_float(self, value: str):
        if value == "":
            return 0.0
        return float(value)

    def _cast_to_boolean(self, value: str):
        if value.lower() in ("", "0", "false"):
            return False
        return True

    def _cast_to_datetime(self, value: str):
        if value == "":
            return None
        return dateutil.parser.parse(value)

    def _cast_to_date(self, value: str):
        if value == "":
            return None
        return dateutil.parser.parse(value).date()

    def _cast_to_json(self, value: str):
        if value in ("",):
            # 正常情况下不会有 ''，很可能是从 CSV 文件读到了空字符，当作 None 处理
            return None
        return json.loads(value)

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type,
            "size": self.size,
            "comment": self.comment,
            "extra": self.extra,
        }

    def __str__(self):
        return f'<Field ("{self.name}", "{self.type}")>'

    def __repr__(self):
        return f'<Field ("{self.name}", "{self.type}")>'


class Schema(object):
    def __init__(self, fields=None):
        self.fields = fields or []

    def add_field(self, field):
        # TODO(liyangliang): clean field names, handle special characters and duplications
        self.fields.append(field)

    def add_field_by_attrs(self, name, type, size=None, comment=None, extra=None):
        self.add_field(Field(name, type, size, comment, extra))

    def remove_field(self, name):
        self.fields = [x for x in self.fields if x.name != name]

    def keep_fields(self, names):
        self.fields = [x for x in self.fields if x.name in names]

    @property
    def field_names(self):
        return [x.name for x in self.fields]

    def __iter__(self):
        return iter(self.fields)

    def to_list(self):
        return [x.to_dict() for x in self.fields]

    def to_json(self):
        return json.dumps(self.to_list())

    def dump(self, filename):
        with open(filename, "w") as f:
            json.dump(self.to_list(), f, indent=2)

    @classmethod
    def load(cls, filename):
        with open(filename) as f:
            data = json.load(f)
        return cls([Field(**item) for item in data])

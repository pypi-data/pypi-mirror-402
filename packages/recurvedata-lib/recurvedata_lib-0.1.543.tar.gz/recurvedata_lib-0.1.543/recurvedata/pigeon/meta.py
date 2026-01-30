import datetime
import json

import cytoolz as toolz

from recurvedata.pigeon.schema import Schema


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.date):
            return o.isoformat()
        if isinstance(o, datetime.timedelta):
            return str(o)
        if isinstance(o, Schema):
            return o.to_list()
        return super().default(o)


class Meta(object):
    def to_dict(self):
        raise NotImplementedError()

    def to_json(self, **kwargs):
        params = toolz.merge({"sort_keys": True, "ensure_ascii": False, "cls": JSONEncoder}, kwargs)
        return json.dumps(self.to_dict(), **params)


class HandlerMeta(Meta):
    def __init__(self):
        self.reset()

    def reset(self):
        self.num_input_rows = 0
        self.num_output_rows = 0
        self.num_error_rows = 0
        self.error_log_size = 0  # 当前打印的报错 row 字符串的字符数

    def to_dict(self):
        return {
            "num_input_rows": self.num_input_rows,
            "num_output_rows": self.num_output_rows,
            "num_error_rows": self.num_error_rows,
            "error_log_size": self.error_log_size,
        }


class HandlerFactoryMeta(HandlerMeta):
    def __init__(self, name):
        self.name = name
        super().__init__()

    def update(self, handler_meta):
        self.num_input_rows += handler_meta.num_input_rows
        self.num_output_rows += handler_meta.num_output_rows
        self.num_error_rows += handler_meta.num_error_rows
        self.error_log_size += handler_meta.error_log_size

    def to_dict(self):
        d = super().to_dict()
        d["name"] = self.name
        return d


class DumperWorkerMeta(Meta):
    def __init__(self):
        self.num_dumped_rows = 0
        self.schema = None
        self.handlers_meta = None

    def to_dict(self):
        return {
            "num_dumped_rows": self.num_dumped_rows,
            "schema": self.schema,
            "handlers_meta": [x.to_dict() for x in self.handlers_meta],
        }


class DumperMeta(Meta):
    def __init__(self, context=None):
        self.time_start = None
        self.time_finish = None
        self.num_dumped_rows = 0
        self.context = context
        self.schema = None
        self.handlers_meta = []

    def mark_start(self):
        self.time_start = datetime.datetime.now()

    def mark_finish(self):
        self.time_finish = datetime.datetime.now()

    @property
    def rows_per_second(self):
        return self.num_dumped_rows / (self.time_finish - self.time_start).total_seconds()

    @property
    def duration(self):
        if not self.time_start:
            return None
        if not self.time_finish:
            return datetime.datetime.now() - self.time_start
        return self.time_finish - self.time_start

    def to_dict(self):
        return {
            "time_start": self.time_start,
            "time_finish": self.time_finish,
            "time_duration": self.duration,
            "num_dumped_rows": self.num_dumped_rows,
            "rows_per_second": self.rows_per_second,
            "context": self.context,
            "schema": self.schema,
            "handlers_meta": [x.to_dict() for x in self.handlers_meta],
        }

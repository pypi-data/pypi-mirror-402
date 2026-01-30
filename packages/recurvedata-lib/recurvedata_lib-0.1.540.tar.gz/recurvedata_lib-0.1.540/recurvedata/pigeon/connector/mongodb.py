import datetime
from collections import OrderedDict

import bson
import pymongo

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.schema import Schema, types
from recurvedata.pigeon.utils import LoggingMixin


@register_connector_class(['mongodb'])
class MongoDBConnector(LoggingMixin):
    def __init__(self, host=None, port=None, **kwargs):
        self.host = host
        self.port = port

        kwargs.setdefault('document_class', OrderedDict)
        self.kwargs = kwargs

    def connect(self, **kwargs):
        opts = self.kwargs.copy()
        opts.update(kwargs)
        
        for k, v in opts.copy().items():
            try:
                pymongo.common.validate(k, v)
            except pymongo.errors.ConfigurationError as e:
                opts.pop(k)

        return pymongo.MongoClient(host=self.host, port=self.port, **opts)

    def infer_schema(self, doc: dict):
        schema = Schema()
        for field, value in doc.items():
            schema.add_field_by_attrs(field, self._infer_data_type(value))
        return schema

    def _infer_data_type(self, value):
        if isinstance(value, float):
            return types.FLOAT64
        if isinstance(value, int):
            return types.INT64
        if isinstance(value, (str, bson.ObjectId)):
            return types.STRING
        if isinstance(value, datetime.datetime):
            return types.DATETIME
        if isinstance(value, bool):
            return types.BOOLEAN

        if isinstance(value, (list, dict)):
            # 被 JSON 序列化
            return types.JSON

        # 其他类型都当作字符串
        return types.STRING

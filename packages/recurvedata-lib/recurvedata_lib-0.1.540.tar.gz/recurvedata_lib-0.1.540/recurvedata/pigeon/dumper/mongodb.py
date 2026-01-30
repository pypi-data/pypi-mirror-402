from bson import json_util

from recurvedata.pigeon.connector.mongodb import MongoDBConnector
from recurvedata.pigeon.dumper.base import BaseDumper
from recurvedata.pigeon.row_factory import ordered_dict_factory
from recurvedata.pigeon.schema import Schema
from recurvedata.pigeon.utils.timing import TimeCounter


class MongoDBDumper(BaseDumper):
    _row_factory = staticmethod(ordered_dict_factory)

    def __init__(self, connector, database, collection, filter=None, projection=None, handler_factories=None):
        """MongoDBDumper 用于从 MongoDB 导出数据
        :param connector: MongoDBConnector 对象
        :param database: database 名字
        :param collection: collection 名字
        :param filter: 查询条件，用于 find 函数。
                       注意，如果传入字符串格式的 filter，将被当作 json 字符串，用 bson.json_util.loads 反序列化。
        :param projection: 控制返回的字段，用于 find 函数
        :param handler_factories:
        """
        super().__init__(handler_factories=handler_factories)

        if not isinstance(connector, MongoDBConnector):
            raise TypeError("connector should be instance of MongoDBConnector")

        self.connector = connector
        self.database = database
        self.collection = collection

        self.filter = filter or {}
        if isinstance(self.filter, str):
            self.filter = json_util.loads(self.filter)

        self.projection = projection

        self.meta.context = {
            "database": database,
            "collection": collection,
            "filter": filter,
            "projection": projection,
        }

    @property
    def row_factory(self):
        return ordered_dict_factory

    @row_factory.setter
    def row_factory(self, factory):
        raise ValueError(f"{self.__class__.__name__}.row_factory is dict_factory, and is readonly")

    def execute(self):
        self.meta.mark_start()
        self.execute_impl()
        self.meta.mark_finish()
        self.logger.info("dumper meta: %s", self.meta.to_json(indent=2))
        self.handle_schema()
        return self.meta

    def execute_impl(self):
        handlers = self.create_handlers()

        self.logger.info("execute with context")
        self.logger.info("  filter: %s", self.filter)
        self.logger.info("  projection: %s", self.projection)

        # MongoDB 没有模式，以第一条结果的字段和值来推导 schema
        schema = Schema()
        field_names = []
        client = self.connector.connect()
        if self.collection not in client[self.database].list_collection_names():
            raise RuntimeError(f"collection '{self.collection}' does not exist")
        total_count = client[self.database][self.collection].count_documents(self.filter)
        cursor = client[self.database][self.collection].find(self.filter, self.projection)

        counter = TimeCounter(name="", log_threshold=10000, logger=self.logger, total=total_count)
        # Use projection field order as the base order
        field_names = list(self.projection.keys()) if self.projection else []

        for doc in cursor:
            counter.incr(1)

            fixed_doc = doc
            # if projection is not None, then use projection to filter the fields and fill the missing fields with None
            if field_names:
                # Use projection field order, and fill missing fields with None
                fixed_doc = self.row_factory(field_names, [doc.get(x, None) for x in field_names])

            for h in handlers:
                h.handle(fixed_doc)

        counter.show_stat()
        self.meta.schema = schema
        self.meta.num_dumped_rows = counter.count

        for hf, h in zip(self.handler_factories, handlers):
            hf.meta.update(h.meta)
        self.meta.handlers_meta = [x.meta for x in self.handler_factories]

        for h in handlers:
            h.close()
        self.join_handlers()

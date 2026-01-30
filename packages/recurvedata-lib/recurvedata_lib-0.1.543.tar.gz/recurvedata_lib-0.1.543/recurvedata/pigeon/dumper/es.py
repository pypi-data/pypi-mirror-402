from recurvedata.pigeon.connector.es import ElasticSearchConnector
from recurvedata.pigeon.dumper.base import BaseDumper
from recurvedata.pigeon.row_factory import ordered_dict_factory
from recurvedata.pigeon.utils import ensure_str_list, extract_dict


class ElasticSearchDumper(BaseDumper):
    _row_factory = staticmethod(ordered_dict_factory)

    def __init__(
        self,
        connector,
        index,
        query=None,
        doc_type=None,
        fields=None,
        meta_fields=None,
        search_kwargs=None,
        handler_factories=None,
    ):
        super().__init__(handler_factories=handler_factories)

        assert isinstance(connector, ElasticSearchConnector)
        self.es = connector

        self.index = index
        self.doc_type = doc_type
        self.query = query
        self.fields = ensure_str_list(fields) or None
        self.meta_fields = ensure_str_list(meta_fields) or None
        self.search_kwargs = search_kwargs or {}

        self.meta.context = {
            "index": self.index,
            "doc_type": self.doc_type,
            "query": self.query,
            "fields": self.fields,
            "meta_fields": self.meta_fields,
            "search_kwargs": self.search_kwargs,
        }
        self.meta.schema = self.get_result_schema()
        self.result_fields = self.meta.schema.field_names

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
        for i, h in enumerate(handlers):
            h.set_input_schema(self.meta.schema)
            self.logger.info("Handler #%s: %s", i, h)

        for hit in self.iter_result():
            doc = self.flat_hit(hit)

            # keep order && patch missing fields
            values = [doc.get(k) for k in self.result_fields]
            ordered_doc = self.row_factory(self.result_fields, values)
            for h in handlers:
                h.handle(ordered_doc)

        for hf, h in zip(self.handler_factories, handlers):
            hf.meta.update(h.meta)
        self.meta.handlers_meta = [x.meta for x in self.handler_factories]

        for h in handlers:
            h.close()
        self.join_handlers()

    def iter_result(self):
        res = self.es.scan(self.query, self.index, self.doc_type, self.fields, **self.search_kwargs)
        n = 0
        t = self.start_timer()
        for hit in res:
            yield hit
            n += 1
            if n % 20000 == 0:
                t.info("dumped %d rows", n)
        t.info("dumped %d rows in total", n)
        self.meta.num_dumped_rows = n

    def flat_hit(self, hit):
        rv = hit["_source"]
        if self.fields:
            rv = extract_dict(rv, self.fields)
        if self.meta_fields:
            rv.update(extract_dict(hit, self.meta_fields))

        return rv

    def get_result_schema(self):
        schema = self.es.get_schema(self.index, self.doc_type)
        if self.fields:
            schema.keep_fields(self.fields)

        if self.meta_fields:
            for name in self.meta_fields:
                schema.add_field_by_attrs(name, self.es.get_meta_field_type(name))
        return schema

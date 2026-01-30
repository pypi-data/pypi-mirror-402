import base64
import hashlib
import pickle
from collections import defaultdict

from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import NotFoundError

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.csv import CSV
from recurvedata.pigeon.schema import Schema, types
from recurvedata.pigeon.utils import LoggingMixin, ensure_str_list, replace_null_values

# https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html#_field_datatypes
_es_type_to_canonical_type = {
    "boolean": types.BOOLEAN,
    "byte": types.INT8,
    "short": types.INT16,
    "integer": types.INT32,
    "long": types.INT64,
    "half_float": types.FLOAT32,
    "float": types.FLOAT32,
    "double": types.FLOAT64,
    "scaled_float": types.FLOAT64,
    "date": types.DATETIME,
    "text": types.STRING,
    "keyword": types.STRING,
    "ip": types.STRING,
    "object": types.STRING,
    "nested": types.STRING,
}

_canonical_type_to_es_type = {
    types.BOOLEAN: "boolean",
    types.INT8: "byte",
    types.INT16: "short",
    types.INT32: "integer",
    types.INT64: "long",
    types.FLOAT32: "float",
    types.FLOAT64: "double",
    types.DATETIME: "date",
    types.STRING: "text",
}


@register_connector_class(["es", "elasticsearch"])
class ElasticSearchConnector(LoggingMixin):
    def __init__(self, host, **kwargs):
        self.host = host
        self._es = Elasticsearch(self.host, **kwargs)

    def scan(self, query=None, index=None, doc_type=None, fields=None, **search_kwargs):
        if isinstance(query, str):
            real_query = {"query": {"query_string": {"query": query}}}
        else:
            real_query = query

        search_kwargs = search_kwargs.copy()
        search_kwargs.update({"index": index, "doc_type": doc_type})
        if fields:
            search_kwargs["_source_include"] = fields
        return helpers.scan(self._es, query=real_query, **search_kwargs)

    def get_mapping(self, index, doc_type):
        try:
            result = self._es.indices.get_mapping(index=index, doc_type=doc_type)
        except NotFoundError as e:
            self.logger.error(str(e))
            return None

        mappings = list(result.values())[0]["mappings"]
        if doc_type is not None:
            properties = mappings[doc_type]["properties"]
        else:
            properties = list(mappings.values())[0]["properties"]
        return properties

    def get_schema(self, index, doc_type):
        mapping = self.get_mapping(index, doc_type)
        schema = Schema()
        for name, attrs in mapping.items():
            es_type = attrs.get("type", "text").lower()
            schema.add_field_by_attrs(name, self.to_canonical_type(es_type))
        return schema

    @staticmethod
    def get_meta_field_type(name):
        return {
            "_index": types.STRING,
            "_type": types.STRING,
            "_id": types.STRING,
            "_score": types.FLOAT64,
        }[name]

    @staticmethod
    def to_canonical_type(es_type):
        return _es_type_to_canonical_type.get(es_type, types.STRING)

    @staticmethod
    def from_canonical_type(canonical_type):
        return _canonical_type_to_es_type[canonical_type]

    def load_csv(
        self,
        filename,
        index,
        doc_type="_doc",
        schema=None,
        id_field=None,
        generate_id=False,
        null_values=("NULL", r"\N"),
        null_replacer=None,
        **csv_options,
    ):
        csv_proxy = CSV(filename, **csv_options)
        if not csv_proxy.has_header:
            raise ValueError(f"missing header in CSV file {filename}")

        # ensure id fields are present in header
        if id_field:
            fields = ensure_str_list(id_field)
            if not all(x in csv_proxy.header for x in fields):
                raise ValueError(f"{id_field} is invalid, only {csv_proxy.header} are support")
        else:
            fields = None

        if schema is not None:
            typed_fields = {x.name: x for x in schema.fields}
        else:
            typed_fields = {}

        def actions_generator():
            counters = defaultdict(int)
            with csv_proxy.reader(as_dict=True) as reader:
                for doc in reader:
                    doc = replace_null_values(doc, null_values, null_replacer)
                    doc = self.values_hook(doc, typed_fields)

                    action = {"_index": index, "_type": doc_type, "_source": doc}

                    if fields:
                        # fields = ensure_str_list(id_field)
                        if len(fields) == 1:
                            action["_id"] = doc[fields[0]]
                        else:
                            action["_id"] = self.encode_id([doc[x] for x in fields])
                    if generate_id:
                        action["_id"] = self.encode_id(doc.values())

                    counters["rows_read"] += 1
                    counters["rows_yield"] += 1
                    if counters["rows_yield"] % 10000 == 0:
                        self.logger.info("progress: %s", counters)

                    yield action

        # 消费生成器
        for _ in helpers.parallel_bulk(
            self._es, actions=actions_generator(), thread_count=8, chunk_size=1000, queue_size=8
        ):
            pass

    @staticmethod
    def encode_id(values):
        content = pickle.dumps(tuple(values))
        return base64.urlsafe_b64encode(hashlib.sha1(content).digest()).decode()

    @staticmethod
    def values_hook(doc: dict, typed_fields: dict):
        for k, v in doc.items():
            field = typed_fields.get(k)
            if field is None or field.type in [types.STRING]:
                continue

            doc[k] = typed_fields[k].cast(v)
        return doc

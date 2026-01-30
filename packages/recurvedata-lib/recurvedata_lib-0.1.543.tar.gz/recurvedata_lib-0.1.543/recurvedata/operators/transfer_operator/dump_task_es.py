import copy
import json

try:
    from recurvedata.pigeon.dumper.es import ElasticSearchDumper
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator import utils
from recurvedata.operators.transfer_operator.task import DumpTask
from recurvedata.utils import extract_dict


class ElasticSearchDumpTask(DumpTask):
    ds_name_fields = ("data_source_name",)
    worker_install_require = ["pigeon[elasticsearch]"]

    def execute_impl(self, *args, **kwargs):
        ds = self.must_get_connection_by_name(self.config["data_source_name"])
        hf = self.create_handler_factory()
        dump_options = extract_dict(self.rendered_config, keys=["index", "doc_type", "query", "fields", "meta_fields"])
        if self.rendered_config.get("search_kwargs"):
            search_kwargs = json.loads(self.rendered_config.get("search_kwargs"))
            dump_options["search_kwargs"] = search_kwargs
        dump_options.update({"connector": ds.connector, "handler_factories": [hf]})
        dumper = ElasticSearchDumper(**dump_options)
        return dumper.execute()

    @classmethod
    def config_schema(cls):
        # get_choices_by_type = cls.get_connection_names_by_type
        # dss = get_choices_by_type('elasticsearch')
        return {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": _l("Elasticsearch Data Source"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": [
                            "elasticsearch",
                        ],
                    },
                    # 'default': cls.first_or_default(dss, ''),
                },
                "index": {
                    "type": "string",
                    "title": _l("Elasticsearch Index"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "doc_type": {
                    "type": "string",
                    "title": _l("Document Type"),
                    "default": "_doc",
                    "description": _l("The type of documents to query"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "query": {
                    "type": "string",
                    "title": _l("Search Query"),
                    "default": "*",
                    "description": _l("Elasticsearch query string to filter documents. Supports Jinja templating."),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "fields": {
                    "type": "string",
                    "title": _l("Document Fields"),
                    "description": _l(
                        "Comma-separated list of document fields to retrieve. Leave empty to get all fields."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "meta_fields": {
                    "type": "array",
                    "uniqueItems": True,
                    "items": {
                        "type": "string",
                        "enum": ["_index", "_type", "_id"],
                        "enumNames": ["_index", "_type", "_id"],
                    },
                    "title": _l("Document Metadata Fields"),
                    "description": _l("Additional metadata fields to include with each document."),
                    "ui:widget": "SelectWidget",
                },
                "search_kwargs": {
                    "type": "string",
                    "title": _l("Advanced Search Options"),
                    "description": _l(
                        "Additional options for Elasticsearch scan operation in JSON format (e.g. size, scroll)."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "transform": copy.deepcopy(utils.TRANSFORM),
            },
            "required": ["data_source_name", "index"],
        }

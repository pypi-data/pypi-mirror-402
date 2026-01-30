try:
    from recurvedata.pigeon.loader.csv_to_es import CSVToElasticSearchLoader
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator.task import LoadTask
from recurvedata.utils import extract_dict


class ElasticSearchLoadTask(LoadTask):
    ds_name_fields = ("data_source_name",)
    ds_types = ("elasticsearch",)
    should_write_header = True
    worker_install_require = ["pigeon[elasticsearch]"]

    def execute_impl(self, *args, **kwargs):
        es_ds = self.must_get_connection_by_name(self.config["data_source_name"])
        load_options = extract_dict(self.rendered_config, keys=["index", "doc_type", "id_field", "generate_id"])
        load_options.update(
            {
                "connector": es_ds.connector,
                "filename": self.filename,
                "delete_file": True,
            }
        )
        loader = CSVToElasticSearchLoader(**load_options)
        return loader.execute()

    @classmethod
    def config_schema(cls):
        # get_choices_by_type = cls.get_connection_names_by_type
        # dss = get_choices_by_type(cls.ds_types)
        return {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": _l("Elasticsearch Data Source"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": cls.ds_types,
                    },
                    # 'default': cls.first_or_default(dss, ''),
                },
                "index": {
                    "type": "string",
                    "title": _l("Elasticsearch Index"),
                    "description": _l("Name of the Elasticsearch index to load data into"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "doc_type": {
                    "type": "string",
                    "title": _l("Document Type"),
                    "description": _l("Type of document to create in Elasticsearch"),
                    "default": "_doc",
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "id_field": {
                    "type": "string",
                    "title": _l("Document ID Field"),
                    "description": _l(
                        "Field from the input data to use as the document ID. Leave empty to auto-generate IDs"
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "generate_id": {
                    "type": "boolean",
                    "title": _l("Generate Document IDs"),
                    "description": _l(
                        "Automatically generate unique document IDs based on record content. Takes precedence over ID Field if both are specified"
                    ),
                    "default": False,
                },
            },
            "required": ["data_source_name", "index"],
        }

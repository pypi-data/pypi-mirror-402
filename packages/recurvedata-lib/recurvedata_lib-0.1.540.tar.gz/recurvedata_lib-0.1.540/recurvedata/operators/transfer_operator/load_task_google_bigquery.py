import copy

try:
    from recurvedata.pigeon.loader.csv_to_google_bigquery import CSVToGoogleBigqueryLoader
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator import utils
from recurvedata.operators.transfer_operator.task import LoadTask


class GoogleBigqueryLoadTask(LoadTask):
    ds_name_fields = ("google_bigquery_data_source_name",)
    ds_types = ("bigquery",)
    default_dumper_handler_options = {}
    worker_install_require = ["pigeon[google_bigquery]"]

    def execute_impl(self, *args, **kwargs):
        google_bigquery_ds = self.must_get_connection_by_name(self.config["google_bigquery_data_source_name"])
        load_options = self.rendered_config.copy()
        for k in ["google_bigquery_data_source_name"]:
            load_options.pop(k, None)
        load_options.update(
            {
                "filename": self.filename,
                "google_bigquery_connector": google_bigquery_ds.connector,
                "delete_file": True,
                "dataset": google_bigquery_ds.data.get("database"),
            }
        )
        loader = CSVToGoogleBigqueryLoader(**load_options)
        return loader.execute()

    @classmethod
    def config_schema(cls):
        # get_choices_by_type = cls.get_connection_names_by_type
        # dws = get_choices_by_type(cls.ds_types)
        schema = {
            "type": "object",
            "properties": {
                "google_bigquery_data_source_name": {
                    "type": "string",
                    "title": _l("BigQuery Connection"),
                    "description": _l("Select the BigQuery connection to use"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": cls.ds_types,
                    },
                    # 'default': cls.first_or_default(dws, ''),
                },
                # "dataset": {
                #     "type": "string",
                #     "title": "Dataset",
                #     "ui:field": "CodeEditorWithReferencesField",
                #     "ui:options": {
                #         "type": "plain",
                #     },
                # },
                "table": {
                    "type": "string",
                    "title": _l("Target Table"),
                    "description": _l("Name of the table to load data into"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "create_table_ddl": {
                    "type": "string",
                    "title": _l("Table Creation SQL"),
                    "description": _l("SQL statement to create the destination table if it doesn't exist"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "sql",
                        "sqlLang": "sql",
                    },
                },
            },
            "required": ["google_bigquery_data_source_name", "table", "mode"],
        }
        properties_schema = schema["properties"]
        properties_schema.update(copy.deepcopy(utils.LOAD_COMMON))

        # remove dedup
        properties_schema.pop("dedup", None)
        properties_schema.pop("dedup_uniq_keys", None)
        properties_schema.pop("dedup_orderby", None)
        return schema

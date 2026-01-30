import copy

try:
    from recurvedata.pigeon.loader.csv_to_redshift import CSVToRedshiftLoader
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator import utils
from recurvedata.operators.transfer_operator.task import LoadTask


class RedshiftLoadTask(LoadTask):
    ds_name_fields = ("redshift_data_source_name",)
    ds_types = ("redshift",)
    worker_install_require = ["pigeon[redshift]"]

    def execute_impl(self, *args, **kwargs):
        redshift_ds = self.must_get_connection_by_name(self.config["redshift_data_source_name"])

        load_options = self.rendered_config.copy()
        for k in ["redshift_data_source_name"]:
            load_options.pop(k, None)

        load_options.update(
            {
                "filename": self.filename,
                "redshift_connector": redshift_ds.connector,
                "delete_file": True,
                "database": redshift_ds.database,
                "schema": redshift_ds.data.get("schema"),
            }
        )
        loader = CSVToRedshiftLoader(**load_options)
        return loader.execute()

    @classmethod
    def config_schema(cls):
        # get_choices_by_type = cls.get_connection_names_by_type
        # dss = get_choices_by_type(cls.ds_types)
        schema = {
            "type": "object",
            "properties": {
                "redshift_data_source_name": {
                    "type": "string",
                    "title": _l("Redshift Connection"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": cls.ds_types,
                    },
                    # 'default': cls.first_or_default(dss, ''),
                },
                # "database": {
                #     "type": "string",
                #     "title": "Database",
                #     "ui:field": "CodeEditorWithReferencesField",
                #     "ui:options": {
                #         "type": "plain",
                #     },
                # },
                # "schema": {
                #     "type": "string",
                #     "title": "Schema",
                #     "default": "public",
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
                    "description": _l("SQL statement to create the target table if it doesn't exist"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "sql",
                        "sqlLang": "redshift",
                    },
                },
            },
            "required": ["redshift_data_source_name", "table", "mode"],
        }
        properties_schema = schema["properties"]
        properties_schema.update(copy.deepcopy(utils.LOAD_COMMON))
        return schema

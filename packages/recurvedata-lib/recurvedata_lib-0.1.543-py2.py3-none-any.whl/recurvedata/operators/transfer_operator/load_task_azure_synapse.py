import copy

try:
    from recurvedata.pigeon.loader.csv_to_azure_synapse import CSVToAzureSynapseLoader
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator import utils
from recurvedata.operators.transfer_operator.task import LoadTask


class AzureSynapseLoadTask(LoadTask):
    ds_name_fields = ("azure_synapse_data_source_name",)
    ds_types = ("azure_synapse",)
    default_dumper_handler_options = {}
    worker_install_require = ["pigeon"]

    def execute_impl(self, *args, **kwargs):
        azure_synapse_ds = self.must_get_connection_by_name(self.config["azure_synapse_data_source_name"])
        load_options = self.rendered_config.copy()
        for k in ["azure_synapse_data_source_name"]:
            load_options.pop(k, None)
        load_options.update(
            {
                "filename": self.filename,
                "azure_synapse_connector": azure_synapse_ds.connector,
                "delete_file": True,
                "compress": True,
            }
        )
        loader = CSVToAzureSynapseLoader(**load_options)
        return loader.execute()

    @classmethod
    def config_schema(cls):
        # get_choices_by_type = cls.get_connection_names_by_type
        # dws = get_choices_by_type(cls.ds_types)
        schema = {
            "type": "object",
            "properties": {
                "azure_synapse_data_source_name": {
                    "type": "string",
                    "title": _l("Azure Synapse Connection"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": cls.ds_types,
                    },
                    # 'default': cls.first_or_default(dws, ''),
                },
                "schema": {
                    "type": "string",
                    "title": _l("Database Schema"),
                    "description": _l("Schema name in Azure Synapse database"),
                    "default": "dbo",
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
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
                    "description": _l(
                        "SQL statement to create the target table if it doesn't exist. See "
                        "<a target='_blank' href='https://learn.microsoft.com/en-us/sql/t-sql/statements/create-table-azure-sql-data-warehouse'>"
                        "Azure Synapse Docs</a> for syntax."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "sql",
                        "sqlLang": "sql",
                    },
                },
            },
            "required": ["azure_synapse_data_source_name", "table", "mode"],
        }
        properties_schema = schema["properties"]
        properties_schema.update(copy.deepcopy(utils.LOAD_COMMON))
        return schema

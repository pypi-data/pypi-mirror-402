import logging
from typing import Any

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator import const
from recurvedata.operators.transfer_operator.task import LoadTask
from recurvedata.operators.transfer_operator.utils import allowed_modes

try:
    from recurvedata.pigeon.loader.csv_to_microsoft_fabric import CSVToMsFabricLoader
except ImportError:
    pass

logger = logging.getLogger(__name__)


class MicrosoftFabricLoadTask(LoadTask):
    ds_name_fields = ("data_source_name",)
    ds_types = ("microsoft_fabric",)
    worker_install_require = ["pigeon[azure]"]

    def execute_impl(self, *args: Any, **kwargs: Any) -> None:
        ds = self.must_get_connection_by_name(self.config["data_source_name"])
        load_options: dict[str, Any] = self.rendered_config.copy()
        for k in ["data_source_name"]:
            load_options.pop(k, None)
        columns = load_options.get("columns", "")
        columns = [x.strip() for x in columns.split(",")] if columns.strip(" ,") else []
        load_options["lineterminator"] = "\r\n" if self.dump_task_type == "PythonDumpTask" else "0x0D0A"
        load_options.update(
            {
                "filename": self.filename,
                "connector": ds.connector,
                "delete_file": True,
                "using_insert": False,
                "columns": columns,
                "database": ds.database,
                "schema": ds.data.get("schema"),
                "compress": True,  # Enable compression for better performance
                "blob_options": ds.data.get("blob_options", {}),
            }
        )
        logger.info(load_options)
        loader = CSVToMsFabricLoader(**load_options)
        return loader.execute()

    @classmethod
    def config_schema(cls):
        schema = {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": _l("Microsoft Fabric Connection"),
                    "description": _l("The Microsoft Fabric data source to load data into"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": cls.ds_types,
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
                    "description": _l("SQL statement to create the target table if it doesn't exist"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "sql",
                        "sqlLang": "sql",
                    },
                },
                "mode": {
                    "type": "string",
                    "title": _l("Load Mode"),
                    "description": _l("How to handle existing data in the target table"),
                    "enum": list(allowed_modes),
                    "enumNames": list(allowed_modes),
                    "default": const.LOAD_OVERWRITE,
                },
                "primary_keys": {
                    "ui:hidden": '{{parentFormData.mode !== "MERGE"}}',
                    "type": "string",
                    "title": _l("Primary Keys"),
                    "description": _l(
                        "Comma-separated list of columns used for deduplication in MERGE mode. "
                        "Should be primary or unique key columns."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
            },
            "required": ["data_source_name", "table"],
        }
        return schema

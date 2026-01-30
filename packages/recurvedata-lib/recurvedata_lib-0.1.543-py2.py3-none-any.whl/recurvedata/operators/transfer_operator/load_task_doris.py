try:
    from recurvedata.pigeon.loader.csv_to_doris import CSVToDorisLoader
except ImportError:
    pass

from typing import TYPE_CHECKING, Any, List, Tuple

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator import const
from recurvedata.operators.transfer_operator.task import LoadTask
from recurvedata.operators.transfer_operator.utils import allowed_modes

if TYPE_CHECKING:
    from recurvedata.connectors.pigeon import DataSource


class DorisLoadTask(LoadTask):
    ds_name_fields: Tuple[str] = ("data_source_name",)
    ds_types: Tuple[str] = ("doris",)
    default_dumper_handler_options = {
        "null": r"\N",
        "lineterminator": "\n",
        "escapechar": "'",
        "doublequote": False,
    }
    worker_install_require: List[str] = [
        "pigeon[doris]",
    ]

    def execute_impl(self, *args, **kwargs) -> Any:
        """Execute the Doris load task by loading CSV data into a Doris table."""
        # Get the Doris data source connection
        ds: "DataSource" = self.must_get_connection_by_name(self.config["data_source_name"])

        # Copy and prepare the load options
        load_options: dict = self.rendered_config.copy()
        load_options.pop("data_source_name", None)

        # Update with required loader options
        load_options.update(
            {
                "filename": self.filename,
                "connector": ds.connector,
                "delete_file": True,  # Clean up CSV file after loading
                "load_strict_mode": self.config.get("load_strict_mode", False),
                "max_filter_ratio": self.config.get("max_filter_ratio", 0),
                "database": ds.database,
            }
        )

        # Initialize and execute the loader
        loader = CSVToDorisLoader(**load_options)
        return loader.execute()

    @classmethod
    def config_schema(cls) -> dict[str, Any]:
        schema = {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": _l("Doris Connection"),
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
                    "description": _l(
                        "SQL statement to create the target table if it doesn't exist. See "
                        "<a target='_blank' href='https://doris.apache.org/docs/sql-manual/sql-statements/table-and-view/table/CREATE-TABLE'>"
                        "Doris Docs</a> for syntax."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "sql",
                        "sqlLang": "mysql",
                    },
                },
                "mode": {
                    "type": "string",
                    "title": _l("Load Mode"),
                    "description": _l("How to handle existing data in the target table"),
                    "enum": list(allowed_modes),
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
                "using_insert": {
                    "type": "boolean",
                    "title": _l("Use INSERT Mode"),
                    "description": _l("By default Stream Load is used. Enable to use INSERT statements instead."),
                    "default": False,
                    "ui:hidden": True,
                },
                "load_strict_mode": {
                    "type": "boolean",
                    "title": _l("Enable Strict Mode"),
                    "default": False,
                    "description": _l(
                        "When enabled, validates that data matches target table schema before loading. "
                        "Raises error if validation fails."
                    ),
                    "ui:hidden": "{{parentFormData.using_insert}}",
                },
                "insert_batch_size": {
                    "ui:hidden": "{{!parentFormData.using_insert}}",
                    "type": "number",
                    "ui:options": {"controls": False},
                    "title": _l("Batch Size"),
                    "default": 500,
                    "minimum": 1,
                    "maximum": 2000,
                    "description": _l("Number of rows to insert in each batch"),
                },
                "insert_concurrency": {
                    "ui:hidden": "{{!parentFormData.using_insert}}",
                    "type": "number",
                    "ui:options": {"controls": False},
                    "title": _l("Concurrent Inserts"),
                    "default": 1,
                    "minimum": 1,
                    "maximum": 10,
                    "description": _l("Number of parallel insert operations"),
                },
                "max_filter_ratio": {
                    "type": "number",
                    "ui:options": {"controls": False},
                    "title": _l("Max Filter Ratio"),
                    "default": 0,
                    "minimum": 0,
                    "maximum": 1,
                    "description": _l(
                        "The maximum tolerated ratio of filterable (e.g., non-compliant) data. Default is zero tolerance. Value range: 0~1. If the error rate during import exceeds this value, the import will fail."
                    ),
                    "ui:hidden": "{{parentFormData.using_insert}}",
                },
            },
            "required": ["data_source_name", "table"],
        }
        return schema

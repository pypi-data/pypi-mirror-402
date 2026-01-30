try:
    from recurvedata.pigeon.loader.csv_to_starrocks import CSVToStarRocksLoader
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator import const
from recurvedata.operators.transfer_operator.task import LoadTask
from recurvedata.operators.transfer_operator.utils import allowed_modes


class StarRocksLoadTask(LoadTask):
    ds_name_fields = ("data_source_name",)
    ds_types = ("starrocks",)
    default_dumper_handler_options = {
        "null": r"\N",
        "lineterminator": "\n",
        "escapechar": "'",
        "doublequote": False,
    }
    worker_install_require = [
        "pigeon[starrocks]",
    ]

    def execute_impl(self, *args, **kwargs):
        ds = self.must_get_connection_by_name(self.config["data_source_name"])
        load_options = self.rendered_config.copy()
        for k in ["data_source_name"]:
            load_options.pop(k, None)
        load_options.update(
            {
                "filename": self.filename,
                "connector": ds.connector,
                "delete_file": True,
                "load_strict_mode": self.config.get("load_strict_mode", False),
                "database": ds.database,
            }
        )
        loader = CSVToStarRocksLoader(**load_options)
        return loader.execute()

    @classmethod
    def config_schema(cls):
        schema = {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": _l("StarRocks Connection"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": cls.ds_types,
                    },
                },
                # "database": {
                #     "type": "string",
                #     "title": "Database",
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
                    "description": _l(
                        "SQL statement to create the target table if it doesn't exist. See "
                        "<a target='_blank' href='https://docs.starrocks.io/docs/sql-reference/sql-statements/table_bucket_part_index/CREATE_TABLE'>"
                        "StarRocks Docs</a> for details"
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
                # "pre_queries": {
                #     "type": "string",
                #     "title": "Queries Ran Before Loading",
                #     "description": '新数据导入前运行的 SQL，多条 SQL 用 `;` 分隔；支持传入变量，详见 <a target="_blank" href="http://bit.ly/2JMutjn">文档</a>',
                #     "ui:field": "CodeEditorWithReferencesField",
                #     "ui:options": {
                #         "type": "code",
                #         "lang": "sql",
                #         "sqlLang": "mysql",
                #     },
                # },
                # "post_queries": {
                #     "type": "string",
                #     "title": "Queries Ran After Loading",
                #     "description": '新数据导入后运行的 SQL，多条 SQL 用 `;` 分隔；支持传入变量，详见 <a target="_blank" href="http://bit.ly/2JMutjn">文档</a>',
                #     "ui:field": "CodeEditorWithReferencesField",
                #     "ui:options": {
                #         "type": "code",
                #         "lang": "sql",
                #         "sqlLang": "mysql",
                #     },
                # },
            },
            "required": ["data_source_name", "table"],
        }
        return schema

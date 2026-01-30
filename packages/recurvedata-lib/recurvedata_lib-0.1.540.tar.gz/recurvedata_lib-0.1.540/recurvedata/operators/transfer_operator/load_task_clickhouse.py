import csv

try:
    from recurvedata.pigeon.loader.csv_to_clickhouse import CSVToClickHouseLoader
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator import const
from recurvedata.operators.transfer_operator.task import LoadTask
from recurvedata.operators.transfer_operator.utils import allowed_modes


class ClickHouseLoadTask(LoadTask):
    ds_name_fields = ("data_source_name",)
    ds_types = ("clickhouse",)
    default_dumper_handler_options = {
        "null": r"\N",
        "quoting": csv.QUOTE_MINIMAL,
    }
    worker_install_require = ["pigeon[clickhouse]"]

    def execute_impl(self, *args, **kwargs):
        ds = self.must_get_connection_by_name(self.config["data_source_name"])
        load_options = self.rendered_config.copy()
        for k in ["data_source_name"]:
            load_options.pop(k, None)
        load_options.update({"filename": self.filename, "connector": ds.connector, "delete_file": True})
        loader = CSVToClickHouseLoader(**load_options)
        return loader.execute()

    @classmethod
    def config_schema(cls):
        # get_choices_by_type = cls.get_connection_names_by_type
        # dss = get_choices_by_type(cls.ds_types)
        schema = {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": _l("ClickHouse Connection"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": cls.ds_types,
                    },
                    # 'default': cls.first_or_default(dss, ''),
                },
                "database": {
                    "type": "string",
                    "title": _l("Target Database"),
                    "description": _l("Name of the database to load data into"),
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
                        "<a target='_blank' href='https://clickhouse.com/docs/en/sql-reference/statements/create/table'>"
                        "ClickHouse Docs</a> for syntax."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "sql",
                        "sqlLang": "sql",
                    },
                },
                "table_engine": {
                    "type": "string",
                    "title": _l("Table Engine"),
                    "description": _l(
                        "Storage engine for the target table. Ignored if Table Creation SQL is provided. See "
                        "<a target='_blank' href='https://clickhouse.com/docs/en/engines/table-engines'>"
                        "ClickHouse Docs</a> for options."
                    ),
                    "default": "Log",
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
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
                # "using_insert": {
                #     "type": "boolean",
                #     "title": "Using INSERT",
                #     "default": False,
                #     "description": "默认使用 `clickhouse-client` 导入数据，出错时会回退到用 INSERT 语句批量导入数据",
                # },
                "insert_batch_size": {
                    # "ui:hidden": "{{!parentFormData.using_insert}}",
                    "type": "number",
                    "ui:options": {"controls": False},
                    "title": _l("Batch Size"),
                    "description": _l("Number of rows to insert in each batch"),
                    "default": 10000,
                    "minimum": 1000,
                    "maximum": 100000,
                },
                "insert_concurrency": {
                    # "ui:hidden": "{{!parentFormData.using_insert}}",
                    "type": "number",
                    "ui:options": {"controls": False},
                    "title": _l("Concurrent Inserts"),
                    "default": 1,
                    "minimum": 1,
                    "maximum": 5,
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
                #         "sqlLang": "sql",
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
                #         "sqlLang": "sql",
                #     },
                # },
            },
            "required": ["data_source_name", "database", "table", "insert_batch_size"],
        }
        return schema

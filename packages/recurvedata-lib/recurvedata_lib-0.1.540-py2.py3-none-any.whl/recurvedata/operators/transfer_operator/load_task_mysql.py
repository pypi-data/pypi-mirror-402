try:
    from recurvedata.pigeon.loader.csv_to_mysql import CSVToMySQLLoader
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator import const
from recurvedata.operators.transfer_operator.task import LoadTask
from recurvedata.operators.transfer_operator.utils import allowed_modes


class MySQLLoadTask(LoadTask):
    ds_name_fields = ("mysql_data_source_name",)
    ds_types = ("mysql", "tidb")
    worker_install_require = [
        "pigeon[mysql]",
    ]
    default_dumper_handler_options = {
        "null": r"\N",
    }

    def execute_impl(self, *args, **kwargs):
        mysql_ds = self.must_get_connection_by_name(self.config["mysql_data_source_name"])
        load_options = self.rendered_config.copy()
        for k in ["mysql_data_source_name"]:
            load_options.pop(k, None)
        load_options.update(
            {
                "filename": self.filename,
                "connector": mysql_ds.connector,
                "delete_file": True,
                "database": mysql_ds.database,
            }
        )
        loader = CSVToMySQLLoader(**load_options)
        return loader.execute()

    @classmethod
    def config_schema(cls):
        # get_choices_by_type = cls.get_connection_names_by_type
        # dss = get_choices_by_type(cls.ds_types)

        schema = {
            "type": "object",
            "properties": {
                "mysql_data_source_name": {
                    "type": "string",
                    "title": _l("MySQL Connection"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": cls.ds_types,
                    },
                    # 'default': cls.first_or_default(dss),
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
                    "description": _l("SQL statement to create the target table if it doesn't exist"),
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
                    "title": _l("Use INSERT Statements"),
                    "default": False,
                    "description": _l(
                        "If disabled (default), uses fast bulk loading via `LOAD DATA LOCAL INFILE`. "
                        "If enabled, uses standard `INSERT` statements instead."
                    ),
                },
                "insert_batch_size": {
                    "ui:hidden": "{{!parentFormData.using_insert}}",
                    "type": "number",
                    "ui:options": {"controls": False},
                    "title": _l("Batch Size"),
                    "default": 1000,
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
            "required": ["mysql_data_source_name", "table"],
        }
        return schema

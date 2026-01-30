import logging

try:
    from recurvedata.pigeon.loader.csv_to_mssql import CSVToMsSQLLoader
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator import const
from recurvedata.operators.transfer_operator.task import LoadTask
from recurvedata.operators.transfer_operator.utils import allowed_modes

logger = logging.getLogger(__name__)


class MsSQLLoadTask(LoadTask):
    ds_name_fields = ("data_source_name",)
    ds_types = ("mssql", "azure_mssql")
    worker_install_require = ["pigeon[azure]"]

    def execute_impl(self, *args, **kwargs):
        ds = self.must_get_connection_by_name(self.config["data_source_name"])
        load_options = self.rendered_config.copy()
        for k in ["data_source_name"]:
            load_options.pop(k, None)
        columns = load_options.get("columns", "")
        columns = [x.strip() for x in columns.split(",")] if columns.strip(" ,") else []
        load_options.update(
            {
                "filename": self.filename,
                "connector": ds.connector,
                "delete_file": True,
                "using_insert": False,  # 自动推导，优先使用批量加载文件
                "columns": columns,
                "database": ds.database,
                "schema": ds.data.get("schema"),
            }
        )
        logger.info(load_options)
        loader = CSVToMsSQLLoader(**load_options)
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
                    "title": _l("MSSQL Connection"),
                    "description": _l("The MSSQL data source to load data into"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": cls.ds_types,
                    },
                },
                # "database": {
                #     "type": "string",
                #     "title": _l("Target Database"),
                #     "description": _l("Name of the database to load data into"),
                #     "ui:field": "CodeEditorWithReferencesField",
                #     "ui:options": {
                #         "type": "plain",
                #     },
                # },
                # "schema": {
                #     "type": "string",
                #     "title": _l("Database Schema"),
                #     "description": _l("Schema name in the target database (default: dbo)"),
                #     "default": "dbo",
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
                # 'insert_batch_size': {
                #     'type': 'number',
                #      "ui:options": {"controls": False},
                #     'title': 'INSERT Batch Size',
                #     'default': 500,
                #     'minimum': 1,
                #     'maximum': 2000,
                #     'description': '如果不支持批量加载 INSERT 导入数据，该参数设定 batch 大小'
                # }
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
            "required": ["data_source_name", "table"],
        }
        return schema

import copy

try:
    from recurvedata.pigeon.loader.csv_to_postgresql import CSVToPostgresqlLoader
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator import utils
from recurvedata.operators.transfer_operator.task import LoadTask


class PostgresqlLoadTask(LoadTask):
    ds_name_fields = ("data_source_name",)
    ds_types = ("postgres",)
    worker_install_require = ["pigeon[postgres]"]

    def execute_impl(self, *args, **kwargs):
        ds = self.must_get_connection_by_name(self.config["data_source_name"])
        load_options = self.rendered_config.copy()
        for k in ["data_source_name"]:
            load_options.pop(k, None)
        load_options.setdefault("database", ds.database)
        load_options.update(
            {
                "filename": self.filename,
                "connector": ds.connector,
                "delete_file": True,
                "database": ds.database,
                "schema": ds.data.get("schema"),
            }
        )
        loader = CSVToPostgresqlLoader(**load_options)
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
                    "title": _l("PostgreSQL Connection"),
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
                    "title": _l("Create Table DDL"),
                    "description": _l("SQL statement to create the target table if it doesn't exist"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "sql",
                        "sqlLang": "postgresql",
                    },
                },
                # 'using_insert': {
                #     'type': 'boolean',
                #     'title': 'Using INSERT',
                #     'default': False,
                #     'description': '默认使用 `LOAD DATA LOCAL INFILE` 导入数据，也可以选择使用 INSERT 语句'
                # },
                "insert_batch_size": {
                    "type": "number",
                    "ui:options": {"controls": False},
                    "title": _l("Batch Size"),
                    "default": 1000,
                    "minimum": 1,
                    "maximum": 20000,
                    "description": _l("Number of rows inserted in each batch"),
                },
                "insert_concurrency": {
                    "type": "number",
                    "ui:options": {"controls": False},
                    "title": _l("Concurrent Inserts"),
                    "default": 1,
                    "minimum": 1,
                    "maximum": 20,
                    "description": _l("Number of parallel insert operations"),
                },
            },
            "required": ["data_source_name", "table"],
        }
        schema["properties"].update(copy.deepcopy(utils.LOAD_COMMON))
        return schema

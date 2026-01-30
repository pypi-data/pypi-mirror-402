import copy
import glob
import json
import os

try:
    from recurvedata.pigeon.loader.csv_to_hive import CSVToHiveLoader
    from recurvedata.pigeon.utils import fs
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator import utils
from recurvedata.operators.transfer_operator.task import LoadTask


class HiveLoadTask(LoadTask):
    ds_name_fields = ("hive_data_source_name",)
    ds_types = ("hive",)
    default_dumper_handler_options = {
        "hive": True,
        "merge_files": False,  # do not merge intermediate files, pass in file pattern
    }
    worker_install_require = ["pigeon[hive_impala]"]

    def execute_impl(self, *args, **kwargs):
        hive_ds = self.must_get_connection_by_name(self.config["hive_data_source_name"])

        load_options = self.rendered_config.copy()
        for k in ["hive_data_source_name", "impala_data_source_name"]:
            load_options.pop(k, None)

        partition = load_options.pop("partition", None)
        if partition:
            load_options["partition"] = json.loads(partition)

        sub_files = glob.glob(f"{self.filename}.[0-9]*")
        if os.path.exists(self.filename) and not sub_files:
            # dumper merged file
            filename = self.filename
        else:
            # dump without merging, use pattern
            # if upstream dump result is empty, sub_files is empty array, force to [self.filename] to ensure array is not empty
            if all([fs.is_file_empty(x) for x in sub_files]):
                sub_files = [self.filename]
            filename = sub_files

        load_options.update(
            {
                "filename": filename,
                "hive_connector": hive_ds.connector,
                "delete_file": True,
            }
        )
        impala_ds = self.get_connection_by_name(self.config["impala_data_source_name"])
        if impala_ds:
            load_options.update({"impala_connector": impala_ds.connector})
        loader = CSVToHiveLoader(**load_options)
        return loader.execute()

    @classmethod
    def config_schema(cls):
        # hive_dss = cls.get_connection_names_by_type(cls.ds_types)
        # impala_dss = cls.get_connection_names_by_type('impala')
        schema = {
            "type": "object",
            "properties": {
                "hive_data_source_name": {
                    "type": "string",
                    "title": _l("Hive Connection"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": cls.ds_types,
                    },
                    # 'default': cls.first_or_default(hive_dss, ''),
                },
                "impala_data_source_name": {
                    "type": "string",
                    "title": _l("Impala Connection"),
                    "description": _l("Optional Impala connection for faster data loading"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": [
                            "impala",
                        ],
                    },
                    # 'default': cls.first_or_default(impala_dss, ''),
                },
                "database": {
                    "type": "string",
                    "title": _l("Database Name"),
                    "description": _l("Name of the Hive database to load data into. Supports template variables."),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "table": {
                    "type": "string",
                    "title": _l("Table Name"),
                    "description": _l("Name of the Hive table to load data into. Supports template variables."),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "create_table_ddl": {
                    "type": "string",
                    "title": _l("Table Creation SQL"),
                    "description": _l(
                        "SQL statement to create the table if it doesn't exist. "
                        "PARQUET storage format is recommended for better performance. "
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "sql",
                        "sqlLang": "hive",
                    },
                },
                "partition": {
                    "type": "string",
                    "title": _l("Partition Specification"),
                    "description": _l(
                        "JSON object specifying the partition to load data into. "
                        "For T+1 tasks, use {'dt': '{{ yesterday_dt }}'} to load yesterday's partition. "
                        "Supports template variables."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "compression_codec": {
                    "type": "string",
                    "title": _l("Compression Method"),
                    "enum": ["snappy", "none", "gzip"],
                    "enumNames": ["snappy", "none", "gzip"],
                    "description": _l(
                        "Data compression format. 'none' for no compression, 'gzip' for maximum compression, "
                        "'snappy' for balanced compression/performance."
                    ),
                    "default": "snappy",
                },
            },
            # NOTE: frontend uses vue-json-schema, which has a bug where enum fields must be required...
            "required": [
                "hive_data_source_name",
                "impala_data_source_name",
                "database",
                "table",
                "mode",
                "compression_codec",
            ],
        }
        properties_schema = schema["properties"]
        properties_schema.update(copy.deepcopy(utils.LOAD_COMMON))
        return schema

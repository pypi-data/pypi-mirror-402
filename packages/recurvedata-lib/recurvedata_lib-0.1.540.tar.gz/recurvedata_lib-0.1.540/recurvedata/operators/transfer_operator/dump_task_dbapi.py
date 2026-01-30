import copy

import jsonschema

from recurvedata.connectors.service import list_sql_operator_types
from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator import utils
from recurvedata.operators.transfer_operator.task import DumpTask
from recurvedata.pigeon.dumper.dbapi import DBAPIDumper
from recurvedata.pigeon.row_factory import ordered_dict_factory
from recurvedata.pigeon.utils.sql import apply_where_safely
from recurvedata.utils import date_time, extract_dict


class DBAPIDumpTask(DumpTask):
    ds_name_fields = ("data_source_name",)
    worker_install_require = ["pigeon"]

    @property
    def time_column_tz(self):
        return self.config.get("time_column_tz", "UTC")

    def determine_time_range(self):
        start_date, end_date = self.get_schedule_time_range()
        if self.config.time_column_type == "date":
            return start_date.date(), end_date.date()

        # convert timezone
        start_date = date_time.astimezone(start_date, tz=self.time_column_tz)
        end_date = date_time.astimezone(end_date, tz=self.time_column_tz)

        return start_date.replace(tzinfo=None), end_date.replace(tzinfo=None)

    def derive_sql_query(self, connector, base_query: str):
        base_query = base_query.strip().rstrip(";")
        comment = self.get_query_comment_conf()
        if not self.config.incremental_by_time or self.dag.is_once:
            annotated_query = connector.add_leading_comment(base_query, comment)
            return annotated_query

        if not base_query:
            base_query = f"SELECT * FROM {connector.quote_identifier(self.config.table)}"
        annotated_query = connector.add_leading_comment(base_query, comment)

        start, end = self.determine_time_range()
        col = connector.quote_identifier(self.config.time_column)

        if connector.is_phoenix():
            where = f"{col} >= TIMESTAMP '{start}' AND {col} < TIMESTAMP '{end}'"
        else:
            where = f"{col} >= '{start}' AND {col} < '{end}'"
        return apply_where_safely(annotated_query, where)

    def execute_impl(self, *args, **kwargs):
        ds = self.must_get_connection_by_name(self.config["data_source_name"])
        hf = self.create_handler_factory()
        dump_options = extract_dict(self.rendered_config, keys=["table", "splitby", "splits", "concurrency"])
        dump_options.update(
            {
                "connector": ds.connector,
                "sql": self.derive_sql_query(ds.connector, self.rendered_config.get("sql", "")),
                "handler_factories": [hf],
            }
        )
        if not dump_options.get("splitby"):
            dump_options["splits"] = dump_options["concurrency"] = 1
        dumper = DBAPIDumper(**dump_options)
        dumper.row_factory = ordered_dict_factory
        return dumper.execute()

    @classmethod
    def validate(cls, configuration):
        conf = super().validate(configuration)
        if not (conf.get("table") or conf.get("sql")):
            raise jsonschema.ValidationError(message="either table or sql is required", path=("table", "sql"))
        return conf

    @classmethod
    def config_schema(cls):
        return {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": _l("Data Source"),
                    "description": _l("Database connection to extract data from"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": list_sql_operator_types(),
                    },
                },
                "table": {
                    "type": "string",
                    "title": _l("Source Table"),
                    "description": _l(
                        "Table name including schema (if required). Either specify a table name or SQL query."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "sql": {
                    "type": "string",
                    "title": _l("Custom Query"),
                    "description": _l(
                        "Custom SELECT query with Jinja template support. Takes precedence over table name if both are specified."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "sql",
                        "sqlLang": "sql",
                    },
                },
                "splitby": {
                    "type": "string",
                    "title": _l("Split Column"),
                    "description": _l(
                        "Column to partition data by for parallel processing. Must be indexed, sortable and non-null."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "splits": {
                    "ui:hidden": "{{ !parentFormData.splitby }}",
                    "type": "number",
                    "ui:options": {"controls": False},
                    "title": _l("Number of Splits"),
                    "default": 1,
                    "minimum": 1,
                    "maximum": 2000,
                },
                "concurrency": {
                    "ui:hidden": "{{ !parentFormData.splitby }}",
                    "type": "number",
                    "ui:options": {"controls": False},
                    "title": _l("Parallel Threads"),
                    "default": 1,
                    "description": _l("Number of concurrent extraction threads (1-20)"),
                    "minimum": 1,
                    "maximum": 20,
                },
                "transform": copy.deepcopy(utils.TRANSFORM),
                "incremental_by_time": {
                    "type": "boolean",
                    "title": _l("Enable Time-based Incremental Sync"),
                    "default": False,
                    "description": _l("Sync data incrementally based on a time column"),
                    "ui:widget": "BaseCheckbox",
                    "ui:options": {
                        "label": _l("Enable Time-based Incremental Sync"),
                    },
                },
                "time_column": {
                    "ui:hidden": "{{!parentFormData.incremental_by_time}}",
                    "type": "string",
                    "title": _l("Time Column Name"),
                    "default": "snapshot_time",
                    "description": _l(
                        "Name of the time column used for incremental sync. Column should be indexed for better performance."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "time_column_tz": {
                    "ui:hidden": "{{!parentFormData.incremental_by_time}}",
                    "type": "string",
                    "title": _l("Time Column Timezone"),
                    "default": "UTC",
                    "enum": [
                        "UTC",
                        "Asia/Shanghai",
                    ],
                    "enumNames": [
                        "UTC",
                        "Asia/Shanghai",
                    ],
                },
                "time_column_type": {
                    "ui:hidden": "{{!parentFormData.incremental_by_time}}",
                    "type": "string",
                    "title": _l("Timestamp Format"),
                    "default": "datetime",
                    "enum": ["datetime", "date"],
                    "enumNames": ["datetime", "date"],
                },
                "time_auto_round": {
                    "ui:hidden": "{{!parentFormData.incremental_by_time}}",
                    "type": "boolean",
                    "title": "Auto Round Time Range",
                    "default": True,
                    "description": _l(
                        "Automatically round time ranges to appropriate intervals. For example:\n"
                        "- Daily tasks running at 01:23 will sync previous day's data from 00:00 to 00:00\n"
                        "- Weekly tasks will round to Monday 00:00\n"
                        "- Monthly tasks will round to 1st day 00:00\n"
                        "If disabled, exact execution times will be used (e.g. 01:23 to 01:23)"
                    ),
                },
            },
            "required": [
                "data_source_name",
            ],
        }

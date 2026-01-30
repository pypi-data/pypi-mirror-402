import copy
import json
import logging

try:
    from bson import json_util

    from recurvedata.pigeon.dumper.mongodb import MongoDBDumper
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator import utils
from recurvedata.operators.transfer_operator.task import DumpTask
from recurvedata.utils import date_time, extract_dict

logger = logging.getLogger(__name__)


class MongoDBDumpTask(DumpTask):
    ds_name_fields = ("data_source_name",)
    worker_install_require = ["pigeon[mongo]"]

    @property
    def time_column_tz(self):
        return self.config.get("time_column_tz", "UTC")

    def determine_time_range(self):
        start_date, end_date = self.get_schedule_time_range()
        # convert timezone
        start_date = date_time.astimezone(start_date, tz=self.time_column_tz)
        end_date = date_time.astimezone(end_date, tz=self.time_column_tz)

        return start_date.replace(tzinfo=None), end_date.replace(tzinfo=None)

    def execute_impl(self, *args, **kwargs):
        ds = self.must_get_connection_by_name(self.config["data_source_name"])
        hf = self.create_handler_factory()
        dump_options = extract_dict(self.rendered_config, keys=["collection", "filter", "projection"])
        dump_options.update({"connector": ds.connector, "handler_factories": [hf], "database": ds.database})

        # projection 设置为 null 或 '' 都当作 None 处理，即包含所有字段
        proj = dump_options.get("projection")
        if proj:
            dump_options["projection"] = json.loads(proj)
        else:
            dump_options["projection"] = None

        if dump_options["filter"]:
            flt = json_util.loads(dump_options["filter"])
        else:
            flt = {}
        if not self.dag.is_once and self.config.incremental_by_time:
            start, end = self.determine_time_range()
            time_flt = {self.config.time_column: {"$gte": start, "$lt": end}}
            flt.update(time_flt)

        dump_options["filter"] = flt

        logger.info("Dump options: %s", dump_options)
        dumper = MongoDBDumper(**dump_options)
        return dumper.execute()

    @classmethod
    def config_schema(cls):
        # get_choices_by_type = cls.get_connection_names_by_type
        # dss = get_choices_by_type('mongodb')
        return {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": _l("MongoDB Connection"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": [
                            "mongodb",
                        ],
                    },
                },
                "collection": {
                    "type": "string",
                    "title": _l("MongoDB Collection"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "filter": {
                    "type": "string",
                    "title": _l("Query Filter"),
                    "default": "{}",
                    "description": _l(
                        "MongoDB query filter in JSON format. Will be deserialized using bson.json_util and passed to find() method. "
                        "Supports MongoDB query operators like $gt, $lt, $in etc. See MongoDB documentation for details."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "json",
                    },
                },
                "projection": {
                    "type": "string",
                    "title": _l("Field Selection"),
                    "description": _l(
                        "Specify which fields to return in JSON format. Empty value returns all fields. Passed directly to MongoDB find() function."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "json",
                    },
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
            "required": ["data_source_name", "collection"],
        }

import copy

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator import utils
from recurvedata.operators.transfer_operator.task import DumpTask
from recurvedata.pigeon.dumper.aliyun_sls import AliyunSLSDumper
from recurvedata.utils import extract_dict


class AliyunSLSDumpTask(DumpTask):
    ds_name_fields = ("data_source_name",)

    def execute_impl(self, *args, **kwargs):
        ds = self.must_get_connection_by_name(self.config["data_source_name"])
        hf = self.create_handler_factory()
        dump_options = extract_dict(
            self.rendered_config, keys=["project", "logstore", "query", "start_time", "end_time", "fields"]
        )
        access_key_id = ds.data.get("access_key_id")
        access_key_secret = ds.data.get("access_key_secret")
        endpoint = ds.data.get("endpoint")
        dump_options.update(
            {
                "endpoint": endpoint,
                "access_key_id": access_key_id,
                "access_key_secret": access_key_secret,
                "handler_factories": [hf],
            }
        )
        dumper = AliyunSLSDumper(**dump_options)
        return dumper.execute()

    @classmethod
    def config_schema(cls):
        return {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": _l("Aliyun Access Key"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": ["aliyun_access_key"],
                    },
                },
                "project": {"type": "string", "title": _l("Project Name")},
                "logstore": {"type": "string", "title": _l("Logstore Name")},
                "query": {
                    "type": "string",
                    "title": _l("Query"),
                    "description": _l("Query to retrieve logs from Aliyun SLS."),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "sql",
                    },
                },
                "start_time": {
                    "type": "string",
                    "description": _l(
                        "Start time of the data to retrieve, supports Jinja templating for dynamic. Format: %Y-%m-%d %H:%M:%S"
                    ),
                    "title": _l("Start Time"),
                    "default": "{{ data_interval_start }}",
                },
                "end_time": {
                    "type": "string",
                    "description": _l(
                        "End time of the data to retrieve, supports Jinja templating for dynamic. Format: %Y-%m-%d %H:%M:%S"
                    ),
                    "title": _l("End Time"),
                    "default": "{{ data_interval_end }}",
                },
                "fields": {
                    "type": "string",
                    "title": _l("Fields"),
                    "description": _l("Comma-separated list of fields to retrieve. Leave empty to get all fields."),
                },
                "transform": copy.deepcopy(utils.TRANSFORM),
            },
            "required": ["data_source_name", "project", "logstore", "start_time", "end_time"],
        }

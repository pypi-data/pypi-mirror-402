import copy

try:
    import arrow

    from recurvedata.pigeon.dumper.cass import CassandraDumper
    from recurvedata.pigeon.row_factory import ordered_dict_factory
except ImportError:
    pass

from recurvedata.operators.transfer_operator import utils
from recurvedata.operators.transfer_operator.task import DumpTask
from recurvedata.utils import extract_dict


class CassandraDumpTask(DumpTask):
    enabled = False
    worker_install_require = ["pigeon[cassandra]"]
    ds_name_fields = ("data_source_name",)

    def determine_partitions(self):
        if self.config.partitions:
            return self.config.partitions

        if not self.config.incremental_by_time:
            return None

        if self.dag.is_once:
            return None

        start_date, end_date = self.get_schedule_time_range()
        partitions = arrow.Arrow.range(self.config.time_granularity, start_date, end_date)
        partitions = [x.datetime for x in partitions[:-1]]
        return partitions

    def execute_impl(self, *args, **kwargs):
        ds = self.must_get_connection_by_name(self.config["data_source_name"])
        hf = self.create_handler_factory()
        dump_options = extract_dict(
            self.rendered_config, keys=["table", "columns", "where", "partition_column", "concurrency"]
        )
        dump_options.update({"connector": ds.connector, "handler_factories": [hf]})
        partitions = self.determine_partitions()
        if partitions:
            dump_options.update({"partitions": partitions})
        dumper = CassandraDumper(**dump_options)
        # if self.has_custom_transformer():
        dumper.row_factory = ordered_dict_factory
        return dumper.execute()

    @classmethod
    def config_schema(cls):
        # dss = cls.get_connection_names_by_type('cassandra')
        return {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": "Data Source",
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": [
                            "cassandra",
                        ],
                    },
                    # 'default': cls.first_or_default(dss, ''),
                },
                "table": {
                    "type": "string",
                    "title": "Table Name",
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "columns": {
                    "type": "string",
                    "title": "Columns",
                    "description": "要导出的列，用 `,` 分隔；默认导出所有列（*）",
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "where": {
                    "type": "string",
                    "title": "Where Clause",
                    "description": "Where 条件",
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "partition_column": {
                    "type": "string",
                    "title": "Partition Column",
                    "description": "分区键，通常名为 date",
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "partitions": {
                    "type": "string",
                    "title": "Partitions",
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "concurrency": {
                    "type": "number",
                    "ui:options": {"controls": False},
                    "title": "Concurrency",
                    "default": 1,
                    "description": "并发数，1~20",
                    "minimum": 1,
                    "maximum": 20,
                },
                "transform": copy.deepcopy(utils.TRANSFORM),
                "incremental_by_time": {
                    "type": "boolean",
                    "title": "Incremental By Time",
                    "default": False,
                    "description": "是否按时间进行增量同步，这个时间必须是分区键",
                    "ui:widget": "BaseCheckbox",
                    "ui:options": {
                        "label": "Incremental By Time",
                    },
                },
                "time_granularity": {
                    "ui:hidden": "{{!parentFormData.incremental_by_time}}",
                    "type": "string",
                    "title": "Time Granularity",
                    "default": "day",
                    "description": "分区键的时间粒度，用于生成分区值",
                    "enum": ["day", "hour"],
                    "enumNames": ["day", "hour"],
                },
                "time_auto_round": {
                    "ui:hidden": "{{!parentFormData.incremental_by_time}}",
                    "type": "boolean",
                    "title": "Round Time Resolution",
                    "default": True,
                    "description": "是否把数据时间范围 round 到合适的粒度。比如每天 01:23 同步上一个自然日的数据，"
                    "则运行时间是 01:23，数据范围是 [T-1 00:00, T 00:00)；否则数据范围是 [T-1 01:23, T 01:23)。"
                    "开启后，每天运行的任务，数据范围会 round 到 0 点，即自然日；"
                    "每周运行的任务，会 round 到周一 0 点；"
                    "每月运行的任务，会 round 到每月 1 日 0 点",
                },
            },
            # NOTE：前端用的 vue-json-schema 有 bug，enum 字段必须被 required...
            "required": ["data_source_name", "table", "time_granularity"],
            # 处理表单联动，只有 incremental_by_time 为 True 时，才需要显示其他两个输入框
        }

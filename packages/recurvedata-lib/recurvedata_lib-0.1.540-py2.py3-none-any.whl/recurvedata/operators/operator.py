import datetime
from typing import TYPE_CHECKING, Callable

from recurvedata.operators.base import Configurable
from recurvedata.operators.ui import format_config_schema
from recurvedata.utils.registry import Registry

if TYPE_CHECKING:
    from recurvedata.executors.models import ExecutorDag, ExecutorNode
    from recurvedata.operators.task import BaseTask

_registry = Registry(key_callback=lambda x: x.name())


def get_operator_class(name):
    return _registry.get(name)


class BaseOperator(Configurable):
    stages = ()
    task_cls = None
    web_install_require = []  # the python modules needed by Recurve Web
    worker_install_require = []  # the python modules needed by Recurve Worker

    def __init__(
        self, dag: "ExecutorDag", node: "ExecutorNode", execution_date: datetime.datetime, variables: dict = None
    ):
        self.dag: "ExecutorDag" = dag
        self.node: "ExecutorNode" = node
        self.execution_date: datetime.datetime = execution_date
        self.task: BaseTask = None
        self.variables: dict = variables or {}
        self.init_task()

    def __init_subclass__(cls, **kwargs):
        _registry.add(cls)

    def execute(self):
        task_obj = self.task
        if task_obj:
            task_obj.execute()

    def init_task(self):
        if self.task_cls:
            self.task = self.task_cls(self.dag, self.node, self.execution_date, self.variables)

    def set_execution_date(self, execution_date):
        if execution_date == self.execution_date:
            return
        # 有些 T0 任务，需要修改 operator 的 execute_date
        # task 也需要设置 execute_date
        self.execution_date = execution_date
        if self.task:
            self.task.set_execution_date(execution_date)

    @classmethod
    def config_schema(cls) -> dict:
        if cls.task_cls:
            return cls.task_cls.config_schema()

    @classmethod
    def to_dict(cls) -> dict:
        return {
            "name": cls.name(),
            "config_schema": {"source": cls.config_schema()},
        }

    @classmethod
    def get_setup_install_require(cls) -> dict:
        return {
            "web": cls.web_install_require,
            "worker": cls.worker_install_require,
        }

    @classmethod
    def ui_config_schema(cls) -> dict:
        res = {
            "source": {
                "name": "Source",
                "config_schema": format_config_schema(cls.config_schema(), "source"),
            }
        }
        return res

    @staticmethod
    def _add_schema_name_to_json_schema_error(schema_name: str, validate_func: Callable, *args, **kwargs):
        try:
            return validate_func(*args, **kwargs)
        except Exception as e:
            e.schema_name = schema_name
            raise e

    @classmethod
    def ui_validate(cls, configuration: dict) -> dict:
        return {
            "source": cls._add_schema_name_to_json_schema_error(
                "source", cls.validate, cls.ui_config_to_config(configuration)
            ),
        }

    @classmethod
    def ui_config_to_config(cls, configuration: dict) -> dict:
        """
        ui_config: 前端保存时传来的配置，和 ui_config_schema 里一一对应，通常是
            {'source': source_dct, 'meta': meta_dct} 格式
        config: Operator 具体的配置，通常指 ui_config 里的 source。

        区分 ui config 和 config 的原因:
        前端页面，根据 ui config_schema 里配置的，基本分为 Source, Meta 两大块。
        其中 Meta 是调度器相关配置，和具体的 Operator 关联不大。
        为了把调度器相关的校验逻辑、schema 和具体 Operator 区分开，
        设置了 ui_config
        """
        return configuration["source"]

    @classmethod
    def get_ds_name_field_values(cls, rendered_config: dict) -> list[str]:
        config = cls.ui_config_to_config(rendered_config)
        return cls.task_cls.get_ds_name_field_values(config)

import datetime
import json
import logging
import urllib.parse
from functools import cached_property
from typing import TYPE_CHECKING, Any, Optional, Union

import jsonschema

from recurvedata.consts import ETLExecutionStatus
from recurvedata.core.templating import Renderer
from recurvedata.operators.base import Configurable
from recurvedata.operators.context import context
from recurvedata.operators.models import DagBase, NodeBase
from recurvedata.utils.attrdict import AttrDict

if TYPE_CHECKING:
    from recurvedata.executors.client import ExecutorClient


logger = logging.getLogger(__name__)


class LineageTaskMixin(object):
    # todo: move to utils
    def process_lineage(self):
        try:
            lineage = self.parse_lineage()
            self.save_lineage(lineage)
        except Exception as e:
            # lineage_fail_notify(self)
            logger.exception(f"failed to process lineage, error: {e}")

    def parse_lineage(self):
        pass

    def save_lineage(self, lineage):
        if not lineage:
            return

        self.save_lineage(self, lineage)
        # todo: worker sdk


class BaseTask(Configurable, LineageTaskMixin):
    no_template_fields = ()  # 不使用 jinja 渲染的字段
    ds_name_fields = ()

    def __init__(self, dag: DagBase, node: NodeBase, execution_date: datetime.datetime, variables: dict = None):
        self.dag: DagBase = dag
        self.node: NodeBase = node
        self.execution_date: datetime.datetime = execution_date
        self.variables: dict = variables or {}

        self.config = AttrDict(self.node.configuration)
        self.task_instance_id: int = 0

    @classmethod
    def validate(cls, configuration: dict) -> dict:
        config = super().validate(configuration)

        # validate data sources
        for name in cls.ds_name_fields:
            ds = context.get_connection_by_name(connection_name=configuration[name])
            if not ds:
                raise jsonschema.ValidationError(
                    message=f"Unknown data source {repr(configuration[name])}", path=(name,)
                )
        return config

    @classmethod
    def get_ds_name_field_values(cls, rendered_config: dict) -> list[str]:
        res = set()
        for field in cls.ds_name_fields:
            if field in rendered_config:
                ds_name = rendered_config[field]
                res.add(ds_name)
            elif "." in field:
                tmp_rendered_config = rendered_config
                for sub_field in field.split("."):
                    if sub_field not in tmp_rendered_config:
                        break
                    tmp_rendered_config = tmp_rendered_config[sub_field]
                else:
                    if isinstance(tmp_rendered_config, str):
                        ds_name = tmp_rendered_config
                        res.add(ds_name)
        return list(res)

    @cached_property
    def rendered_config(self) -> AttrDict:
        return self.render_config()

    def render_config(self) -> AttrDict:
        result = {}
        env = Renderer()
        ctx = self.get_template_context()

        for k, v in self.config.items():
            if v is None or k in self.__class__.no_template_fields or not isinstance(v, (str, dict, list, tuple)):
                result[k] = v
            else:
                result[k] = env.render_template(v, ctx)
        return AttrDict(result)

    def get_template_context(self) -> dict[str, Any]:
        ctx = Renderer.init_context(self.execution_date, self.dag.schedule_interval)
        ctx.update(self.variables)
        return ctx

    def execute(self, *args, **kwargs):
        # TODO: create new task instance, send request to server or message queue?

        self.on_task_start()

        self.before_execute_hook()

        error = None
        meta = None
        error_stack = None

        logger.info("task configuration: %s", json.dumps(self.rendered_config, indent=2, ensure_ascii=False))
        try:
            meta = self.execute_impl(*args, **kwargs)
        except Exception as exc:
            error = exc
            error_stack = exc.__repr__()
            self.on_execute_impl_error(exc)

        self.after_execute_hook()

        self.on_task_finish(meta, error, error_stack)  # todo: try except?

        if error is not None:
            raise error

    def on_task_start(self):
        self.task_instance_id = context.init_task_instance_on_task_start(self)

    def on_task_finish(self, meta: Any, error: Exception, error_stack: str):
        try:
            if meta:
                meta = meta.to_json()
        except Exception as e:
            logger.debug(f"failed to get json from meta {meta}, error: {e}")
            meta = None
        if error_stack:
            task_status = ETLExecutionStatus.FAILED
        else:
            task_status = ETLExecutionStatus.SUCCESS
        context.update_task_instance_on_task_finish(self, self.task_instance_id, task_status, meta, error, error_stack)

    def before_execute_hook(self):
        pass

    def after_execute_hook(self):
        pass

    def on_execute_impl_error(self, exc: Exception):
        """callback function to be called if `execute_impl` throws exceptions"""
        pass

    def execute_impl(self, *args, **kwargs):
        raise NotImplementedError

    def get_query_comment_conf(self) -> str:
        query_config = {
            "Source": "Recurve",
            "Owner": self.dag.owner,
            "Node": self.node_url,
        }
        return ", ".join(["{}: {}".format(k, v) for k, v in query_config.items()])

    def set_execution_date(self, execution_date):
        if execution_date == self.execution_date:
            return
        _ = self.rendered_config
        # rendered_config 依赖 self.execution_date
        # 需要用旧的 execution_date 渲染后，再替换掉 self.execution_date
        self.execution_date = execution_date

    @property
    def node_url(self) -> str:
        # https://abc.env.name.domain.com/datawork/workflow?p_id=257942399102349312&wf_id=258282502478635008&open_drawer=true&node_key=D2f0I
        host = context.client.base_url  # todo: correct it
        query_string = urllib.parse.urlencode(
            {"p_id": self.dag.project_id, "job_id": self.dag.id, "node_key": self.node.node_key, "open_drawer": "true"}
        )
        return f"{host}/datawork/workspace/job?{query_string}"

    # add proxy methods to avoid importing context everywhere

    @staticmethod
    def get_connection_by_name(name: str):
        return context.get_connection_by_name(name)

    @staticmethod
    def must_get_connection_by_name(name: str):
        return context.must_get_connection_by_name(name)

    @staticmethod
    def get_connection_names_by_type(connection_type: Union[str, list[str]]) -> list[str]:
        return context.get_connection_names_by_type(connection_type)

    @property
    def stage(self) -> Optional[str]:
        return

    @property
    def client(self) -> "ExecutorClient":
        return context.client

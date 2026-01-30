import datetime
import logging
import typing

try:
    from recurvedata.pigeon.utils.fs import new_stagefile_factory
except ImportError:
    pass

from recurvedata.operators.config import CONF
from recurvedata.operators.models import DagBase, NodeBase
from recurvedata.operators.operator import BaseOperator
from recurvedata.operators.transfer_operator.task import get_dump_classes, get_load_classes, get_task_class
from recurvedata.operators.ui import format_config_schema
from recurvedata.utils import md5hash

if typing.TYPE_CHECKING:
    from recurvedata.operators.transfer_operator.task import DumpTask, LoadTask

logger = logging.getLogger(__name__)


class TransferOperator(BaseOperator):
    """
    Operator that handles data transfer operations between dump and load stages.
    Manages the execution of dump and load tasks with appropriate configurations.
    """

    stages = ("dump", "load")

    def __init__(self, dag: DagBase, node: NodeBase, execution_date: datetime.datetime, variables: dict = None) -> None:
        self.dump_task: "DumpTask" = None
        self.load_task: "LoadTask" = None
        self.filename: str = self._determine_filename(dag, node, execution_date)
        # self.execution_date = as_local_datetime(execution_date)

        super().__init__(dag, node, execution_date, variables)

    def init_task(self):
        params = {
            "dag": self.dag,
            "node": self.node,
            "execution_date": self.execution_date,
            "filename": self.filename,
            "variables": self.variables,
        }

        load_config = self.node.configuration["load"]
        load_cls = self.get_task_class(load_config["name"])
        logger.debug(f"create load task with {params}")

        self.load_task: LoadTask = load_cls(config=load_config["config"], **params)

        # TODO: 最好能去掉这种配置，dump 和 load 都使用使用统一的 CSV 格式，由 loader 自己去处理
        handler_options = {
            "encoding": None,
            "write_header": self._determine_write_header(),
        }
        if self.load_task.default_dumper_handler_options:
            handler_options.update(self.load_task.default_dumper_handler_options)

        dump_config = self.node.configuration["dump"]
        dump_cls = self.get_task_class(dump_config["name"])
        logger.debug(f"create dump task with {params}")
        self.dump_task: DumpTask = dump_cls(config=dump_config["config"], handler_options=handler_options, **params)
        self.load_task.dump_task_type = dump_cls.__name__

    def set_execution_date(self, execution_date):
        self.dump_task.set_execution_date(execution_date)
        self.load_task.set_execution_date(execution_date)

    def _determine_write_header(self):
        return self.load_task.should_write_header

    @staticmethod
    def _determine_filename(dag: DagBase, node: NodeBase, execution_date: datetime.datetime) -> str:
        """
        Generate a unique filename for the transfer operation.

        Args:
            dag: The DAG instance
            node: The node instance
            execution_date: The execution datetime

        Returns:
            str: Generated filename
        """
        dag_id = dag.id
        node_id = node.node_key
        is_link_node = getattr(node, "is_link_op", False)
        if not is_link_node:
            hash_txt = md5hash(f"{dag_id}|{node_id}|{execution_date}")
            prefix = f"{dag_id}_{node_id}_"
        else:
            origin_node = node.origin_node
            hash_txt = md5hash(f"{dag_id}|{origin_node.node_key}|{node_id}|{execution_date}")
            prefix = f"{dag_id}_{origin_node.node_key}_{node_id}_"
            logger.info(f"link op _determine_filename: {prefix} {hash_txt}")

        hash_len = max(8, len(hash_txt) - len(prefix))
        return new_stagefile_factory(CONF.DATA_ROOT)(prefix + hash_txt[:hash_len])

    def dump(self):
        return self.dump_task.execute()

    def load(self):
        return self.load_task.execute()

    def execute(self):
        self.dump()
        self.load()

    @classmethod
    def validate(cls, configuration: dict):
        config = {
            "dump": cls._validate_task_config(configuration["dump"]),
            "load": cls._validate_task_config(configuration["load"]),
        }
        return config

    @classmethod
    def _validate_task_config(cls, config: dict):
        task_cls = cls.get_task_class(config["name"])
        cfg = task_cls.validate(config["config"])
        return {"name": config["name"], "config": cfg}

    @classmethod
    def to_dict(cls) -> dict:
        return {
            "name": cls.name(),
            "config_schema": {
                "dump": [x.to_dict() for x in get_dump_classes()],
                "load": [x.to_dict() for x in get_load_classes()],
            },
        }

    @classmethod
    def config_schema(cls):
        return {
            "dump": [{"name": x.name(), "config_schema": x.config_schema()} for x in cls.get_dump_classes()],
            "load": [{"name": x.name(), "config_schema": x.config_schema()} for x in cls.get_load_classes()],
        }

    @classmethod
    def ui_config_schema(cls):
        return {
            "dump": {
                "name": "Dump",
                "config_schema": [
                    {"name": x.name(), "config_schema": format_config_schema(x.config_schema(), "dump")}
                    for x in cls.get_dump_classes()
                ],
            },
            "load": {
                "name": "Load",
                "config_schema": [
                    {"name": x.name(), "config_schema": format_config_schema(x.config_schema(), "load")}
                    for x in cls.get_load_classes()
                ],
            },
        }

    @classmethod
    def ui_validate(cls, configuration: dict) -> dict:
        res = {
            "dump": cls._add_schema_name_to_json_schema_error("dump", cls._validate_task_config, configuration["dump"]),
            "load": cls._add_schema_name_to_json_schema_error("load", cls._validate_task_config, configuration["load"]),
        }
        return res

    @classmethod
    def ui_config_to_config(cls, configuration: dict) -> dict:
        return {
            "dump": configuration["dump"],
            "load": configuration["load"],
        }

    @classmethod
    def get_ds_name_field_values(cls, rendered_config: dict) -> list[str]:
        config = cls.ui_config_to_config(rendered_config)
        res = []
        dump_cls = cls.get_task_class(config["dump"]["name"])
        if dump_cls:
            res.extend(dump_cls.get_ds_name_field_values(config["dump"]["config"]))
        load_cls = cls.get_task_class(config["load"]["name"])
        if load_cls:
            res.extend(load_cls.get_ds_name_field_values(config["load"]["config"]))
        return res

    @classmethod
    def get_task_class(cls, name: str):
        return get_task_class(name)

    @classmethod
    def get_dump_classes(cls, check_enabled=True):
        res_lst = get_dump_classes()
        if check_enabled:
            res_lst = [dump_cls for dump_cls in res_lst if dump_cls.enabled]
        return res_lst

    @classmethod
    def get_load_classes(cls, check_enabled=True):
        res_lst = get_load_classes()
        if check_enabled:
            res_lst = [load_cls for load_cls in res_lst if load_cls.enabled]
        return res_lst

    @classmethod
    def get_setup_install_require(cls) -> dict:
        require_dct = {}
        op_name = cls.name()
        op_web_requires = cls.web_install_require[:]
        op_worker_requires = cls.worker_install_require[:]
        for dump_cls in cls.get_dump_classes():
            if dump_cls.web_install_require:
                require_dct[f"web.{op_name}.dump.{dump_cls.name()}"] = dump_cls.web_install_require
                op_web_requires.extend(dump_cls.web_install_require)
            if dump_cls.worker_install_require:
                require_dct[f"worker.{op_name}.dump.{dump_cls.name()}"] = dump_cls.worker_install_require
                op_worker_requires.extend(dump_cls.worker_install_require)

        for load_cls in cls.get_load_classes():
            if load_cls.web_install_require:
                require_dct[f"web.{op_name}.load.{load_cls.name()}"] = load_cls.web_install_require
                op_web_requires.extend(load_cls.web_install_require)
            if load_cls.worker_install_require:
                require_dct[f"worker.{op_name}.load.{load_cls.name()}"] = load_cls.worker_install_require
                op_worker_requires.extend(load_cls.worker_install_require)
        require_dct["web"] = sorted(list(set(op_web_requires)))
        require_dct["worker"] = sorted(list(set(op_worker_requires)))
        return require_dct

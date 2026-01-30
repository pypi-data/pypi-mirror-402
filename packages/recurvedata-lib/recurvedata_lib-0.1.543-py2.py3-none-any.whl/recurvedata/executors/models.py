from dataclasses import dataclass
from typing import Any

from recurvedata.connectors.service import PigeonDataSource as DataSource  # noqa
from recurvedata.operators import get_operator_class
from recurvedata.operators.models import DagBase, NodeBase


@dataclass
class ExecutorDag(DagBase):
    project_id: int
    workflow_id: int = None
    workflow_version: str = None
    workflow_name: str = None

    @property
    def dag_id(self):
        return self.id


@dataclass
class ExecutorNode(NodeBase):
    dag: ExecutorDag
    operator: str
    config: dict
    variable: dict[str, Any]
    job_variable: dict[str, Any] = None
    stage: str = None
    link_settings: dict[str, Any] = None  # RecurveLink related settings

    @property
    def configuration(self):
        op_cls = get_operator_class(self.operator)
        return op_cls.ui_config_to_config(self.config)

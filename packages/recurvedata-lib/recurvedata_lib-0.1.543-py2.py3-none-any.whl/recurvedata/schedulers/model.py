from dataclasses import dataclass, field
from typing import Optional

from recurvedata.operators.models import DagBase, NodeBase


@dataclass
class SchedulerDag(DagBase):
    workflow_version: str | None = None


@dataclass
class SchedulerNode(NodeBase):
    """
    调度器的 Node 对象
    """

    operator: str

    scheduler_settings: Optional[dict] = None
    skip_self: Optional[bool] = None
    skip_downstream: Optional[bool] = None
    latest_only: Optional[bool] = None


@dataclass
class LinkNodeItem:
    """
    the node linked by LinkOperator
    """

    link_wf_id: int
    link_wf_version: str
    link_node_id: int
    link_node_name: str
    link_node_key: str
    link_latest_only: bool
    link_operator: str
    link_skip_downstream: bool
    link_skip_self: bool
    link_scheduler_settings: dict = None
    link_config: dict = None  # used in CustomAirflowOperator
    node_id: int = None
    plan_id: int = None

    @property
    def config(self):
        # for CustomAirflowOperator
        return self.link_config


@dataclass
class LinkWorkflowItem:
    """
    LinkOperator - link workflow
    """

    node_id: int
    link_wf_id: int
    link_wf_name: str
    link_wf_version: str
    link_graph: list[tuple[str, str]] = field(default_factory=list)  # [(upstream_node_key, downstream_node_key),]
    link_nodes: list[LinkNodeItem] = None

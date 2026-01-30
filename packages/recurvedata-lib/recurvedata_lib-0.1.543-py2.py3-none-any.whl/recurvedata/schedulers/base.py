import datetime
import logging
from dataclasses import dataclass
from functools import cached_property
from typing import ClassVar, Optional

import pendulum

from recurvedata.schedulers.client import SchedulerClient
from recurvedata.schedulers.schemas import JobListResponse
from recurvedata.utils.dataclass import init_dataclass_from_dict

logger = logging.getLogger(__name__)


@dataclass
class DagSchema:
    id: int  # recurve job_id
    name: str  # recurve job_name
    project_id: int
    project_name: str
    workflow_id: int
    workflow_name: str
    workflow_version: str
    graph: list[tuple[str, str]]  # [(upstream_node_key, downstream_node_key),]
    nodes: list
    schedule_type: str
    schedule_interval: str
    timezone: str

    owner_username: str
    # scheduler_args: dict
    start_date: Optional[datetime.datetime] = None
    end_date: Optional[datetime.datetime] = None
    scheduler_settings: Optional[dict] = None
    retries: Optional[int] = None
    retry_delay: Optional[int] = None

    # attr for modeling pipeline
    skip_data_tests: bool = False

    enable_depends_on_jobs: Optional[bool] = False
    depends_on_jobs: Optional[list[dict]] = None

    @property
    def job_id(self):
        return self.id


class SchedulerBase(object):
    DEFAULT_DAG_OWNER: ClassVar[str] = "recurve"

    def __init__(self, sharding_size: int = 1, sharding_key: int = 0):
        self.sharding_size = sharding_size
        self.sharding_key = sharding_key
        self.client: SchedulerClient = self.init_client()

    @cached_property
    def localtz(self):  # todo: move to CONF
        return pendulum.timezone("Asia/Shanghai")

    @classmethod
    def init_client(cls) -> SchedulerClient:
        return SchedulerClient()

    def list_scheduler_dag(self):
        """
        从 sdk 获取符合条件的所有 dag 信息
        :return:
        """

        jobs: JobListResponse = self.client.list_jobs(sharding_size=self.sharding_size, sharding_key=self.sharding_key)

        for job in jobs.jobs:
            dag = init_dataclass_from_dict(DagSchema, job.model_dump())
            yield dag

    def create_dag(self, row: DagSchema):
        """
        生成对应调度器（airflow/...) 的对象
        :param args:
        :param kwargs:
        :return:
        """
        try:
            return self.create_dag_impl(row)
        except Exception as e:
            logger.exception(f"failed to generate dag {row.id}, %s", e)
        return  # todo: add new client api to notify

    def create_dag_impl(self, row: DagSchema):
        pass

    def execute(self, *args, **kwargs):
        """
        入口
        :param args:
        :param kwargs:
        :return:
        """
        for row in self.list_scheduler_dag():
            pass

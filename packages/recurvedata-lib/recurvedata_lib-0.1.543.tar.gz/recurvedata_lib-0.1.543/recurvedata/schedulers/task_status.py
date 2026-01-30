import datetime
import logging
import signal
import sys
import time

import pytz
from airflow.models import DagRun, TaskInstance
from airflow.models.taskinstancehistory import TaskInstanceHistory
from airflow.utils.session import create_session
from sqlalchemy import and_, func, tuple_
from sqlalchemy.orm import joinedload

from recurvedata.config import AgentConfig
from recurvedata.schedulers.client import SchedulerClient
from recurvedata.schedulers.consts import SYSTEM_DAG_PREFIX

logger = logging.getLogger(__name__)


class TaskStatusScanner:
    def __init__(self):
        config = AgentConfig.load()
        if config.request_timeout < 30:
            config.request_timeout = 30
        self.client = SchedulerClient(config)
        self._running = False

    def run(self, interval: int):
        def signal_handler(_sig, _frame):
            self._running = False

        def handle_sigterm(_sig, _frame):
            self._running = False
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, handle_sigterm)

        self._running = True
        step = interval

        while self._running:
            if step >= interval:
                status_cursor = self.client.get_task_status_cursor()

                job_runs = {}
                task_runs = {}

                def _collect_job_runs(_job_runs):
                    for jr in _job_runs:
                        job_runs[(str(jr["job_id"]), jr["run_id"])] = jr

                def _collect_task_runs(_task_runs):
                    for tr in _task_runs:
                        task_runs[(tr["job_id"], tr["run_id"], tr["node_key"])] = tr

                _job_runs = self.scan_dag_runs(
                    self._localize_time(status_cursor.job_run),
                    status_cursor.limit,
                    sliding_time=status_cursor.sliding_time,
                )
                _collect_job_runs(_job_runs)

                _task_runs, _job_runs = self.scan_task_instances(
                    self._localize_time(status_cursor.task_run),
                    status_cursor.limit,
                    sliding_time=status_cursor.sliding_time,
                )
                _collect_job_runs(_job_runs)
                _collect_task_runs(_task_runs)

                _task_runs, _job_runs = self.scan_unfinished_task_instances(
                    status_cursor.unfinished
                )
                _collect_job_runs(_job_runs)
                _collect_task_runs(_task_runs)

                logger.info(f"number of job runs: {len(job_runs)}")
                logger.info(f"number of task runs: {len(task_runs)}")

                # get actual job start time
                filters = list(job_runs.keys())

                if filters:
                    with create_session() as session:
                        query = (
                            session.query(
                                func.min(TaskInstance.start_date).label("start_time"),
                                TaskInstance.dag_id,
                                TaskInstance.run_id,
                                TaskInstance.try_number,
                            )
                            .filter(
                                tuple_(TaskInstance.dag_id, TaskInstance.run_id).in_(
                                    filters
                                )
                            )
                            .group_by(
                                TaskInstance.dag_id,
                                TaskInstance.run_id,
                                TaskInstance.try_number,
                            )
                        )

                        # retried job runs
                        history_filters = []
                        for row in query.all():
                            if row.try_number > 1:
                                history_filters.append((str(row.dag_id), row.run_id))
                                continue

                            job_runs[(row.dag_id), row.run_id]["start_time"] = (
                                row.start_time and row.start_time.isoformat()
                            )

                        if history_filters:
                            query = (
                                session.query(
                                    func.min(TaskInstanceHistory.start_date).label(
                                        "start_time"
                                    ),
                                    TaskInstanceHistory.dag_id,
                                    TaskInstanceHistory.run_id,
                                )
                                .filter(
                                    tuple_(
                                        TaskInstanceHistory.dag_id,
                                        TaskInstanceHistory.run_id,
                                    ).in_(history_filters)
                                )
                                .group_by(
                                    TaskInstanceHistory.dag_id,
                                    TaskInstanceHistory.run_id,
                                )
                            )

                            for row in query.all():
                                job_runs[(row.dag_id, row.run_id)]["start_time"] = (
                                    row.start_time and row.start_time.isoformat()
                                )

                self.client.sync_task_status(
                    job_runs=list(job_runs.values()), task_runs=list(task_runs.values())
                )
                step = 0
            time.sleep(1.0)
            step += 1

    def _localize_time(self, time: datetime.datetime | None):
        if time is not None and time.tzinfo is None:
            timezone = pytz.timezone("UTC")
            time = timezone.localize(time)
        return time

    def _parse_job_id(self, dag_id: str):
        return int(dag_id.split(".")[-1])

    def _sliding_time_query(self, session, model, last_updated_time, sliding_time):
        query = session.query(model).where(~model.dag_id.startswith(SYSTEM_DAG_PREFIX))
        query = query.where(
            and_(
                model.updated_at
                >= (last_updated_time - datetime.timedelta(seconds=sliding_time)),
                model.updated_at < last_updated_time,
            )
        )
        return query.order_by(model.updated_at.asc())

    def _limit_query(self, session, model, last_updated_time, limit):
        query = session.query(model).where(~model.dag_id.startswith(SYSTEM_DAG_PREFIX))
        if last_updated_time is not None:
            query = query.where(model.updated_at >= last_updated_time)
        return query.order_by(model.updated_at.asc()).limit(limit)

    def _format_job_run(self, dr: DagRun, workflow_version: str):
        return dict(
            job_id=self._parse_job_id(dr.dag_id),
            run_id=dr.run_id,
            state=dr.state,
            start_time=dr.start_date and dr.start_date.isoformat(),
            end_time=dr.end_date and dr.end_date.isoformat(),
            execution_date=dr.execution_date and dr.execution_date.isoformat(),
            workflow_version=workflow_version,
            airflow_updated_at=dr.updated_at and dr.updated_at.isoformat(),
            run_type=None,
            data_interval_end=dr.data_interval_end and dr.data_interval_end.isoformat(),
        )

    def scan_dag_runs(
        self,
        last_updated_time: datetime.datetime | None,
        limit: int,
        sliding_time: int = 0,
    ):
        job_runs = []
        workflow_version_map = {}

        with create_session() as session:
            dag_runs: list[DagRun] = []
            if last_updated_time and sliding_time > 0:
                dag_runs.extend(
                    self._sliding_time_query(
                        session, DagRun, last_updated_time, sliding_time
                    ).all()
                )
            dag_runs.extend(
                self._limit_query(session, DagRun, last_updated_time, limit).all()
            )

            for dr in dag_runs:
                workflow_version = workflow_version_map.get((dr.dag_id, dr.run_id))
                if workflow_version is None:
                    ti = (
                        session.query(TaskInstance)
                        .filter(
                            TaskInstance.dag_id == dr.dag_id,
                            TaskInstance.run_id == dr.run_id,
                        )
                        .first()
                    )
                    workflow_version = ti and ti.executor_config.get("workflow_version")
                    if workflow_version is not None:
                        workflow_version_map[(dr.dag_id, dr.run_id)] = workflow_version
                job_runs.append(self._format_job_run(dr, workflow_version))
        return job_runs

    def _format_task_run(self, ti: TaskInstance):
        return dict(
            job_id=self._parse_job_id(ti.dag_id),
            run_id=ti.run_id,
            node_key=ti.task_id,
            state=ti.state,
            try_number=ti._try_number,
            start_time=ti.start_date and ti.start_date.isoformat(),
            end_time=ti.end_date and ti.end_date.isoformat(),
            execution_date=ti.execution_date and ti.execution_date.isoformat(),
            workflow_version=ti.executor_config.get("workflow_version"),
            operator=ti.executor_config.get("operator"),
            task=ti.executor_config.get("task"),
            link_workflow_id=ti.executor_config.get("link_workflow_id"),
            link_workflow_version=ti.executor_config.get("link_workflow_version"),
            airflow_updated_at=ti.updated_at and ti.updated_at.isoformat(),
        )

    def scan_task_instances(
        self,
        last_updated_time: datetime.datetime | None,
        limit: int,
        sliding_time: int = 0,
    ):
        dag_runs = {}
        task_runs = []

        with create_session() as session:
            tis: list[TaskInstance] = []
            if last_updated_time and sliding_time > 0:
                tis.extend(
                    self._sliding_time_query(
                        session, TaskInstance, last_updated_time, sliding_time
                    )
                    .options(joinedload(TaskInstance.dag_run))
                    .all()
                )
            tis.extend(
                self._limit_query(session, TaskInstance, last_updated_time, limit)
                .options(joinedload(TaskInstance.dag_run))
                .all()
            )

            for ti in tis:
                dag_runs[(ti.dag_run.dag_id, ti.dag_run.run_id)] = (
                    ti.dag_run,
                    ti.executor_config.get("workflow_version"),
                )
                task_runs.append(self._format_task_run(ti))
        return task_runs, [
            self._format_job_run(dr, workflow_version)
            for dr, workflow_version in dag_runs.values()
        ]

    def scan_unfinished_task_instances(self, data: dict | None):
        if not data:
            return [], []

        dag_ids = set()
        task_ids = set()
        run_ids = set()
        for dag_id, item in data.items():
            dag_ids.add(dag_id)
            for task_id, _run_ids in item.items():
                task_ids.add(task_id)
                for run_id in _run_ids:
                    run_ids.add(run_id)

        dag_runs = {}
        task_runs = []

        with create_session() as session:
            criterion = []
            if dag_ids:
                criterion.append(TaskInstance.dag_id.in_(dag_ids))
            if task_ids:
                criterion.append(TaskInstance.task_id.in_(task_ids))
            if run_ids:
                criterion.append(TaskInstance.run_id.in_(run_ids))

            tis: list[TaskInstance] = (
                session.query(TaskInstance)
                .where(*criterion)
                .options(joinedload(TaskInstance.dag_run))
                .all()
            )

            for ti in tis:
                if (
                    ti.dag_id not in data
                    or ti.task_id not in data[ti.dag_id]
                    or ti.run_id not in data[ti.dag_id][ti.task_id]
                ):
                    continue
                dag_runs[(ti.dag_run.dag_id, ti.dag_run.run_id)] = (
                    ti.dag_run,
                    ti.executor_config.get("workflow_version"),
                )
                task_runs.append(self._format_task_run(ti))
        return task_runs, [
            self._format_job_run(dr, workflow_version)
            for dr, workflow_version in dag_runs.values()
        ]

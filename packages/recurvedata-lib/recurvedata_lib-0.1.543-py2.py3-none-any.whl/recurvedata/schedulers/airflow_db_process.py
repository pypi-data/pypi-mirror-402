import datetime
import logging
from typing import Any, Optional

from airflow.api.common.mark_tasks import (
    set_dag_run_state_to_failed,
    set_dag_run_state_to_queued,
    set_dag_run_state_to_success,
)
from airflow.api.common.trigger_dag import trigger_dag
from airflow.models import DAG, DagModel, DagRun, TaskInstance
from airflow.models.serialized_dag import SerializedDagModel
from airflow.utils import timezone
from airflow.utils.session import create_session, provide_session
from airflow.utils.state import TaskInstanceState
from sqlalchemy import Index, Table
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateIndex

from recurvedata.utils.date_time import to_local_datetime, utcnow

logger = logging.getLogger(__name__)


class AirflowDbService:
    @classmethod
    def update_dag(cls, dag: DAG):
        logger.info(f"start sync dag {dag.dag_id} to serialized_dag")
        DAG.sync_to_db(dag)
        SerializedDagModel.write_dag(dag)
        logger.info(f"finish sync {dag.dag_id} to serialized_dag")

    @classmethod
    def activate_dag(cls, dag: DAG):
        with create_session() as session:
            d = session.query(DagModel).filter(DagModel.dag_id == dag.dag_id).one_or_none()
            if not d:
                raise ValueError(f"dag not exists: {dag.dag_id}")

            if d.is_paused is False:
                logger.info(f"{dag.dag_id} is active, no need to activate")
                return

            logger.info(f"start activate_dag dag {dag.dag_id}")

            d.is_paused = False
            session.merge(d)
            session.commit()

            logger.info(f"finish activate_dag dag {dag.dag_id}")

    @classmethod
    def deactivate_dag(cls, dag: DAG):
        with create_session() as session:
            d = session.query(DagModel).filter(DagModel.dag_id == dag.dag_id).one_or_none()
            if not d:
                raise ValueError(f"dag not exists: {dag.dag_id}")

            if d.is_paused is True:
                logger.info(f"{dag.dag_id} is deactive, no need to deactivate")
                return

            logger.info(f"start deactivate_dag dag {dag.dag_id}")

            d.is_paused = True
            session.merge(d)
            session.commit()

            logger.info(f"finish deactivate_dag dag {dag.dag_id}")

    @classmethod
    def delete_dag(cls, dag_id: str, job_name: str):
        with create_session() as session:
            d: DagModel = session.query(DagModel).filter(DagModel.dag_id == dag_id).one_or_none()
            if not d:
                logger.warning(f"dag not exists: {dag_id}")
                return

            logger.info(f"start delete_dag dag {job_name} {dag_id}")
            d.is_paused = True
            d.is_active = False
            session.merge(d)
            session.commit()

            logger.info(f"finish delete_dag dag {job_name} {dag_id}")
            # todo(chenjingmeng): delete dag

    @classmethod
    def trigger_job_run(
        cls,
        dag: DAG,
        execution_date: datetime.datetime,
        include_past: bool,
        include_future: bool,
        run_type: str,
        conf: dict[str, Any] | None = None,
    ):
        execution_date_ds = execution_date.isoformat()
        run_id = f"{run_type}__{execution_date_ds}"
        reference_date = to_local_datetime(execution_date_ds)
        current_date = utcnow()
        airflow_current_date = dag.previous_schedule(current_date)

        if include_past:
            airflow_start_date = dag.start_date or dag.default_args.get("start_date")
            if airflow_start_date:
                tmp_date = dag.previous_schedule(reference_date)
                while tmp_date >= airflow_start_date:
                    cls._trigger_run_if_not_exists(
                        dag.dag_id, run_id=f"{run_type}__{tmp_date.isoformat()}", execution_date=tmp_date, conf=conf
                    )
                    tmp_date = dag.previous_schedule(tmp_date)

        if include_future:
            tmp_date = dag.following_schedule(reference_date)
            while tmp_date <= airflow_current_date:
                cls._trigger_run_if_not_exists(
                    dag.dag_id, run_id=f"{run_type}__{tmp_date.isoformat()}", execution_date=tmp_date, conf=conf
                )
                tmp_date = dag.following_schedule(tmp_date)

        cls._trigger_run_if_not_exists(dag.dag_id, run_id, execution_date=execution_date, conf=conf)

    @staticmethod
    def _trigger_run_if_not_exists(
        dag_id: str, run_id: str, execution_date: datetime.datetime, conf: dict[str, Any] | None = None
    ):
        import recurvedata.schedulers.airflow_trigger_dag_patch  # noqa

        with create_session() as session:
            existing_run = session.query(DagRun).filter(DagRun.dag_id == dag_id, DagRun.run_id == run_id).first()
            if existing_run:
                logger.info(f"Skipping existing run for {dag_id} at {run_id}")
                return
        logger.info(f"start trigger dag_run for {dag_id} at {run_id}")
        trigger_dag(dag_id, run_id=run_id, execution_date=execution_date, conf=conf, replace_microseconds=False)
        logger.info(f"finished trigger dag_run for {dag_id} at {run_id} execution_date: {execution_date}")

    @staticmethod
    @provide_session
    def _get_rerun_earliest_execution_date(dag: DAG, session: Session = None) -> Optional[datetime.datetime]:
        earliest_dag_run = (
            session.query(DagRun).filter(DagRun.dag_id == dag.dag_id).order_by(DagRun.execution_date).first()
        )
        return earliest_dag_run and earliest_dag_run.execution_date

    @classmethod
    def rerun_job_run(
        cls,
        dag: DAG,
        run_id: str | None,
        min_execution_date: datetime.datetime | None,
        max_execution_date: datetime.datetime | None,
        failed_only: bool,
    ):
        kwargs = {
            "dag_id": dag.dag_id,
            "run_id": run_id,
            "execution_start_date": min_execution_date,
            "execution_end_date": max_execution_date,
        }
        if min_execution_date or max_execution_date:
            kwargs.pop("run_id")
        drs: list[DagRun] = DagRun.find(**kwargs)
        if not drs:
            logger.info(f"skip rerun, no dag_run found for {dag.dag_id} at {run_id}")
            return
        clear_start_date = min([dr.execution_date for dr in drs])
        clear_end_date = max([dr.execution_date for dr in drs])

        logger.info(
            f"prepare to clear dag_run for {dag.dag_id}, start_date: {clear_start_date}, end_date: {clear_end_date}, failed_only: {failed_only}"
        )

        dag.clear(
            start_date=clear_start_date,
            end_date=clear_end_date,
            only_failed=failed_only,
        )

    @classmethod
    def rerun_task_run(
        cls,
        dag: DAG,
        run_id: str,
        node_key: str,
        min_execution_date: datetime.datetime | None,
        max_execution_date: datetime.datetime | None,
        include_upstream: bool,
        include_downstream: bool,
        failed_only: bool,
    ):
        kwargs = {
            "dag_id": dag.dag_id,
            "run_id": run_id,
            "execution_start_date": min_execution_date,
            "execution_end_date": max_execution_date,
        }
        if min_execution_date or max_execution_date:
            kwargs.pop("run_id")
        drs: list[DagRun] = DagRun.find(**kwargs)
        if not drs:
            logger.info(
                f"skip rerun, no dag_run found for {dag.dag_id} at {run_id}, or between {min_execution_date} and {max_execution_date}"
            )
            return
        clear_start_date = min([dr.execution_date for dr in drs])
        clear_end_date = max([dr.execution_date for dr in drs])
        dr_task_ids_map: dict[str, set[str]] = {dr.run_id: {ti.task_id for ti in dr.get_task_instances()} for dr in drs}

        clear_task_ids: list[str] = []
        for task_id in dag.task_dict.keys():
            if task_id.startswith(node_key):
                clear_task_ids.append(task_id)

        expanded_task_ids = set(clear_task_ids)
        if include_upstream or include_downstream:
            if include_upstream:
                for task_id in clear_task_ids:
                    if task_id in dag.task_dict:
                        task = dag.task_dict[task_id]
                        # Use Airflow's built-in method to get all upstream tasks
                        upstream_task_ids = task.get_flat_relative_ids(upstream=True)
                        expanded_task_ids.update(upstream_task_ids)

            if include_downstream:
                for task_id in clear_task_ids:
                    if task_id in dag.task_dict:
                        task = dag.task_dict[task_id]
                        # Use Airflow's built-in method to get all downstream tasks
                        downstream_task_ids = task.get_flat_relative_ids(upstream=False)
                        expanded_task_ids.update(downstream_task_ids)

        clear_task_ids = list(expanded_task_ids)
        clear_task_ids_set = set(clear_task_ids)
        with create_session() as session:
            for dr in drs:
                extra_task_ids = clear_task_ids_set - dr_task_ids_map[dr.run_id]
                for task_id in extra_task_ids:
                    task = dag.task_dict[task_id]
                    ti = TaskInstance(task, run_id=dr.run_id, map_index=-1)
                    ti.dag_run = dr
                    ti.updated_at = timezone.utcnow()
                    session.add(ti)
            session.commit()

        logger.info(
            f"prepare to clear task: {dag.dag_id}, {clear_task_ids} start_date: {clear_start_date}, end_date: {clear_end_date}, failed_only: {failed_only}"
        )

        clear_cnt = dag.clear(
            task_ids=clear_task_ids,
            start_date=clear_start_date,
            end_date=clear_end_date,
            only_failed=failed_only,
        )
        logger.info(f"finish clear task: {dag.dag_id}, {clear_task_ids}, total clear: {clear_cnt} task_instances")

    @classmethod
    def init_airflow_tables(cls):
        from airflow.settings import engine
        from airflow.utils.db import reflect_tables

        def _is_index_exists(session: Session, table_name: str, index_name: str) -> bool:
            query = f"""
            SELECT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE tablename = {table_name!r}
                  AND indexname = {index_name!r}
            )
            """
            result = session.execute(query)
            return result.scalar()

        with create_session() as session:
            metadata = reflect_tables(tables=["dag_run", "task_instance"], session=session)
            dag_run = Table("dag_run", metadata, autoload_with=engine)
            task_instance = Table("task_instance", metadata, autoload_with=engine)

            dag_run_updated_at_idx = Index("ix_dag_run_updated_at", dag_run.c.updated_at)
            task_instance_updated_at_idx = Index("ix_task_instance_updated_at", task_instance.c.updated_at)

            with engine.connect():
                if not _is_index_exists(session, "dag_run", "ix_dag_run_updated_at"):
                    logger.info("start creating index on dag_run.updated_at")
                    session.execute(CreateIndex(dag_run_updated_at_idx))
                    logger.info("Created index on dag_run.updated_at")
                else:
                    logger.info("Skipped creating index on dag_run.updated_at")

                if not _is_index_exists(session, "task_instance", "ix_task_instance_updated_at"):
                    logger.info("start creating index on task_instance.updated_at")
                    session.execute(CreateIndex(task_instance_updated_at_idx))
                    logger.info("Created index on task_instance.updated_at")
                else:
                    logger.info("Skipped creating index on task_instance.updated_at")

    @classmethod
    def mark_dag_run_success(cls, dag: DAG, run_id: str = None, whole_dag: bool = False):
        if not run_id:
            if not whole_dag:
                logger.info("mark_dag_run need a run_id, skip mark_dag_run")
                return
            run_ids = cls._get_dag_run_ids(dag)
            for run_id in run_ids:
                cls.mark_dag_run_success(dag, run_id)
            return
        logger.info(f"start mark dag run {dag.dag_id} {run_id} to success")
        set_dag_run_state_to_success(dag=dag, run_id=run_id, commit=True)

    @classmethod
    def mark_dag_run_failed(cls, dag: DAG, run_id: str = None, whole_dag: bool = False):
        """
        will mark un-running tasks to skipped;
        mark running tasks to failed;
        keep finished tasks the same.
        """
        if not run_id:
            if not whole_dag:
                logger.info("mark_dag_run need a run_id, skip mark_dag_run")
                return
            run_ids = cls._get_dag_run_ids(dag)
            for run_id in run_ids:
                cls.mark_dag_run_failed(dag, run_id)
            return
        logger.info(f"start mark dag run {dag.dag_id} {run_id} to failed")
        set_dag_run_state_to_failed(dag=dag, run_id=run_id, commit=True)

    @classmethod
    def mark_dag_run_queued(cls, dag: DAG, run_id: str = None, whole_dag: bool = False):
        """
        Mark dag run state to queued.
        """
        if not run_id:
            if not whole_dag:
                logger.info("mark_dag_run need a run_id, skip mark_dag_run")
                return
            run_ids = cls._get_dag_run_ids(dag)
            for run_id in run_ids:
                cls.mark_dag_run_queued(dag, run_id)
            return
        logger.info(f"start mark dag run {dag.dag_id} {run_id} to queued")
        set_dag_run_state_to_queued(dag=dag, run_id=run_id, commit=True)

    @staticmethod
    @provide_session
    def _get_dag_run_ids(dag: DAG, session: Session = None) -> list[str]:
        query = session.query(DagRun.run_id).filter(DagRun.dag_id == dag.dag_id)
        return [res[0] for res in query.all()]

    @classmethod
    @provide_session
    def delete_whole_dag_dr_ti(cls, dag: DAG, session: Session = None):
        logger.info(f"start delete whole dag_run and task_instance for {dag.dag_id}")
        for model in (TaskInstance, DagRun):
            session.query(model).filter(model.dag_id == dag.dag_id).delete(synchronize_session="fetch")
        logger.info(f"finish deleted whole dag_run and task_instance for {dag.dag_id}")

    @staticmethod
    @provide_session
    def _set_task_run_state(dag: DAG, run_id: str, node_key: str, state: TaskInstanceState, session: Session = None):
        logger.info(f"start set task_run {dag.dag_id} {run_id} {node_key} to {state}")
        dag.set_task_instance_state(
            task_id=node_key,
            run_id=run_id,
            state=state,
            session=session,
        )
        logger.info(f"finish set task_run {dag.dag_id} {run_id} {node_key} to {state}")

    @staticmethod
    def terminate_task_run(dag: DAG, run_id: str, node_key: str):
        AirflowDbService._set_task_run_state(dag, run_id, node_key, TaskInstanceState.FAILED)

import logging
from typing import Optional

from airflow.models import DAG

from recurvedata.schedulers.airflow import AirflowScheduler
from recurvedata.schedulers.consts import get_dag_file_loc

logger = logging.getLogger(__name__)


def get_job_dag(job_id: int) -> Optional["DAG"]:
    scheduler = AirflowScheduler(sharding_size=job_id, sharding_key=0)
    dag_dct = scheduler.execute()
    dag_ids = list(dag_dct.keys())
    if not dag_ids:
        return
    dag = dag_dct[dag_ids[0]]
    dag.fileloc = get_dag_file_loc(job_id)
    return dag

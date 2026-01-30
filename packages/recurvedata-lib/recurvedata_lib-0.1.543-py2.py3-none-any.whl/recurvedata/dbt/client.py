import os

from recurvedata.client import Client
from recurvedata.dbt.schemas import AnalyticsDatabaseConnectionAndVariable, DbtGzMd5
from recurvedata.executors.schemas import ConnectionItem
from recurvedata.executors.utils import get_airflow_run_id
from recurvedata.utils import get_env_id


class DbtClient(Client):
    def fetch_project_gzip_md5(self, project_id: int) -> DbtGzMd5:
        params = {"env_id": get_env_id(), "project_id": project_id}
        return self.request(
            "GET",
            path=f"/api/dbt/project/{project_id}/md5",
            response_model_class=DbtGzMd5,
            params=params,
            retries=5,
        )

    def fetch_project_gzip(self, project_id: int, file_name: str, client_md5: str = None):
        # client_md5 is the md5 of the file on the client side, if client_md5 is not changed in the server side, the file will not be downloaded
        params = {"env_id": get_env_id(), "project_id": project_id}
        if client_md5:
            params["client_md5"] = client_md5
        return self.request_file(
            "GET",
            path=f"/api/dbt/project/{project_id}/gz",
            params=params,
            file_name=file_name,
            retries=5,
        )

    def send_dbt_model_result(
        self,
        job_id: int,
        node_key: str,
        compiled_sql: str,
        run_sql: str,
        run_sql_log: list[dict] | None,
        materialization: str,
        try_number: int,
        raw_materialized_result: dict = None,
        raw_test_result: dict = None,
        test_case_sample_data: dict[str, dict] = None,
        test_case_skipped: bool = False,
    ):
        payload = {
            "raw_materialized_result": raw_materialized_result,
            "raw_test_result": raw_test_result,
            "compiled_code": compiled_sql,
            "run_sql": run_sql,
            "run_sql_log": run_sql_log,
            "materialization": materialization,
            "test_case_sample_data": test_case_sample_data,
            "data_interval_end": os.environ.get("AIRFLOW_DATA_INTERVAL_END"),
            "try_number": try_number,
            "test_case_skipped": test_case_skipped,
        }
        params = {
            "env_id": get_env_id(),
            "run_id": get_airflow_run_id(),
        }
        return self.request(
            "POST",
            path=f"/api/dbt/model_result/{job_id}/{node_key}",
            params=params,
            json=payload,
            timeout=10,
            retries=5,
        )

    def get_connection(self, project_id: int) -> ConnectionItem:
        params = {
            "env_id": get_env_id(),
            "project_id": project_id,
        }
        return self.request(
            "GET",
            path="/api/dbt/connection",
            response_model_class=ConnectionItem,
            params=params,
            retries=5,
        )

    def get_connection_and_variables(self, project_id: int) -> AnalyticsDatabaseConnectionAndVariable:
        params = {
            "env_id": get_env_id(),
            "project_id": project_id,
        }
        return self.request(
            "GET",
            path="/api/dbt/connection_and_variable",
            response_model_class=AnalyticsDatabaseConnectionAndVariable,
            params=params,
            retries=5,
        )

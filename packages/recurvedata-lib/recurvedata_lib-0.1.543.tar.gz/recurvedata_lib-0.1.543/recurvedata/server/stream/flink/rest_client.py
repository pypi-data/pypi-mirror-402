import time
from typing import Dict, List, Optional, Self

import requests
from loguru import logger

from recurvedata.exceptions import RecurveException
from recurvedata.executors.schemas import ConnectionItem

MAX_WAIT_TIME = 60
POLL_INTERVAL = 2


class FlinkRestClient:
    """
    Client to interact with Flink REST API
    Docs: https://nightlies.apache.org/flink/flink-docs-master/docs/ops/rest_api
    """

    def __init__(self, flink_url: str):
        self.flink_url = flink_url
        self.base_headers = {"Content-Type": "application/json"}

    @classmethod
    def from_connection(cls, connection_item: ConnectionItem) -> Self:
        flink_url = connection_item.data.get("flink_url")
        if not flink_url:
            raise RecurveException(data="Flink URL is not set in the flink connection")
        return cls(flink_url=flink_url)

    def get_cluster_info(self) -> Dict:
        """Get Flink cluster overview information"""
        response = requests.get(f"{self.flink_url}/v1/overview")
        response.raise_for_status()
        return response.json()

    def list_jobs(self) -> List[Dict]:
        """List all jobs in the Flink cluster"""
        response = requests.get(f"{self.flink_url}/v1/jobs")
        response.raise_for_status()
        return response.json()

    def get_job_details(self, job_id: str) -> Dict:
        """Get detailed information about a specific job

        Args:
            job_id: The Flink job ID

        Returns:
            Job details dictionary
        """
        response = requests.get(f"{self.flink_url}/v1/jobs/{job_id}")
        try:
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to get job details: {e}")
            raise RecurveException(data=f"Failed to get job details: {str(e)}")
        return response.json()

    def get_job_status(self, job_id: str) -> str:
        """Get the status of a job

        Args:
            job_id: The Flink job ID

        Returns:
            Job status string (RUNNING, FINISHED, FAILED, CANCELED, etc.)
        """
        details = self.get_job_details(job_id)
        return details.get("state", "UNKNOWN")

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job

        Args:
            job_id: The Flink job ID

        Returns:
            True if cancellation was successful
        """
        response = requests.patch(f"{self.flink_url}/v1/jobs/{job_id}")

        if response.status_code in [200, 202]:
            logger.info(f"Job {job_id} canceled successfully")
            return True
        else:
            logger.error(f"Failed to cancel job {job_id}")
            logger.debug(f"Response: {response.text}")
            raise RecurveException(data=f"Failed to cancel job {job_id}: {response.text}")

    def _waiting_for_job_savepoints_completion(self, response: requests.Response, job_id: str) -> str:
        request_id = response.json().get("request-id")

        # Poll for savepoint completion
        max_wait_time = MAX_WAIT_TIME  # seconds
        poll_interval = POLL_INTERVAL  # seconds
        elapsed_time = 0

        while elapsed_time < max_wait_time:
            status_response = requests.get(f"{self.flink_url}/v1/jobs/{job_id}/savepoints/{request_id}")

            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get("status", {}).get("id")

                if status == "COMPLETED":
                    savepoint_path = status_data.get("operation", {}).get("location")
                    logger.info(f"Job {job_id} savepoint completed: {savepoint_path}")
                    return savepoint_path
                elif status == "FAILED":
                    error = status_data.get("operation", {}).get("failure-cause", {})
                    logger.error(f"Job {job_id} savepoint failed: {error}")
                    raise RecurveException(data=f"Job {job_id} savepoint failed: {error}")

            time.sleep(poll_interval)
            elapsed_time += poll_interval

        logger.warning(f"Job {job_id} savepoint request timed out after {max_wait_time}s")
        raise RecurveException(data=f"Job {job_id} savepoint request timed out after {max_wait_time}s")

    def stop_job_with_savepoint(
        self,
        job_id: str,
        target_directory: str = None,
        drain: bool = True,
    ) -> Optional[str]:
        """Stop a job with savepoint

        Args:
            job_id: The Flink job ID
            target_directory: Directory to save the savepoint (defaults to consts.SAVE_POINT_PATH)
            drain: Whether to drain the job before stopping

        Returns:
            Savepoint path if successful, None otherwise
        """
        target_dir = target_directory or "..."  # TODO: implement this

        logger.info(f"Stopping job {job_id} with savepoint...")
        payload = {"targetDirectory": target_dir, "drain": drain}

        response = requests.post(f"{self.flink_url}/v1/jobs/{job_id}/stop", json=payload, headers=self.base_headers)

        if response.status_code not in [200, 202]:
            logger.error(f"Failed to stop job {job_id} with savepoint")
            logger.debug(f"Response: {response.text}")
            raise RecurveException(data=f"Failed to stop job {job_id} with savepoint: {response.text}")

        savepoint_path = self._waiting_for_job_savepoints_completion(response, job_id)
        return savepoint_path

    def trigger_savepoint(
        self,
        job_id: str,
        target_directory: str = None,
        cancel_job: bool = False,
    ) -> str:
        """Trigger a savepoint for a running job

        Args:
            job_id: The Flink job ID
            target_directory: Directory to save the savepoint
            cancel_job: Whether to cancel the job after savepoint

        Returns:
            Savepoint path if successful
        """
        target_dir = target_directory or "..."  # TODO: implement this

        logger.info(f"Triggering savepoint for job {job_id}...")
        payload = {"target-directory": target_dir, "cancel-job": cancel_job}

        response = requests.post(
            f"{self.flink_url}/v1/jobs/{job_id}/savepoints", json=payload, headers=self.base_headers
        )

        if response.status_code not in [200, 202]:
            logger.error(f"Failed to trigger savepoint for job {job_id}")
            logger.debug(f"Response: {response.text}")
            raise RecurveException(data=f"Failed to trigger savepoint for job {job_id}")

        savepoint_path = self._waiting_for_job_savepoints_completion(response, job_id)
        return savepoint_path

    def get_job_exceptions(self, job_id: str, max_exceptions: int = 10) -> List[Dict]:
        """Get exceptions for a job

        Args:
            job_id: The Flink job ID
            max_exceptions: Maximum number of exceptions to retrieve

        Returns:
            List of exception dictionaries
        """
        response = requests.get(
            f"{self.flink_url}/v1/jobs/{job_id}/exceptions", params={"maxExceptions": max_exceptions}
        )
        response.raise_for_status()
        return response.json().get("all-exceptions", [])

    def get_job_metrics(self, job_id: str, metric_names: List[str] = None) -> Dict:
        """Get metrics for a job

        Args:
            job_id: The Flink job ID
            metric_names: Optional list of specific metric names to retrieve

        Returns:
            Metrics dictionary
        """
        url = f"{self.flink_url}/v1/jobs/{job_id}/metrics"
        params = {}
        if metric_names:
            params["get"] = ",".join(metric_names)

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def wait_for_job_status(
        self,
        job_id: str,
        expected_status: str,
        timeout: int = 60,
        poll_interval: float = 2.0,
    ) -> bool:
        """Wait for a job to reach a specific status

        Args:
            job_id: The Flink job ID
            expected_status: Expected status (RUNNING, FINISHED, FAILED, etc.)
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds

        Returns:
            True if job reached expected status, False if timeout
        """
        logger.info(f"Waiting for job {job_id} to reach status: {expected_status}")
        elapsed_time = 0

        while elapsed_time < timeout:
            try:
                status = self.get_job_status(job_id)

                if status == expected_status:
                    logger.info(f"Job {job_id} reached status: {expected_status}")
                    return True
                elif status in ["FAILED", "CANCELED"] and expected_status not in ["FAILED", "CANCELED"]:
                    logger.error(f"Job {job_id} entered terminal state: {status}")
                    return False

                time.sleep(poll_interval)
                elapsed_time += poll_interval
            except Exception as e:
                logger.warning(f"Error checking job {job_id} status: {e}")
                time.sleep(poll_interval)
                elapsed_time += poll_interval

        logger.warning(f"Job {job_id} timeout waiting to reach status: {expected_status}")
        raise RecurveException(data=f"Job {job_id} timeout waiting to reach status: {expected_status}")

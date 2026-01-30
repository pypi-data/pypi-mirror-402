import json
import time
from contextlib import contextmanager
from typing import Dict

import requests
from loguru import logger

from recurvedata.exceptions import RecurveException
from recurvedata.executors.schemas import ConnectionItem
from recurvedata.server.stream.flink.schema import FlinkConfig, SqlGatewayClientExecuteStatementResponse

MAX_WAIT_TIME = 60
POLL_INTERVAL = 0.5


class FlinkSQLGatewayClient:
    """Client to interact with Flink SQL Gateway REST API"""

    def __init__(
        self,
        gateway_url: str,
        checkpoint_path: str = None,
        save_point_path: str = None,
        checkpoint_interval: int = 10000,
        parallelism: int = 1,
        max_parallelism: int = None,
        restart_strategy: str = "fixed-delay",
    ):
        self.gateway_url = gateway_url
        self.checkpoint_path = checkpoint_path
        self.save_point_path = save_point_path
        self.checkpoint_interval = checkpoint_interval
        self.parallelism = parallelism
        self.max_parallelism = max_parallelism
        self.restart_strategy = restart_strategy
        self.base_headers = {"Content-Type": "application/json"}

    @classmethod
    def from_connection(cls, connection_item: ConnectionItem, flink_config: FlinkConfig) -> "FlinkSQLGatewayClient":
        flink_url = connection_item.data.get("flink_url")
        if not flink_url:
            raise RecurveException(data="Flink URL is not set in the flink connection")

        gateway_port = connection_item.data.get("flink_sql_gateway_port")
        if not gateway_port:
            raise RecurveException(data="Flink SQL Gateway port is not set in the flink connection")

        if flink_url.startswith("http"):
            base_url = ":".join(flink_url.split(":")[:2])
        else:
            base_url = f"http://{flink_url.split(':')[0]}"

        client = cls(
            gateway_url=f"{base_url}:{gateway_port}",
            checkpoint_path=None,
            save_point_path=None,
            checkpoint_interval=flink_config.checkpoint_interval,
            parallelism=flink_config.parallelism,
            max_parallelism=flink_config.max_parallelism,
            restart_strategy=flink_config.restart_strategy,
        )
        return client

    def create_session(self) -> str:
        """Create a new SQL Gateway session"""
        url = f"{self.gateway_url}/v1/sessions"
        properties = {
            "execution.runtime-mode": "streaming",
            # Checkpoint configuration
            "execution.checkpointing.interval": f"{self.checkpoint_interval}ms",
            "execution.checkpointing.mode": "EXACTLY_ONCE",
            "execution.checkpointing.externalized-checkpoint-retention": "RETAIN_ON_CANCELLATION",
            # CORRECT property names for checkpoint storage
            "execution.checkpointing.checkpoints-after-tasks-finish.enabled": "true",
            "parallelism.default": self.parallelism,
        }
        if self.checkpoint_path:
            properties["state.checkpoints.dir"] = self.checkpoint_path
        if self.save_point_path:
            properties["state.savepoints.dir"] = self.save_point_path
        payload = {"properties": properties}

        response = requests.post(url, json=payload, headers=self.base_headers)
        response.raise_for_status()

        session_handle = response.json()["sessionHandle"]
        logger.info(f"Created session: {session_handle}")
        return session_handle

    def execute_statement(
        self,
        sql_statement: str,
        wait_for_completion: bool = False,
        session_handle: str = None,
    ) -> SqlGatewayClientExecuteStatementResponse:
        """Execute a SQL statement via SQL Gateway.

        Args:
            session_handle: The SQL Gateway session handle
            sql_statement: The SQL statement to execute
            wait_for_completion: If True, wait and check if operation succeeds (default: True)

        Returns:
            SqlGatewayClientExecuteStatementResponse if successful

        Raises:
            RecurveException if operation fails
        """

        def _execute(_session_handle: str) -> SqlGatewayClientExecuteStatementResponse:
            response = requests.post(
                f"{self.gateway_url}/v1/sessions/{_session_handle}/statements", json={"statement": sql_statement}
            )

            operation_data = response.json()
            operation_handle = operation_data.get("operationHandle")

            if not operation_handle:
                error_msg = "Failed to submit SQL statement"
                logger.error(error_msg)
                logger.debug(json.dumps(operation_data, indent=2))
                raise RecurveException(data=f"{error_msg}: {operation_data}")

            if not wait_for_completion:
                return SqlGatewayClientExecuteStatementResponse()

            # Poll operation status until it completes or fails
            max_wait_time = MAX_WAIT_TIME  # seconds
            poll_interval = POLL_INTERVAL  # seconds
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                status_data = self.get_operation_status(_session_handle, operation_handle)
                status = status_data.get("status")

                if status == "FINISHED":
                    logger.info("SQL statement completed successfully")
                    result_data = self.get_operation_result(_session_handle, operation_handle)
                    if "jobID" in result_data:
                        job_id = result_data["jobID"]
                    else:
                        job_id = None
                    return SqlGatewayClientExecuteStatementResponse(job_id=job_id)
                elif status == "ERROR":
                    actual_error = self._handle_operation_error(_session_handle, operation_handle, status_data)
                    raise RecurveException(data=f"SQL statement failed: {actual_error}")
                elif status == "CANCELED":
                    raise RecurveException(data="SQL statement was canceled")
                elif status in ["INITIALIZED", "PENDING", "RUNNING"]:
                    # Still processing, wait and poll again
                    time.sleep(poll_interval)
                    elapsed_time += poll_interval
                else:
                    logger.warning(f"Unknown status: {status}")
                    logger.debug(f"Full status response: {json.dumps(status_data, indent=2)}")
                    time.sleep(poll_interval)
                    elapsed_time += poll_interval

            # Timeout reached
            logger.warning(f"SQL statement status check timed out after {max_wait_time}s")
            return SqlGatewayClientExecuteStatementResponse(
                error=f"SQL statement status check timed out after {max_wait_time}s"
            )

        if session_handle:
            return _execute(session_handle)
        else:
            with self.get_session() as session_handle:
                return _execute(session_handle)

    def _handle_operation_error(self, session_handle: str, operation_handle: str, status_data: Dict) -> str:
        """Extract and format error message from a failed operation.

        Args:
            session_handle: The SQL Gateway session handle
            operation_handle: The operation handle
            status_data: The status response data

        Returns:
            Formatted error message string
        """
        logger.error("SQL statement failed!")
        logger.debug(f"Status response: {json.dumps(status_data, indent=2)}")

        try:
            # Fetch the full operation result to get detailed error message
            result_data = self.get_operation_result(session_handle, operation_handle)
            logger.debug("\nDetailed error from result endpoint:")
            logger.debug(json.dumps(result_data, indent=2))

            # Extract error message from various possible locations
            error_msg = self._extract_error_from_result(result_data, status_data)

            # Extract actual error text
            if isinstance(error_msg, dict):
                actual_error = error_msg.get("message") or error_msg.get("errorMessage") or str(error_msg)
            elif error_msg:
                actual_error = str(error_msg)[:500]  # Limit length
            else:
                actual_error = "Unknown error - check logs above"

            return actual_error

        except Exception as e:
            logger.exception(f"Could not fetch detailed error: {e}")
            return "Error occurred, check Flink UI for details"

    def _extract_error_from_result(self, result_data: Dict, status_data: Dict) -> str:
        """Extract error message from result data.

        Args:
            result_data: The operation result data
            status_data: The operation status data

        Returns:
            Error message string or None
        """
        error_msg = None

        # Check if errors are in an "errors" array
        if "errors" in result_data and isinstance(result_data["errors"], list):
            # Get the first error that contains useful info
            for err in result_data["errors"]:
                if err and "Internal server error" not in err:
                    error_msg = err
                    break
                elif err and "Caused by:" in err:
                    # Extract the root cause from stack trace
                    lines = err.split("\n")
                    for line in lines:
                        if "ValidationException:" in line or "SqlExecutionException:" in line:
                            error_msg = line.split(":", 1)[-1].strip()
                            break
                    if error_msg:
                        break

        # Try other common error fields
        if not error_msg:
            error_msg = (
                result_data.get("errorMessage")
                or result_data.get("error")
                or status_data.get("errorMessage")
                or status_data.get("error")
            )

        return error_msg

    def get_operation_status(self, session_handle: str, operation_handle: str) -> Dict:
        """Get the status of an operation."""
        response = requests.get(f"{self.gateway_url}/v1/sessions/{session_handle}/operations/{operation_handle}/status")
        return response.json()

    def get_operation_result(self, session_handle: str, operation_handle: str) -> Dict:
        """Get the full result of an operation (includes error details)."""
        response = requests.get(
            f"{self.gateway_url}/v1/sessions/{session_handle}/operations/{operation_handle}/result/0"
        )
        return response.json()

    def close_session(self, session_handle: str):
        """Close the current session"""
        url = f"{self.gateway_url}/v1/sessions/{session_handle}"
        response = requests.delete(url, headers=self.base_headers)
        response.raise_for_status()
        logger.info(f"Closed session: {session_handle}")

    @contextmanager
    def get_session(self):
        """Context manager for SQL Gateway session.

        Usage:
            with get_session() as session_handle:
                # use session_handle here
                execute_statement(session_handle, sql)
        """
        session_handle = None
        try:
            session_handle = self.create_session()
            yield session_handle
        except Exception as e:
            logger.exception(f"Error during session execution: {e}")
            raise
        finally:
            if session_handle:
                try:
                    self.close_session(session_handle)
                except Exception as e:
                    logger.warning(f"Warning: Failed to close session: {e}")

import logging
import os
import time
import traceback
from typing import Dict, Any
from tempfile import NamedTemporaryFile

from recurvedata.executors.client import ExecutorClient
from recurvedata.operators.config import CONF
from recurvedata.config import RECURVE_EXECUTOR_PYENV_NAME, PY_PACKAGES_PATH
from recurvedata.operators.python_operator.operator import PythonTask, PythonRequirementsMixin
from recurvedata.server.executor.schemas import PythonScriptValidationResult
from recurvedata.utils.mp import robust_run_subprocess

logger = logging.getLogger(__name__)

DEFAULT_PY_VERSION = os.environ.get("RECURVE_OPERATOR_PYTHON_DEFAULT_VERSION", "3.11.9")


class ExecutorService:
    """Service for executing Python code validation using the same infrastructure as PythonOperator"""

    @staticmethod
    def validate_python_script(
        project_id: int,
        python_code: str, 
        python_env_conn_name: str,
    ) -> PythonScriptValidationResult:
        """
        Validate Python script by executing it in the specified Python environment.
        
        Uses the same logic as PythonOperator to ensure consistency with actual execution.
        
        Args:
            project_id: Project ID for context
            python_code: Python code to validate
            python_env_conn_name: Python environment from project connection name
            
        Returns:
            PythonScriptValidationResult with validation status and details
        """
        start_time = time.time()
        requirements = ""
        
        try:
            logger.info(f"Starting Python script validation for project: {project_id} with python env conn name: {python_env_conn_name}")
            
            # Get connection configuration from gateway executor service API by project connection name
            conn_config = ExecutorService._get_python_env_config(python_env_conn_name, project_id)
            
            # Prepare environment using PythonOperator logic (reuse existing methods)
            pyenv_name: str = conn_config.get("pyenv")
            py_version: str = conn_config.get("python_version", DEFAULT_PY_VERSION)
            requirements = conn_config.get("requirements", "")
            
            logger.info(f"Preparing Python environment: {pyenv_name} with version {py_version} and requirements: {requirements}")
            
            # Reuse existing static methods from PythonTask and PythonRequirementsMixin
            PythonTask._install_virtualenv(py_version, pyenv_name)
            if requirements:
                # Use custom requirements installation to capture error output
                ExecutorService._install_requirements_with_output_capture(requirements, pyenv_name)
            
            # Execute the Python code
            ExecutorService._execute_python_code(python_code, conn_config, project_id)
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            logger.info(f"Python script validation completed successfully in {execution_time_ms:.2f}ms")
            
            return PythonScriptValidationResult(
                valid=True,
                message="Python script executed successfully",
                execution_time_ms=execution_time_ms,
                installed_requirements=requirements
            )
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_details = {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc()
            }
            
            logger.error(f"Python script validation failed: {error_details}")
            
            return PythonScriptValidationResult(
                valid=False,
                message=f"Python script validation failed: {str(e)}",
                error=error_details,
                execution_time_ms=execution_time_ms,
                installed_requirements=requirements
            )

    @staticmethod
    def _get_python_env_config(python_env_project_conn_name: str, project_id: int) -> Dict[str, Any]:
        """
        Get Python environment configuration using ExecutorClient.
        
        Fetches the real connection configuration from the executor API.
        """
        try:
            logger.info(f"Fetching Python environment configuration for: {python_env_project_conn_name} in project: {project_id}")
            
            # Create ExecutorClient to fetch connection configuration
            executor_client = ExecutorClient()
            
            # Use the get_py_conn_configs method to fetch configuration
            py_conn_config = executor_client.get_py_conn_configs(
                conn_type="python",
                pyenv_name=RECURVE_EXECUTOR_PYENV_NAME,
                project_conn_name=python_env_project_conn_name,
                project_id=project_id
            )
            
            logger.info(f"Retrieved Python connection config: {py_conn_config}")
            
            # Extract the configuration data
            if py_conn_config and isinstance(py_conn_config, dict):
                # The response structure should contain the environment configuration
                requirements_data = py_conn_config.get("requirements", "")
                
                # Handle requirements - could be a list or string
                if isinstance(requirements_data, list):
                    # Join multiple requirements with newlines
                    requirements_str = "\n".join(requirements_data)
                else:
                    requirements_str = requirements_data or ""
                
                config = {
                    "pyenv": py_conn_config.get("pyenv"),
                    "python_version": py_conn_config.get("python_version", DEFAULT_PY_VERSION),
                    "requirements": requirements_str
                }
                logger.info(f"Using python env configuration: {config}")
                return config
            else:
                logger.warning(f"No configuration found for {python_env_project_conn_name} in project: {project_id}, using defaults: {DEFAULT_PY_VERSION}")
                
        except Exception as e:
            logger.error(f"Failed to fetch Python environment config for {python_env_project_conn_name} in project: {project_id}: {e}")
            logger.info("Falling back to default configuration")
        
        # Fallback to default configuration
        return {
            "pyenv": RECURVE_EXECUTOR_PYENV_NAME,
            "python_version": DEFAULT_PY_VERSION,
            "requirements": ""
        }

    @staticmethod
    def _install_requirements_with_output_capture(requirements: str, pyenv_name: str) -> None:
        """
        Install requirements with output capture to include pip errors in exceptions.
        
        This is a modified version of PythonRequirementsMixin._install_requirements
        that captures the subprocess output for better error reporting.
        """
        if pyenv_name != RECURVE_EXECUTOR_PYENV_NAME:
            requirements += "\nrecurvedata-lib[slim]"
        if not requirements:
            return
            
        logger.info("installing requirements")
        
        # Install recurvedata-lib from local package if it's a new virtualenv
        if pyenv_name != RECURVE_EXECUTOR_PYENV_NAME:
            python = CONF.PYENV_PYTHON_PATH.format(pyenv=pyenv_name)
            output, ret_code = robust_run_subprocess(
                f"{python} -m pip install -v --no-index --find-links={PY_PACKAGES_PATH} recurvedata-lib[slim]".split(),
                _logger=logger
            )
            if ret_code:
                raise RuntimeError(f"Failed to install recurvedata-lib:\n{output}")
        
        # Install user requirements
        with NamedTemporaryFile(mode="w+t", prefix="recurve_python_requirements_", suffix=".txt") as requirements_path:
            requirements_path.write(requirements)
            requirements_path.flush()
            python = CONF.PYENV_PYTHON_PATH.format(pyenv=pyenv_name)
            
            # Use robust_run_subprocess to capture output
            output, ret_code = robust_run_subprocess(
                f"{python} -m pip install -r {requirements_path.name}".split(),
                _logger=logger
            )
            
            if ret_code:
                raise RuntimeError(f"Failed to install requirements:\n{output}")

    @staticmethod
    def _execute_python_code(python_code: str, conn_config: Dict[str, Any], project_id: int) -> None:
        """
        Execute Python code using the exact same logic as PythonOperator.
        
        This reuses the execution logic from PythonTask.__run_python.
        """
        pyenv = conn_config["pyenv"]
        
        # Create temporary file for the Python code (same pattern as PythonTask)
        prefix = f"recurve_python_validation_{project_id}_"
        with NamedTemporaryFile(mode="w+t", prefix=prefix, suffix=".py") as tmp_file:
            tmp_file.write(python_code)
            tmp_file.flush()
            
            logger.info(f"Executing Python code in environment {pyenv}")
            logger.debug(f"Code to execute:\n{python_code}")
            
            # Reuse the exact same execution logic as PythonTask.__run_python
            script_path = os.path.abspath(tmp_file.name)
            python_path = CONF.PYENV_PYTHON_PATH.format(pyenv=pyenv)
            os_env = os.environ.copy()
            
            output, ret_code = robust_run_subprocess([python_path, script_path], env=os_env, _logger=logger)
            
            if ret_code:
                raise RuntimeError(f"Python Operator Error:\n{output}")  # Same error message as PythonTask
                
            logger.info("Python script executed successfully")

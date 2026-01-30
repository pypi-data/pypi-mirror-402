import ast
import logging
import os
from tempfile import NamedTemporaryFile

from recurvedata.config import PY_PACKAGES_PATH, RECURVE_EXECUTOR_PYENV_NAME
from recurvedata.core.translation import _l
from recurvedata.operators.config import CONF
from recurvedata.operators.operator import BaseOperator
from recurvedata.operators.task import BaseTask
from recurvedata.utils.mp import robust_run_subprocess, run_subprocess

logger = logging.getLogger(__name__)

DEFAULT_PY_VERSION = os.environ.get("RECURVE_OPERATOR_PYTHON_DEFAULT_VERSION", "3.11.9")


class PythonRequirementsMixin:
    @staticmethod
    def _install_requirements(requirements: str, pyenv_name: str):
        if pyenv_name != RECURVE_EXECUTOR_PYENV_NAME:
            requirements += "\nrecurvedata-lib[slim]"
        if not requirements:
            return
        logger.info("installing requirements")
        # Install recurvedata-lib from local package if it's a new virtualenv
        if pyenv_name != RECURVE_EXECUTOR_PYENV_NAME:
            python = CONF.PYENV_PYTHON_PATH.format(pyenv=pyenv_name)
            run_subprocess(
                f"{python} -m pip install -v --no-index --find-links={PY_PACKAGES_PATH} recurvedata-lib[slim]".split()
            )
        with NamedTemporaryFile(mode="w+t", prefix="recurve_python_requirements_", suffix=".txt") as requirements_path:
            requirements_path.write(requirements)
            requirements_path.flush()
            python = CONF.PYENV_PYTHON_PATH.format(pyenv=pyenv_name)
            run_subprocess(f"{python} -m pip install -r {requirements_path.name}".split())


class PythonTask(BaseTask, PythonRequirementsMixin):
    ds_name_fields = ("python_env",)

    @classmethod
    def config_schema(cls) -> dict:
        return {
            "type": "object",
            "properties": {
                "python_env": {
                    "type": "string",
                    "title": _l("Python Env"),
                    "description": _l(
                        "Python virtual environment name that will be created and can be shared between tasks"
                    ),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": [
                            "python",
                        ]
                    },
                },
                "code": {
                    "type": "string",
                    "title": _l("Code"),
                    "description": _l(
                        "Python code that will be executed. Supports Jinja templating for dynamic code generation and variable substitution."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "python",
                    },
                },
            },
            "required": ["python_env", "code"],
        }

    def __custom_os_env(self) -> dict:
        custom_env = os.environ.copy()
        return custom_env

    def __run_python(self, filename: str, pyenv: str, os_env: dict):
        script_path = os.path.abspath(filename)
        python = CONF.PYENV_PYTHON_PATH.format(pyenv=pyenv)
        output, ret_code = robust_run_subprocess([python, script_path], env=os_env, _logger=logger)
        if ret_code:
            raise RuntimeError(f"Python Operator Error:\n{output}")

    def _prepare_env(self, python_config: dict):
        pyenv_name: str = python_config.get("pyenv")
        py_version: str = python_config.get("python_version", DEFAULT_PY_VERSION)
        self._install_virtualenv(py_version, pyenv_name)
        self._install_requirements(python_config.get("requirements", ""), pyenv_name)

    @staticmethod
    def _install_virtualenv(py_version: str, pyenv_name: str):
        python_path: str = CONF.PYENV_PYTHON_PATH.format(pyenv=pyenv_name)
        if os.path.exists(python_path):
            return
        run_subprocess(["pyenv", "virtualenv", py_version, pyenv_name])

    def execute_impl(self, *args, **kwargs):
        config = self.rendered_config
        code = config.code
        os_env = self.__custom_os_env()

        conn_config: dict = self.get_connection_by_name(config.python_env).extra
        self._prepare_env(conn_config)
        pyenv = conn_config["pyenv"]
        prefix = f"recurve_python_{self.dag.id}_{self.node.id}_"
        with NamedTemporaryFile(mode="w+t", prefix=prefix, suffix=".py") as tmp_file:
            tmp_file.write(code)
            tmp_file.flush()
            logger.info(code)
            self.__run_python(tmp_file.name, pyenv, os_env)


class PythonOperator(BaseOperator):
    task_cls = PythonTask

    @classmethod
    def validate(cls, configuration) -> dict:
        res = super().validate(configuration)
        # syntax_error = cls._get_python_code_syntax_error(res['code'])
        # if syntax_error:
        #     raise jsonschema.ValidationError(f'Python Syntax Error {syntax_error}')
        return res

    @staticmethod
    def _get_python_code_syntax_error(code):
        try:
            ast.parse(code)
        except SyntaxError as e:
            return e

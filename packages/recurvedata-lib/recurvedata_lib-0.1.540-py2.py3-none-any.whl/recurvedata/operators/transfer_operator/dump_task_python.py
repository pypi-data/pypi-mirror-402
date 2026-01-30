import copy
import inspect
import logging
import re

import jsonschema

from recurvedata.config import RECURVE_EXECUTOR_PYENV_NAME
from recurvedata.core.translation import _l
from recurvedata.operators.python_operator.operator import PythonRequirementsMixin
from recurvedata.operators.transfer_operator.mixin import HiveTextfileConverterMixin
from recurvedata.operators.transfer_operator.task import DumpTask

logger = logging.getLogger(__name__)

_SOURCE_SKELETON = _l(
    '''
def execute(filename: str, *args, **kwargs):
    """
    The execute function must be implemented as the entry point for ReOrc.

    Args:
        filename: Required. Output data to this file in CSV format. This file will be used as input for the Loader.

    Data Source Parameters:
        For database configurations, use ReOrc's Data Sources instead of hardcoding credentials in the code.
        When defining the execute function, use special parameter names to specify required data sources.
        ReOrc will pass corresponding pigeon connector objects that can be used for database interactions.

        Parameter naming convention:
        - Must have 'datasource_' prefix, e.g. datasource_xxx
        - Example: datasource_mysql='my_mysql_default'
          At runtime, ReOrc will pass a pigeon.connector.MysqlConnector object

        Example usage:
            def execute(filename, datasource_mysql='my_mysql_default'):
                df = datasource_mysql.get_pandas_df('SELECT * FROM my_database.my_table')
                df.to_csv(filename, header=False)
    """
    pass
'''
)


# FIXME: record all supported template variables, find a way to keep consistent with `get_template_context` method
_TEMPLATE_VARIABLES = {
    "dt",
    "yesterday",
    "yesterday_dt",
    "tomorrow",
    "tomorrow_dt",
    "logical_date",
    "data_interval_start",
    "data_interval_end",
    "data_interval_start_dt",
    "data_interval_end_dt",
}


class PythonCodeRunner(object):
    # test page: https://regex101.com/r/p8YCQc/1
    _JINJA2_VAR_PATTERN = re.compile(r"^{{\s*([^\d\W]\w*)\s*}}$")

    def __init__(self, source):
        self.source = source

        self.__namespace = {}
        self.__parameters = {}
        self.__datasource_params = {}
        self.__jinja2_variables_params = {}
        self.__ready_for_execution = False
        self.__compiled = False

    @property
    def entrypoint(self):
        if not self.__compiled:
            raise ValueError("entrypoint is not ready, inspect first")
        return self.__namespace.get("execute")

    def inspect(self):
        logger.info("compiling source code\n%s", self.source)
        code = compile(self.source, "", "exec")
        exec(code, self.__namespace)
        self.__compiled = True
        entrypoint = self.entrypoint

        if not (entrypoint and inspect.isfunction(entrypoint)):
            raise jsonschema.ValidationError(message="execute function is required", path=("source",))

        sig = inspect.signature(entrypoint)
        for name, param in sig.parameters.items():
            value = param.default
            logger.info("found parameter %s=%s", name, value)

            # special naming for data source parameters: `datasource_xxx`
            if self.is_datasource_param(name):
                if self._is_empty(value):
                    raise jsonschema.ValidationError(message=f"{name} must be known data source name", path=("source",))
                ds = DumpTask.get_connection_by_name(value)
                if not ds:
                    raise jsonschema.ValidationError(message=f"Unknown data source {repr(name)}", path=("source",))
                self.__datasource_params[name] = value

            # jinja2 template `{{ dt }}`, no Jinja2 rendering, directly replace
            elif self.is_jinja2_variable(value):
                variable = self._JINJA2_VAR_PATTERN.search(value).groups()[0]
                # unsupported variables
                if variable not in _TEMPLATE_VARIABLES:
                    raise jsonschema.ValidationError(
                        message=f"Unsupport template variable {repr(value)}", path=("source",)
                    )
                self.__jinja2_variables_params[name] = variable

            else:
                # keep default value, data source and template variable parameters are injected at runtime by calling `bind_parameters`
                self.__parameters[name] = value
        self.__parameters.update(self.__datasource_params)
        self.__parameters.update(self.__jinja2_variables_params)

    def is_datasource_param(self, name: str) -> bool:
        return name.startswith("datasource_")

    def is_jinja2_variable(self, name: str) -> bool:
        return isinstance(name, str) and self._JINJA2_VAR_PATTERN.match(name)

    @staticmethod
    def _is_empty(obj) -> bool:
        return obj is inspect.Signature.empty

    def bind_parameters(self, filename, template_context, **kwargs):
        params = copy.deepcopy(kwargs)
        params["filename"] = filename

        logger.info("binding data source connectors %s", self.__datasource_params)
        for param_name, ds_name in self.__datasource_params.items():
            params[param_name] = DumpTask.get_connection_by_name(ds_name).connector

        logger.info("binding jinja2 variables %s", self.__jinja2_variables_params)
        for param_name, variable in self.__jinja2_variables_params.items():
            params[param_name] = template_context[variable]

        # bind other parameters, or override default parameters
        for k, v in params.items():
            if k in self.__parameters:
                self.__parameters[k] = v

        # check if there are any parameters not passed
        for name, value in self.__parameters.items():
            if name not in ["args", "kwargs"] and self._is_empty(value):
                raise TypeError(f"parameter {repr(name)} is not bound")

        logger.info("bounded parameters %s", self.__parameters)
        self.__ready_for_execution = True

    def execute(self):
        if not self.__ready_for_execution:
            raise RuntimeError("must call inspect and bind_parameters before calling execute")
        logger.info("calling entrypoint %s with parameters %s...", self.entrypoint, self.__parameters)
        self.entrypoint(**self.__parameters)
        logger.info("done.")


class PythonDumpTask(DumpTask, HiveTextfileConverterMixin, PythonRequirementsMixin):
    # no_template_fields = ("source",)

    def execute_impl(self, *args, **kwargs):
        config = self.rendered_config.copy()
        runner = PythonCodeRunner(config["source"])

        # Get and install requirements if any
        py_conn_configs = self.client.get_py_conn_configs()
        if py_conn_configs and isinstance(py_conn_configs, dict):
            requirements = "\n".join(py_conn_configs.get("requirements", []))
            self._install_requirements(requirements, RECURVE_EXECUTOR_PYENV_NAME)

        runner.inspect()
        context = self.get_template_context()
        runner.bind_parameters(filename=self.filename, template_context=context)
        runner.execute()

        self.convert_csv_to_hive_text_if_needed()
        return None

    @classmethod
    def config_schema(cls):
        return {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "title": _l("Python Source Code"),
                    "description": _l(
                        "Python code that extracts data and writes to a CSV file. Must implement an execute() function that takes a filename parameter. Note: The Load step must specify a Create Table DDL when using PythonDump."
                    ),
                    "default": _SOURCE_SKELETON,
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "python",
                    },
                },
            },
            "required": ["source"],
        }

    @classmethod
    def validate(cls, configuration):
        config = super().validate(configuration)

        runner = PythonCodeRunner(config["source"])
        runner.inspect()
        return config

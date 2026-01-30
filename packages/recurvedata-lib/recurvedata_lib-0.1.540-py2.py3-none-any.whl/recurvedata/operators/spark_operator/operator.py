import json
import logging
import os
from functools import lru_cache
from importlib import resources
from subprocess import PIPE, STDOUT, Popen
from tempfile import NamedTemporaryFile
from textwrap import dedent

from recurvedata.core.translation import _l
from recurvedata.operators.operator import BaseOperator
from recurvedata.operators.task import BaseTask

logger = logging.getLogger(__name__)


@lru_cache()
def get_sample_code():
    return resources.files("recurvedata.operators.spark_operator").joinpath("spark_sample.py").read_text()


class SparkTask(BaseTask):
    @classmethod
    def config_schema(cls):
        return {
            "type": "object",
            "properties": {
                "spark_source": {
                    "type": "string",
                    "title": _l("Spark Environment"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": [
                            "spark",
                        ],
                    },
                    "description": _l("Select the Spark environment and version to use for this task"),
                },
                "env": {
                    "type": "string",
                    "title": _l("Environment Variables"),
                    "default": "{}",
                    "description": _l(
                        'Additional environment variables in JSON format (e.g. {"HADOOP_CONF_DIR": "/etc/hadoop/conf"})'
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "json",
                    },
                },
                "execution_config": {
                    "type": "string",
                    "title": _l("Spark Configuration"),
                    "default": dedent(
                        """\
                        {
                            "master": "yarn",
                            "executor-memory": "4g",
                            "num-executors": "10",
                            "executor-cores": "2",
                            "queue": "default",
                            "conf": {
                                "spark.dynamicAllocation.enabled": "False"
                            }
                        }
                    """
                    ),
                    "description": _l(
                        "Spark execution parameters and configurations. See "
                        "<a target='_blank' href='https://spark.apache.org/docs/latest/configuration.html'>"
                        "Spark Docs</a> for available options"
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "json",
                    },
                },
                "code": {
                    "type": "string",
                    "title": _l("Spark Code"),
                    "default": get_sample_code(),
                    "description": _l(
                        "PySpark code to execute. The default template shows how to create a SparkSession "
                        "(Spark 2.3+). Supports Jinja templating for dynamic code generation."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "python",
                    },
                },
            },
            "required": ["spark_source", "env", "execution_config", "code"],
        }

    def __create_env(self, source_env, extra_env):
        env = os.environ.copy()
        env.update(source_env)
        env.update(extra_env)
        return env

    def __create_bash_command(self, script_path, submitter, execution_config, source_conf: dict):
        execution_conf_list = []
        conf_names = []
        for k, v in execution_config.items():
            if k == "conf":
                for k2, v2 in v.items():
                    execution_conf_list.append(f"--conf {k2}={v2}")
                    conf_names.append(k2)
            else:
                execution_conf_list.append(f"--{k} {v}")
        for k, v in source_conf.items():
            if k in conf_names:
                continue
            execution_conf_list.append(f"--conf {k}={v}")
        execution_conf_str = " ".join(execution_conf_list)
        bash_command = submitter + " " + execution_conf_str + " " + script_path
        return bash_command

    def __execute_command(self, bash_command, env):
        logger.info("Running command: %s", bash_command)
        sub_process = Popen(["bash", "-c", bash_command], stdout=PIPE, stderr=STDOUT, env=env)
        logger.info("Output:")
        for raw_line in iter(sub_process.stdout.readline, b""):
            line = raw_line.decode("utf8").rstrip()
            logger.info(line)
        sub_process.wait()
        logger.info("Node exited with return code %s", sub_process.returncode)
        if sub_process.returncode:
            raise Exception("Spark node failed")

    @classmethod
    def __filter_empty_value_in_dict(cls, dct: dict):
        if not dct:
            return dct
        return {k: v for (k, v) in dct.items() if (v is not None and v != "" and v != {})}

    @classmethod
    def _merge_dict(cls, priority_dct: dict, other_dct: dict):
        """
        Filter out empty values
        """
        if not (other_dct and priority_dct):
            return priority_dct or other_dct
        result_dct = {}
        for key in set(list(priority_dct.keys()) + list(other_dct.keys())):
            if key not in priority_dct:
                result_dct[key] = other_dct[key]
                continue
            if key not in other_dct:
                result_dct[key] = priority_dct[key]
                continue
            if isinstance(priority_dct[key], dict) and isinstance(other_dct, dict):
                result_dct[key] = cls._merge_dict(priority_dct[key], other_dct[key])
                continue
            result_dct[key] = priority_dct[key]
        return result_dct

    def __excute_spark_code(self, config):
        spark_source = self.must_get_connection_by_name(config.spark_source)
        submitter = spark_source.extra.get("submitter")
        source_conf = spark_source.extra.get("conf", {})
        source_env = self.__filter_empty_value_in_dict(
            spark_source.extra.get("env")
        )  # Some empty values may be saved when saving on the page
        execution_config = self._merge_dict(
            self.__filter_empty_value_in_dict(json.loads(config.execution_config)),
            self.__filter_empty_value_in_dict(spark_source.extra.get("execution_config")),
        )
        extra_env = json.loads(config.env)  # User input, don't filter empty values
        code = config.code

        prefix = f"recurve_pyspark_{self.dag.dag_id}_{self.node.id}_"
        with NamedTemporaryFile(mode="w+t", prefix=prefix, suffix=".py") as tmp_file:
            tmp_file.write(code)
            tmp_file.flush()
            logger.info(code)
            script_path = os.path.abspath(tmp_file.name)
            bash_command = self.__create_bash_command(script_path, submitter, execution_config, source_conf)
            env = self.__create_env(source_env, extra_env)
            self.__execute_command(bash_command, env)

    def execute_impl(self, *args, **kwargs):
        config = self.rendered_config
        self.__excute_spark_code(config)
        return None


class SparkOperator(BaseOperator):
    task_cls = SparkTask

    @classmethod
    def validate(cls, configuration):
        config = super().validate(configuration)
        # execution_config = json.loads(config['execution_config'])
        # if execution_config['master'] != 'yarn':
        #     raise jsonschema.ValidationError(message='master should be yarn')
        return config

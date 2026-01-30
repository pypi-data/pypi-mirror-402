import argparse
import os
import re
import shlex
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Generator, Optional, Self
from unittest.mock import MagicMock

from recurvedata.dbt.consts import (
    DBT_BIN_PATH,
    DBT_PROFILE_KEY,
    DEFAULT_MATERIALIZED,
    DbtFileNames,
    format_dbt_project_yml_path,
    format_profiles_path,
)
from recurvedata.dbt.schemas import DbtGraph, DbtOperatorNode, SingleModelLineage
from recurvedata.dbt.utils import (
    VariableJSONEncoder,
    ensure_manifest_json_exists,
    extract_project_name,
    run_deps_if_necessary,
)


def _mock_cosmos_airflow():
    """
    cosmos will import airflow internally,
    in CP we don't have airflow environ.
    Airflow use sqlalchemy 1.4, will have some conflict with CP env.
    """
    airflow_mock = MagicMock()

    airflow_mock.version = "2.9"
    airflow_mock.DAG = dict
    airflow_mock.TaskGroup = dict
    airflow_mock.BaseOperator = dict
    sys.modules["airflow"] = airflow_mock
    sys.modules["airflow.models"] = airflow_mock
    sys.modules["airflow.models.dag"] = airflow_mock
    sys.modules["airflow.models.baseoperator"] = airflow_mock
    sys.modules["airflow.models.taskinstance"] = airflow_mock
    sys.modules["airflow.utils"] = airflow_mock
    sys.modules["airflow.utils.task_group"] = airflow_mock
    sys.modules["airflow.utils.strings"] = airflow_mock
    sys.modules["airflow.utils.session"] = airflow_mock
    sys.modules["airflow.utils.operator_helpers"] = airflow_mock
    sys.modules["airflow.utils.context"] = airflow_mock
    sys.modules["airflow.version"] = airflow_mock
    sys.modules["airflow.hooks"] = airflow_mock
    sys.modules["airflow.hooks.base"] = airflow_mock
    sys.modules["airflow.exceptions"] = airflow_mock
    sys.modules["airflow.configuration"] = airflow_mock
    sys.modules["airflow.io"] = airflow_mock
    sys.modules["airflow.io.path"] = airflow_mock


try:
    import airflow.models  # noqa
except ImportError:
    _mock_cosmos_airflow()

try:
    from cosmos import ExecutionConfig, ProfileConfig, ProjectConfig, RenderConfig, settings
    from cosmos.dbt.graph import DbtGraph as CosmosDbtGraph
    from cosmos.dbt.graph import DbtNode as CosmosDbtNode
except ImportError:
    CosmosDbtGraph = None
    CosmosDbtNode = None


class NodeType(str, Enum):
    TEST = "test"
    MODEL = "model"


@dataclass
class ParsedModel:
    model_name: str
    project_name: str
    materialized: str

    @classmethod
    def is_test_node(cls, node: "CosmosDbtNode") -> bool:
        node_id = node.unique_id
        tmp_lst = node_id.split(".")
        node_type = tmp_lst[0]
        return node_type == NodeType.TEST

    @classmethod
    def extract_node_model_id(cls, node: "CosmosDbtNode") -> int | None:
        if cls.is_test_node(node):
            # todo: singular test not supported(not in model_properties.yml)
            model_properties_filename: str = node.file_path.name
            pat = re.compile(r"^model_(?P<model_id>\d+)_properties.yml")
            mobj = pat.match(model_properties_filename)
            return mobj and int(mobj.group("model_id"))
        else:
            # tags rely on CP generation
            pat = re.compile(r"^model_(?P<model_id>\d+)$")
            for tag in node.tags:
                mobj = pat.match(tag)
                if mobj:
                    return int(mobj.group("model_id"))

    @classmethod
    def from_cosmos_node(cls, node: "CosmosDbtNode") -> Optional[Self]:
        node_id = node.unique_id
        tmp_lst = node_id.split(".")
        node_type = tmp_lst[0]
        if node_type != NodeType.MODEL:
            return
        project_name = tmp_lst[1]
        model_name = ".".join(tmp_lst[2:])
        return cls(
            model_name=model_name,
            project_name=project_name,
            materialized=node.config.get("materialized", DEFAULT_MATERIALIZED),
        )

    def to_node_config(self) -> dict:
        return {
            "source": {
                "entity_name": self.model_name,
                "materialized": self.materialized,
            }
        }

    def is_current_project(self, current_project_name):
        return self.project_name == current_project_name


def _extract_select_from_command(command: str) -> list[str]:
    """
    extract --select content from user input command
    """

    parser = argparse.ArgumentParser(description="Parse dbt build command")
    parser.add_argument("-s", "--select", nargs="+")

    args = shlex.split(command)

    if len(args) > 2:  # omit `recurve build`
        args = args[2:]

    parsed_args, unknown = parser.parse_known_args(args)
    return parsed_args.select


def _prepare_os_env():
    # todo(chenjingmeng): move to connectors
    os.environ["DBT_USER"] = ""
    os.environ["DBT_PASSWORD"] = ""


def _construct_cosmos_dag_graph(
    dbt_project_dir: str, dbt_profiles_path: str, dbt_project_yml_path: str, select: list[str], variables: dict
) -> "CosmosDbtGraph":
    _prepare_os_env()
    settings.enable_cache = False

    render_config = RenderConfig(select=select, dbt_project_path=dbt_project_dir, dbt_deps=False)

    profile_config = ProfileConfig(
        profile_name=DBT_PROFILE_KEY,
        target_name="dev",  # when extract model, it always using dev as env
        profiles_yml_filepath=dbt_profiles_path,
    )

    project_config = ProjectConfig(
        dbt_project_path=dbt_project_dir,
        project_name=extract_project_name(dbt_project_yml_path),
        dbt_vars={k: VariableJSONEncoder.format_var(v) for k, v in variables.items()} if variables else None,
    )
    project_config.manifest_path = Path(dbt_project_dir) / "target" / DbtFileNames.MANIFEST_FILE.value
    execution_config = ExecutionConfig(
        dbt_executable_path=DBT_BIN_PATH,
        dbt_project_path=dbt_project_dir,
    )

    dbt_graph = CosmosDbtGraph(
        project=project_config,
        execution_config=execution_config,
        profile_config=profile_config,
        render_config=render_config,
    )
    return dbt_graph


def extract_graph(
    dbt_project_dir: str, models: list[str] = None, model_cmd: str = None, variables: dict = None
) -> DbtGraph:
    """
    extract the models and model graph from model pipeline settings
    :param models: the models selected in the drop down list
    :param model_cmd: the command from the advanced mode
    """
    if models:
        select = models
    else:
        select = _extract_select_from_command(model_cmd)

    if variables:
        variables: dict[str, str] = {k: VariableJSONEncoder.format_var(v) for (k, v) in variables.items()}

    dbt_project_dir = os.path.abspath(os.path.expanduser(dbt_project_dir))
    run_deps_if_necessary(dbt_project_dir)
    ensure_manifest_json_exists(dbt_project_dir)

    dbt_profiles_path = format_profiles_path(dbt_project_dir)
    project_yml_path = format_dbt_project_yml_path(dbt_project_dir)

    cosmos_graph = _construct_cosmos_dag_graph(dbt_project_dir, dbt_profiles_path, project_yml_path, select, variables)
    cosmos_graph.load()

    return _cosmos_graph_2_dbt_graph(cosmos_graph)


def _cosmos_graph_2_dbt_graph(cosmos_graph: CosmosDbtGraph) -> DbtGraph:
    # todo: forbid circular dependency
    graph: list[SingleModelLineage] = []
    extracted_models: list[str] = []
    nodes: list[DbtOperatorNode] = []
    project_name = cosmos_graph.project.project_name
    cross_model_test_dependency: dict[int, set[str]] = {}  # {model_id: depends_on_node_ids}
    for node in cosmos_graph.filtered_nodes.values():
        if not ParsedModel.is_test_node(node):
            continue
        if not (node.depends_on and len(node.depends_on) > 1):
            continue
        model_id = ParsedModel.extract_node_model_id(node)
        if model_id is None:
            # singular test
            continue
        if model_id not in cross_model_test_dependency:
            cross_model_test_dependency[model_id] = set()
        for upstream_node_id in node.depends_on:
            # upstream_node_id maybe current model node_id, not filtered here
            cross_model_test_dependency[model_id].add(upstream_node_id)

    for node_id, node in cosmos_graph.filtered_nodes.items():
        if ParsedModel.is_test_node(node):
            continue
        parsed_model = ParsedModel.from_cosmos_node(node)
        if not parsed_model:
            continue
        # todo(chenjingmeng): support package/dependency
        if not parsed_model.is_current_project(project_name):
            continue
        extracted_models.append(parsed_model.model_name)
        nodes.append(DbtOperatorNode(model_name=parsed_model.model_name, config=parsed_model.to_node_config()))

        node_model_id = ParsedModel.extract_node_model_id(node)
        upstream_node_ids = _dedup_list(node.depends_on + list(cross_model_test_dependency.get(node_model_id, set())))
        for upstream_node_id in upstream_node_ids:
            if upstream_node_id == node_id:
                continue
            upstream_node = cosmos_graph.filtered_nodes.get(upstream_node_id)
            if upstream_node is None:
                continue
            upstream_parsed = ParsedModel.from_cosmos_node(upstream_node)
            if upstream_parsed.is_current_project(project_name):
                graph.append(
                    SingleModelLineage(
                        upstream_model_name=upstream_parsed.model_name, downstream_model_name=parsed_model.model_name
                    )
                )
    return DbtGraph(model_names=extracted_models, graph=graph, nodes=nodes)


def _dedup_list(lst: list | Generator) -> list:
    return list(set(lst))

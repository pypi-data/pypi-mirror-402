import os
import shutil
import sys
from dataclasses import dataclass
from enum import Enum

from recurvedata.config import RECURVE_DBT_HOME

DBT_BIN_PATH = shutil.which("dbt") or os.path.join(os.path.dirname(sys.executable), "dbt")
DBT_PROFILE_KEY = "profile"

DEFAULT_MATERIALIZED = "view"


class DbtFileNames(str, Enum):
    PACKAGES_FILE = "packages.yml"
    PACKAGE_LOCK_FILE = "package-lock.yml"
    DBT_PROJECT_YML_FILE = "dbt_project.yml"
    PROFILES_FILE = "profiles.yml"
    MANIFEST_FILE = "manifest.json"
    DEPS_PACKAGE_DIR = "dbt_packages"


@dataclass
class DbtPath:
    project_id: int
    env_id: int
    base_path: str = RECURVE_DBT_HOME
    pipeline_id: int = None

    @property
    def project_gzip_file(self) -> str:
        return f"{self.project_dir}.tar.gz"

    @property
    def project_dir(self) -> str:
        return os.path.join(self.base_path, self.simple_project_dir)

    @property
    def simple_project_dir(self) -> str:
        if self.pipeline_id:
            return f"project_{self.project_id}_env_{self.env_id}_pipeline_{self.pipeline_id}"
        return f"project_{self.project_id}_env_{self.env_id}"

    @property
    def profiles_path(self) -> str:
        return format_profiles_path(self.project_dir)

    @property
    def dbt_project_yml_path(self) -> str:
        return format_dbt_project_yml_path(self.project_dir)

    @property
    def project_name(self) -> str:
        return f"project_{self.project_id}"

    def get_model_compiled_sql_path(self, model_name: str) -> str:
        return os.path.join(self.project_dir, "target", "compiled", self.project_name, "models", model_name + ".sql")

    def get_model_run_sql_path(self, model_name: str) -> str:
        return os.path.join(self.project_dir, "target", "run", self.project_name, "models", model_name + ".sql")

    def get_model_sql_path(self, model_name: str) -> str:
        return os.path.join(self.project_dir, "models", model_name + ".sql")


def format_profiles_path(project_dir: str) -> str:
    return os.path.join(project_dir, "profiles.yml")


def format_dbt_project_yml_path(project_dir: str) -> str:
    return os.path.join(project_dir, "dbt_project.yml")


def format_packages_yml_path(project_dir: str) -> str:
    return os.path.join(project_dir, "packages.yml")


def format_package_lock_path(project_dir: str) -> str:
    return os.path.join(project_dir, "package-lock.yml")


def format_installed_packages_path(project_dir: str) -> str:
    return os.path.join(project_dir, "dbt_packages")


class DbtMaterialization(str, Enum):
    VIEW = "view"
    TABLE = "table"
    EPHEMERAL = "ephemeral"
    INCREMENTAL = "incremental"


OVERWRITE_DIRECTORIES = [
    "macros",
    "models",
    "tests",
]
OVERWRITE_FILES = ["dbt_project.yml", "profiles.yml", "packages.yml"]

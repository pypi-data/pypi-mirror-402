import base64
import json
import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, get_origin

from pydantic import BaseModel, ConfigDict, Field, SecretStr
from typing_extensions import Self

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo

RECURVE_HOME = Path(os.environ.get("RECURVE_HOME", Path.home() / ".recurve"))
CONFIG_FILE_PATH = RECURVE_HOME / "config.json"

EXECUTOR_RECURVE_HOME = Path(os.environ.get("RECURVE__WORKER__BASE", "/opt/recurve"))
RECURVE_DBT_HOME = EXECUTOR_RECURVE_HOME / "dbt"
EXECUTOR_META_PATH = EXECUTOR_RECURVE_HOME / "meta"
EXECUTOR_WORKER_DATA_PATH = EXECUTOR_RECURVE_HOME / "worker_data"
SERVER_RESULT_STAGING_PATH = EXECUTOR_RECURVE_HOME / "server" / "staging"

PYENV_HOME = Path(os.environ.get("RECURVE__WORKER__PYENV__BASE", "/opt/pyenv"))
RECURVE_EXECUTOR_PYENV_NAME = "recurve_executor"
RECURVE_DBT_PYENV_NAME = "dbt"
RECURVE_EXECUTOR_CLI_NAME = "recurve_executor"
RECURVE_EXECUTOR_CLI = PYENV_HOME / "versions" / RECURVE_EXECUTOR_PYENV_NAME / "bin" / RECURVE_EXECUTOR_CLI_NAME
RECURVE_EXECUTOR_DBT_CLI = PYENV_HOME / "versions" / RECURVE_DBT_PYENV_NAME / "bin" / RECURVE_EXECUTOR_CLI_NAME

REDIS_LOCK_URL: str = os.environ.get("RECURVE__REDIS_LOCK_URL", "redis://localhost:6381/1")
REDIS_CACHE_URL: str = os.environ.get("RECURVE__REDIS_CACHE_URL", "redis://localhost:6381/2")
PY_PACKAGES_PATH: str = "/opt/reorc_packages"


class AgentConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    editable_fields: ClassVar[set[str]] = {
        "token",
        "request_timeout",
    }

    agent_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="The unique identifier of the agent.")
    server_host: str = Field(..., description="The hostname of the server.")
    tenant_domain: str = Field(..., description="The domain of the tenant.")
    token: SecretStr = Field(..., description="The authentication token.")
    request_timeout: int = Field(5, description="The timeout in seconds for HTTP requests.")

    def is_valid(self) -> bool:
        return all((self.token.get_secret_value(), self.server_host, self.tenant_domain))

    @property
    def server_url(self) -> str:
        if self.server_host.startswith("http"):
            return self.server_host
        return f"https://{self.server_host}"

    def set_auth_token(self, encoded_token: str):
        decoded = base64.urlsafe_b64decode(encoded_token.encode()).split(b"::")
        self.tenant_domain = decoded[0].decode()
        self.server_host = decoded[1].decode()
        self.token = SecretStr(base64.urlsafe_b64encode(decoded[2]).decode())

    def clear_auth_token(self):
        self.token = SecretStr("")

    @classmethod
    def load(cls, filename: Path | str | None = None) -> Self:
        if filename is None:
            filename = CONFIG_FILE_PATH
        filename = Path(filename)
        if not filename.exists():
            cfg = cls(server_host="", tenant_domain="", token="")
            cfg.save(filename)
        with open(filename) as f:
            content = f.read()
            return cls.model_validate_json(content)

    def save(self, filename: Path | None = None):
        if filename is None:
            filename = CONFIG_FILE_PATH

        filename.parent.mkdir(parents=True, exist_ok=True)
        with open(filename, "w") as f:
            content: dict = self.model_dump(mode="json")
            content["token"] = self.token.get_secret_value()
            f.write(json.dumps(content, indent=2))
            f.write("\n")


def parse_value(key: str, value: str) -> Any:
    field_info: "FieldInfo" = AgentConfig.model_fields[key]
    field_type = get_origin(field_info.annotation) or field_info.annotation
    if field_type is SecretStr:
        return SecretStr(value)
    if field_type is bool:
        return value.lower() in {"true", "yes", "y", "1"}
    return field_type(value)


CONFIG: AgentConfig = AgentConfig.load()

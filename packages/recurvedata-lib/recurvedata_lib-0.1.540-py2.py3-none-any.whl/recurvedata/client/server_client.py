import logging
import os
from typing import TYPE_CHECKING, Any

from recurvedata.client.client import Client, ResponseModelType
from recurvedata.config import AgentConfig
from recurvedata.exceptions import APIError

if TYPE_CHECKING:
    from recurvedata.dbt.schemas import CompileResponseWithError, PreviewResponseWithError

logger = logging.getLogger(__name__)


class ServerDbtClient(Client):
    def __init__(
        self,
        server_host: str = os.environ.get("RECURVE__DPSERVER__HOST", "http://0.0.0.0:25103"),
        request_timeout: int = 60,
    ):
        config = AgentConfig.load()
        config.server_host = server_host
        config.request_timeout = request_timeout
        super().__init__(config)

    def prepare_header(self, kwargs: dict):
        pass

    def compile(
        self, project_id: int, sql: str, alias: str, force_regenerate_dir: bool = False
    ) -> "CompileResponseWithError":
        from recurvedata.dbt.schemas import CompilePayload, CompileResponseWithError

        payload = CompilePayload(
            project_id=project_id,
            sql=sql,
            alias=alias,
            force_regenerate_dir=force_regenerate_dir,
        )
        return self.request(
            "POST", path="/api/dbt/compile", json=payload.model_dump(), response_model_class=CompileResponseWithError
        )

    def preview(
        self,
        project_id: int,
        sql: str,
        alias: str,
        limit: int,
        force_regenerate_dir: bool = False,
        is_compiled: bool = False,
    ) -> "PreviewResponseWithError":
        from recurvedata.dbt.schemas import PreviewPayload, PreviewResponseWithError

        payload = PreviewPayload(
            project_id=project_id,
            sql=sql,
            alias=alias,
            limit=limit,
            force_regenerate_dir=force_regenerate_dir,
            is_compiled=is_compiled,
        )
        return self.request(
            "POST", path="/api/dbt/preview", json=payload.model_dump(), response_model_class=PreviewResponseWithError
        )

    def request(
        self,
        method: str,
        path: str,
        response_model_class: type[ResponseModelType] | None = None,
        retries: int = 1,
        **kwargs,
    ) -> Any:
        """
        compared with super().request, this function has no retry logic,
        to avoid all exception type is MaxRetriesExceededException
        """
        self.prepare_header(kwargs)
        resp = self._client.request(method, path, **kwargs)
        resp.raise_for_status()
        resp_content = resp.json()

        if "code" in resp_content and resp_content["code"] != "0":
            raise APIError(f"API request failed: {resp_content['msg']}\n{resp_content.get('data')}")

        if response_model_class is not None:
            if "code" in resp_content:
                return response_model_class.model_validate(resp_content["data"])
            return response_model_class.model_validate(resp_content)
        return resp_content.get("data")

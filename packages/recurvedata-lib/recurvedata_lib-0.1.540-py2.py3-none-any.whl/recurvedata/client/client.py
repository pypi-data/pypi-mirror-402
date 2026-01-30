import json
import logging
import time
from typing import Any, TypeVar, overload

import httpx
from pydantic import BaseModel

from recurvedata.__version__ import __version__
from recurvedata.config import AgentConfig
from recurvedata.exceptions import APIError, MaxRetriesExceededException, UnauthorizedError

logger = logging.getLogger(__name__)

ResponseModelType = TypeVar("ResponseModelType", bound=BaseModel)


class Client:
    _config: AgentConfig
    _client: httpx.Client

    def __init__(self, config: AgentConfig = None):
        if not config:
            config = AgentConfig.load()
        self.set_config(config)

    def set_config(self, config: AgentConfig):
        self._config = config
        self._client = httpx.Client(
            base_url=config.server_url,
            timeout=config.request_timeout,
            headers={"User-Agent": f"RecurveLib/{__version__}"},
        )

    @overload
    def request(self, method: str, path: str, response_model_class: None = None, retries: int = 3, **kwargs) -> Any:
        ...

    @overload
    def request(
        self, method: str, path: str, response_model_class: type[ResponseModelType], retries: int = 3, **kwargs
    ) -> ResponseModelType:
        ...

    def prepare_header(self, kwargs: dict):
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._config.agent_id}:{self._config.token.get_secret_value()}"
        headers["X-Tenant-Domain"] = self._config.tenant_domain
        kwargs["headers"] = headers

    def request(
        self,
        method: str,
        path: str,
        response_model_class: type[ResponseModelType] | None = None,
        retries: int = 1,
        **kwargs,
    ) -> Any:
        self.prepare_header(kwargs)
        pre_err: httpx.HTTPStatusError | None = None
        for attempt in range(retries):
            try:
                resp = self._client.request(method, path, **kwargs)
                resp.raise_for_status()
                resp_content = resp.json()

                # TODO(yangliang): handle errors more gracefully
                if "code" in resp_content and resp_content["code"] != "0":
                    raise APIError(f"API request failed: {resp_content['msg']}\n{resp_content.get('data')}")

                if response_model_class is not None:
                    if "code" in resp_content:
                        return response_model_class.model_validate(resp_content["data"])
                    return response_model_class.model_validate(resp_content)
                return resp_content.get("data")
            except httpx.HTTPStatusError as e:
                pre_err = e
                logger.error(
                    f"HTTP error on attempt {attempt + 1} for url '{e.request.url}' :"
                    f" {e.response.status_code} - {e.response.text}"
                )
                if e.response.status_code == 401:
                    raise UnauthorizedError("Unauthorized, please check your agent_id and token")
            except httpx.RequestError as e:
                logger.debug(f"Request error on attempt {attempt + 1} for url '{e.request.url}': {e}")

            if attempt < retries - 1:
                time.sleep(2**attempt)  # Exponential backoff
            else:
                err_msg = str(pre_err) if pre_err else ""
                raise MaxRetriesExceededException(
                    f"Failed to complete {method} request to {path} after {retries} attempts, {err_msg}"
                )

    def request_file(
        self,
        method: str,
        path: str,
        file_name: str,
        retries: int = 1,
        **kwargs,
    ) -> bool:
        self.prepare_header(kwargs)

        pre_err: httpx.HTTPStatusError | None = None
        for attempt in range(retries):
            try:
                resp = self._client.request(method, path, **kwargs)
                resp.raise_for_status()
                try:
                    resp_content = resp.json()

                    if "code" in resp_content and resp_content["code"] != "0":
                        raise APIError(f"API request failed: {resp_content['msg']}\n{resp_content.get('data')}")
                except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
                    pass

                if not resp.content:
                    return False

                with open(file_name, "wb") as f:
                    f.write(resp.content)
                return True

                # TODO(yangliang): handle errors more gracefully
            except httpx.HTTPStatusError as e:
                logger.debug(
                    f"HTTP error on attempt {attempt + 1} for url '{e.request.url}' :"
                    f" {e.response.status_code} - {e.response.text}"
                )
                pre_err = e
                if e.response.status_code == 401:
                    raise UnauthorizedError("Unauthorized, please check your agent_id and token")
            except httpx.RequestError as e:
                logger.debug(f"Request error on attempt {attempt + 1} for url '{e.request.url}': {e}")

            if attempt < retries - 1:
                time.sleep(2**attempt)  # Exponential backoff
            else:
                err_msg = str(pre_err) if pre_err else ""
                raise MaxRetriesExceededException(
                    f"Failed to complete {method} request to {path} after {retries} attempts {err_msg}"
                )

    def close(self):
        self._client.close()

    @property
    def base_url(self) -> str:
        return str(self._client.base_url)

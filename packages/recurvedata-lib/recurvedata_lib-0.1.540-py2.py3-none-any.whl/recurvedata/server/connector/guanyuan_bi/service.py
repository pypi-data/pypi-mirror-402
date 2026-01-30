import base64
import json
from typing import Any

import httpx
import requests

from recurvedata.connectors.connectors.guanyuan_bi import GuanyuanBI
from recurvedata.server.connector.guanyuan_bi.error import GuanyuanApiError
from recurvedata.server.connector.guanyuan_bi.schema import Card, DataSet, Page
from recurvedata.utils.cache import cached


class GuanyuanBIService:
    @staticmethod
    def _handle_response(ret_json: dict[str, Any], check_result: bool) -> Any:
        if check_result:
            if ret_json.get("result") != "ok":
                raise GuanyuanApiError(data=ret_json)
            return ret_json.get("response")
        return ret_json

    @staticmethod
    async def _request(
        method: str,
        url: str,
        json: dict[str, Any] | None = None,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        check_result: bool = True,
    ) -> Any:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method,
                    url,
                    json=json,
                    data=data,
                    headers=headers,
                )
            ret_json = response.json()
        except Exception as e:
            raise GuanyuanApiError(data=str(e))
        return GuanyuanBIService._handle_response(ret_json, check_result)

    @staticmethod
    def _request_sync(
        method: str,
        url: str,
        json: dict[str, Any] | None = None,
        data: str | None = None,
        headers: dict[str, str] | None = None,
        check_result: bool = True,
    ) -> Any:
        try:
            response = requests.request(
                method,
                url,
                json=json,
                data=data,
                headers=headers,
            )
            ret_json = response.json()
        except Exception as e:
            raise GuanyuanApiError(data=str(e))
        return GuanyuanBIService._handle_response(ret_json, check_result)

    @staticmethod
    @cached(ttl=600)
    async def _sign_in_impl(base_url: str, domain: str, login_id: str, password: str) -> str:
        encoded_password = base64.b64encode(password.encode() if password else b"").decode()
        payload = {
            "domain": domain,
            "loginId": login_id,
            "password": encoded_password,
        }
        response = await GuanyuanBIService._request("POST", f"{base_url}/public-api/sign-in", json=payload)
        return response.get("token")

    @staticmethod
    async def sign_in(connector: GuanyuanBI) -> str:
        return await GuanyuanBIService._sign_in_impl(
            connector.base_url,
            connector.domain,
            connector.login_id,
            connector.password,
        )

    @staticmethod
    async def get_pages(connector: GuanyuanBI) -> list[Page]:
        payload = {"token": connector.app_token}
        response = await GuanyuanBIService._request("POST", f"{connector.base_url}/public-api/page/list", json=payload)
        return [Page.model_validate(page) for page in response]

    @staticmethod
    async def get_cards_by_page(connector: GuanyuanBI, page_id: str) -> list[Card]:
        headers = {"token": connector.app_token}
        response = await GuanyuanBIService._request(
            "GET", f"{connector.base_url}/public-api/page/{page_id}", headers=headers
        )
        return [Card.model_validate(card) for card in response.get("cards", [])]

    @staticmethod
    async def get_data_set(connector: GuanyuanBI, data_set_id: str) -> DataSet:
        payload = {"token": connector.app_token}
        response = await GuanyuanBIService._request(
            "POST", f"{connector.base_url}/public-api/data-source/list", json=payload
        )
        for data_source in response:
            if data_source.get("dsId") == data_set_id:
                return DataSet.model_validate(data_source)
        raise GuanyuanApiError(data={"code": "DATA_SET_NOT_FOUND", "message": "Data set not found"})

    @staticmethod
    async def get_card_sql(connector: GuanyuanBI, card_id: str) -> str:
        user_token = await GuanyuanBIService.sign_in(connector)
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "X-Auth-Token": user_token,
        }
        # httpx.client not working with this request, so use requests.request instead
        response = GuanyuanBIService._request_sync(
            "POST",
            f"{connector.base_url}/api/card/{card_id}/sql",
            data=json.dumps({}),
            headers=headers,
            check_result=False,
        )
        if not response.get("sql"):
            raise GuanyuanApiError(data=response)
        return response["sql"]

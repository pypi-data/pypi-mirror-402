import copy
import logging
import time
from typing import Dict, List, Union

import msal
import pandas as pd
import requests

config = dict(
    # Can be set to 'MasterUser' or 'ServicePrincipal'
    AUTHENTICATION_MODE='ServicePrincipal',
    POWER_BI_TENANT_ID='',
    POWER_BI_CLIENT_ID='',
    # Client Secret (App Secret) of the AAD app. Required only for ServicePrincipal authentication mode.
    POWER_BI_CLIENT_SECRET='',
    # Scope of AAD app. Use the below configuration to use all the permissions provided in the AAD(Azure Active Directory) app through Azure portal.
    POWER_BI_SCOPE=['https://analysis.windows.net/powerbi/api/.default'],  # 公有云
    POWER_BI_SCOPE_CN=['https://analysis.chinacloudapi.cn/powerbi/api/.default'],  # 中国区
    # URL used for initiating authorization request
    POWER_BI_AUTHORITY='https://login.microsoftonline.com/tenant_id',
    POWER_BI_AUTHORITY_CN='https://login.chinacloudapi.cn/tenant_id',
    POWER_BI_API_URL_PREFIX='https://api.powerbi.com/v1.0/myorg',
    POWER_BI_API_URL_PREFIX_CN='https://api.powerbi.cn/v1.0/myorg'
)


class PBIRefreshFailedException(Exception):
    pass


class PBIRefreshTimeoutException(Exception):
    pass


class PowerBI:

    def __init__(self, tenant_id: str, client_id: str, client_secret: str, **kwargs):
        self.config = copy.deepcopy(config)
        self.config["POWER_BI_TENANT_ID"] = tenant_id
        self.config["POWER_BI_CLIENT_ID"] = client_id
        self.config["POWER_BI_CLIENT_SECRET"] = client_secret
        for k, v in kwargs.items():
            if k in self.config:
                self.config[k] = v
        self.access_token = None
        self.token_abort_time = None

    def get_access_token(self):
        if self.access_token is not None and time.time() < self.token_abort_time:
            return self.access_token
        try:
            # Service Principal auth is the recommended by Microsoft to achieve App Owns Data Power BI embedding
            authority = self.config['POWER_BI_AUTHORITY_CN'].replace('tenant_id', self.config['POWER_BI_TENANT_ID'])
            client_app = msal.ConfidentialClientApplication(
                client_id=self.config['POWER_BI_CLIENT_ID'],
                client_credential=self.config['POWER_BI_CLIENT_SECRET'],
                authority=authority
            )
            # Make a client call if Access token is not available in cache
            response = client_app.acquire_token_for_client(scopes=self.config['POWER_BI_SCOPE_CN'])
            self.access_token = response
            self.token_abort_time = time.time() + (response["expires_in"] - 60)

            return response

        except Exception as ex:
            raise Exception('Error retrieving Access token\n' + str(ex))

    @property
    def request_header(self):
        """
        Get Power BI API request header
        """
        access_token = self.get_access_token()
        return {
            'Content-Type': 'application/json',
            'Authorization': f"{access_token['token_type']} {access_token['access_token']}"
        }

    def get_refresh_job_info(self, group_id: str, dataset_id: str, request_id: str = None, limit: int = 10) -> Union[Dict, List[Dict]]:
        """
        Parameters:
            group_id: The workspace ID
            dataset_id: The dataset ID
            request_id: 如果指定 request_id，返回对应 request Dict 否则返回 List[Dict]
            limit: numbers of recently requests (Descending), default 10
        """
        url = f"{self.config['POWER_BI_API_URL_PREFIX_CN']}/groups/{group_id}/datasets/{dataset_id}/refreshes/?$top={limit}"
        r = requests.get(url, headers=self.request_header)
        r.raise_for_status()
        ret = r.json()["value"]
        if request_id:
            return next(filter(lambda x: x["requestId"] == request_id, ret), None)
        return ret

    def refresh_dataset_in_group(self, group_id: str, dataset_id: str, is_wait: bool = True, timeout: int = 300, check_interval: int = 20, limit: int = 10):
        """
        推荐使用 refresh_datasets()

        https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/refresh-dataset-in-group \n
        Limitation:
            For Shared capacities, a maximum of 8 requests per day, including refreshes executed by using scheduled refresh, can be initiated.

        Parameters:
            group_id: The workspace ID
            dataset_id: The dataset ID
            is_wait: Wait until refresh finish, default wait for refreshing
            timeout: Default timeout is 5 minutes if is_wait is True
            check_interval: Default 20 seconds
            limit: numbers of recently requests (Descending)

        Returns:
            The refreshing job information
        """

        logging.info(f"Start refreshing dataset {dataset_id} in group {group_id}")
        url = f"{self.config['POWER_BI_API_URL_PREFIX_CN']}/groups/{group_id}/datasets/{dataset_id}/refreshes"
        r = requests.post(url, headers=self.request_header)
        r.raise_for_status()
        request_id = r.headers.get("RequestId")
        # get refresh job information
        job_info = self.get_refresh_job_info(group_id, dataset_id, request_id, limit)
        if not job_info:  # if don't receive specific job, wait a second
            time.sleep(5)
            job_info = self.get_refresh_job_info(group_id, dataset_id, request_id, limit)
        logging.info(f"Refresh detail: request_id -> {request_id}, job_info -> {job_info}")
        if not is_wait:
            if job_info["status"] == "Failed":
                logging.info(f"Refresh failed: {dataset_id}")
                raise PBIRefreshFailedException(job_info)
            return job_info
        abort_time = time.time() + timeout
        while job_info["status"] != "Completed":
            if job_info["status"] == "Failed":
                logging.info(f"Refresh failed: {dataset_id}")
                raise PBIRefreshFailedException(job_info)
            time.sleep(check_interval)
            if time.time() > abort_time:
                logging.info(f"Refresh timeout: {dataset_id}")
                raise PBIRefreshTimeoutException(job_info)
            job_info = self.get_refresh_job_info(group_id, dataset_id, request_id, limit)
            logging.info(f"Retry: {job_info}")
        logging.info(f"Refresh completed: {dataset_id}")
        return job_info

    def refresh_datasets(self, refresh_list: pd.DataFrame, is_wait: bool = True, timeout: int = 300, check_interval: int = 20, limit: int = 10):
        """
        传入包含 group_id，dataset_id 列的 dataframe，刷新完毕返回刷新的情况
        """
        summary = {
            "Completed": [], "Failed": [], "Timeout": [], "Error": []
        }
        if not {"group_id", "dataset_id"}.issubset(refresh_list.columns):
            raise Exception(f"Contain wrong columns, input must include group_id and dataset_id, while target dataframe has {refresh_list.columns.to_list()} columns.")
        for _, row in refresh_list.iterrows():
            group_id, dataset_id = row["group_id"], row["dataset_id"]
            try:
                job_info = self.refresh_dataset_in_group(group_id, dataset_id, is_wait, timeout, check_interval, limit)
                summary["Completed"].append({"group_id": group_id, "dataset_id": dataset_id, "job_info": job_info})
            except PBIRefreshFailedException as e:
                summary["Failed"].append({"group_id": group_id, "dataset_id": dataset_id, "job_info": e.args[0]})
            except PBIRefreshTimeoutException as e:
                summary["Timeout"].append({"group_id": group_id, "dataset_id": dataset_id, "job_info": e.args[0]})
            except Exception as e:
                summary["Error"].append({"group_id": group_id, "dataset_id": dataset_id, "reason": repr(e)})
        return summary

    def get_datasets_in_group(self, group_id: str) -> pd.DataFrame:
        """
        https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/get-datasets-in-group \n
        Returns a list of datasets from the specified workspace.
        """
        url = f"{self.config['POWER_BI_API_URL_PREFIX_CN']}/groups/{group_id}/datasets"
        r = requests.get(url, headers=self.request_header)
        r.raise_for_status()
        df = pd.DataFrame(r.json()["value"]).rename(columns={"id": "dataset_id"})
        df["group_id"] = group_id
        return df

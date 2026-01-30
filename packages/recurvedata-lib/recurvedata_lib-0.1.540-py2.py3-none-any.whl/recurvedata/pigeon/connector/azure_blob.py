import logging
import os
from typing import List, Optional

from azure.core.exceptions import ResourceExistsError
from azure.identity import AzureAuthorityHosts, ClientSecretCredential
from azure.storage.blob import BlobServiceClient, StorageStreamDownloader

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.utils.timing import DisplayProgress

logger = logging.getLogger(__name__)


@register_connector_class("azure_blob")
class AzureBlobConnector:
    """Connector for Azure Blob Storage.

    Four ways to config:
    - using connection_string
    - using account_url + sas_token
    - using endpoint_suffix + account_name + sas_token
    - using endpoint_suffix + account_name + tenant_id + client_id + client_secret

    kwargs:
        spn_authority_host: authority host for spn, default is AzureAuthorityHosts.AZURE_CHINA
    """

    def __init__(
        self,
        connection_string: str = None,
        account_url: str = None,
        endpoint_suffix: str = "core.chinacloudapi.cn",
        account_name: str = None,
        sas_token: str = None,
        tenant_id: str = None,
        client_id: str = None,
        client_secret: str = None,
        **kwargs,
    ):
        self.conn_string = connection_string
        self.account_url = account_url
        self.endpoint_suffix = endpoint_suffix
        self.account_name = account_name
        self.sas_token = sas_token
        self.kwargs = kwargs
        self.spn_authority_host = self.kwargs.get("spn_authority_host") or AzureAuthorityHosts.AZURE_CHINA

        authorize_by_conn_string = False
        authorize_by_sas_token = False
        authorize_by_spn_secret = False
        if connection_string:
            authorize_by_conn_string = True
        if sas_token and (account_url or all((account_name, endpoint_suffix))):
            authorize_by_sas_token = True
        if tenant_id and client_id and client_secret and all((account_name, endpoint_suffix)):
            authorize_by_spn_secret = True

        if not any((authorize_by_conn_string, authorize_by_sas_token, authorize_by_spn_secret)):
            raise ValueError(
                """
                    invalid authorization info
                    Four ways to config:
                    - using connection_string
                    - using account_url + sas_token
                    - using endpoint_suffix + account_name + sas_token
                    - using endpoint_suffix + account_name + tenant_id + client_id + client_secret
                """
            )

        if authorize_by_conn_string:
            self.blob_service = BlobServiceClient.from_connection_string(connection_string, **kwargs)
        elif authorize_by_sas_token:
            if not account_url:
                account_url = f"https://{account_name}.blob.{endpoint_suffix}"
            self.blob_service = BlobServiceClient(account_url, credential=sas_token, **kwargs)
        else:
            credential = ClientSecretCredential(tenant_id, client_id, client_secret, authority=self.spn_authority_host)
            account_url = f"https://{account_name}.blob.{endpoint_suffix}"
            self.blob_service = BlobServiceClient(account_url=account_url, credential=credential)

    @property
    def account_key(self) -> Optional[str]:
        if not self.conn_string:
            return None
        kvs = self.parse_conn_string(self.conn_string)
        return kvs["accountkey"]

    @staticmethod
    def parse_conn_string(conn_string: str):
        parts = conn_string.strip(";").split(";")
        kvs = {}
        for p in parts:
            k, v = p.split("=", 1)
            kvs[k.lower()] = v
        return kvs

    def get_url(self, container: str, blob: str) -> str:
        return f"https://{self.blob_service.primary_hostname}/{container}/{blob}"

    def create_container(self, container_name: str, exist_ok=True):
        """create container"""
        try:
            return self.blob_service.create_container(container_name)
        except ResourceExistsError as e:
            if exist_ok:
                logger.info(f"container {container_name} already exists, skip")
            else:
                raise e

    def delete_container(self, container_name: str, **kwargs):
        """if container not exists, error will be suppressed with the fail_not_exist parameter"""
        self.blob_service.delete_container(container_name, **kwargs)

    def exists(self, container_name: str, blob_name: str = None, **kwargs) -> bool:
        """
        if blob name is none, check whether container exists or not
        if blob name specified, check blob exists or not in the  container
        """
        if blob_name is None:
            client = self.blob_service.get_container_client(container_name)
        else:
            client = self.blob_service.get_blob_client(container_name, blob_name)
        return client.exists(**kwargs)

    def delete_blob(self, container_name, blob_name, **kwargs):
        container = self.blob_service.get_container_client(container_name)
        container.delete_blob(blob_name, **kwargs)

    def list_blobs(self, container_name, name_starts_with=None, include=None, **kwargs) -> List[str]:
        container = self.blob_service.get_container_client(container_name)
        generator = container.list_blobs(name_starts_with=name_starts_with, include=include, **kwargs)
        return [blob.name for blob in generator]

    def upload(self, container_name, local_file_path, blob_name=None, overwrite=True, is_progress_hook=True, **kwargs):
        """
        Upload local file to container with specified blob name.
        The specified container will also be created if not exists.
        """
        if not blob_name:
            blob_name = os.path.basename(local_file_path)

        # container_blob = f'{container_name}/{blob_name}'
        blob = self.blob_service.get_blob_client(container_name, blob_name)
        if not overwrite and blob.exists():
            logger.info("Blob exists, skip!")
            return blob_name

        size = os.path.getsize(local_file_path)
        options = {"overwrite": True, "max_concurrency": 4}
        if is_progress_hook:
            options["progress_hook"] = DisplayProgress(size, stream=False)

        options.update(kwargs)
        with open(local_file_path, "rb") as data:
            blob.upload_blob(data, **options)
        return blob_name

    def download(self, container_name, blob_name, local_file_path, **kwargs):
        """download blob to local"""
        blob = self.blob_service.get_blob_client(container_name, blob_name)
        size = blob.get_blob_properties().size
        if size == 0:
            logging.warning("blob %s has no content, create an empty file and exit", blob_name)
            with open(local_file_path, "w"):
                return

        options = {
            "max_concurrency": 4,
            "progress_hook": DisplayProgress(size, stream=False),
        }
        options.update(kwargs)
        with open(local_file_path, "wb") as f:
            data: StorageStreamDownloader = blob.download_blob(**options)
            data.readinto(f)
        return local_file_path

import logging
import os

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.object_store import ObjectStoreMixin
from recurvedata.connectors.proxy import HTTP_PROXY_CONFIG_SCHEMA, HttpProxyMixin
from recurvedata.connectors.utils import juice_sync_process_special_character_within_secret
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

try:
    import boto3
    from botocore.config import Config
    from s3fs import S3FileSystem
except ImportError:
    S3FileSystem = None

CONNECTION_TYPE = "s3"
UI_CONNECTION_TYPE = "AWS S3"

logger = logging.getLogger(__name__)


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class S3(HttpProxyMixin, ObjectStoreMixin):
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.DESTINATION]
    setup_extras_require = ["fsspec[s3]", "s3fs>=2021.08", "boto3"]

    config_schema = {
        "type": "object",
        "properties": {
            "access_key_id": {"type": "string", "title": _l("AWS Access Key ID")},
            "secret_access_key": {"type": "string", "title": _l("AWS Secret Access Key")},
            "region": {"type": "string", "title": _l("AWS Region")},
            "bucket": {"type": "string", "title": _l("Bucket Name")},
            "proxies": HTTP_PROXY_CONFIG_SCHEMA["proxies"],
        },
        "order": ["access_key_id", "secret_access_key", "region", "bucket", "proxies"],
        "required": ["access_key_id", "secret_access_key"],
        "secret": ["secret_access_key"],
    }

    def init_connection(self, conf) -> S3FileSystem:
        # todo: proxy
        with self._init_proxy_manager():
            client_kwargs = {}
            if "region" in conf and conf["region"]:
                client_kwargs["region_name"] = conf["region"]
            con = S3FileSystem(key=conf["access_key_id"], secret=conf["secret_access_key"], client_kwargs=client_kwargs)
            self.connector = con
            return con

    def test_connection(self):
        with self._init_proxy_manager():
            logger.info(
                f'test s3 connection with bucket {self.bucket} and region {self.region}, proxy: {os.environ.get("http_proxy")}'
            )

            session = boto3.Session(
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.region,
            )
            timeout = 30
            s3_client = session.client("s3", config=Config(connect_timeout=timeout, read_timeout=timeout))
            if self.bucket:
                s3_client.list_objects_v2(Bucket=self.bucket, MaxKeys=1)
            else:
                s3_client.list_buckets()

    @property
    def endpoint(self):
        if not self.region:
            raise ValueError("there is no region for endpoint")
        return f"s3.{self.region}.amazonaws.com"

    juice_sync_able = True

    def juice_sync_path(self, path: str) -> str:
        """
        :param path: the s3 path, note that path is not started with bucket
        :return:
        """
        if not self.bucket:
            raise ValueError("the connection bucket cannot be empty in juice sync")
        secret_part = f"{self.access_key_id}:{self.secret_access_key}"
        secret_part = juice_sync_process_special_character_within_secret(secret_part)
        endpoint_path_part = f'{self.bucket}.{self.endpoint}/{path.lstrip("/")}'
        path_with_secret = f"s3://{secret_part}@{endpoint_path_part}"
        path_without_secret = f"s3://{endpoint_path_part}"
        return path_with_secret, path_without_secret

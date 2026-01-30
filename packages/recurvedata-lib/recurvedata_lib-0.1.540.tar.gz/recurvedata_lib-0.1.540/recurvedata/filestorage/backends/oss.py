from functools import cached_property

import oss2
from ossfs.async_oss import AioOSSFileSystem
from pydantic import ConfigDict

from recurvedata.filestorage.backends.fsspec import FSSpecAbstractStorage
from recurvedata.filestorage.interface import StorageConfig, StorageType


class OSSStorageConfig(StorageConfig):
    endpoint: str
    access_key_id: str
    access_key_secret: str
    bucket_name: str
    directory: str = ""
    security_token: str | None = None  # for sts token

    model_config = ConfigDict(extra="allow")


class OSSStorage(FSSpecAbstractStorage):
    config_class = OSSStorageConfig
    config: OSSStorageConfig
    _fs: AioOSSFileSystem

    @classmethod
    def storage_type(cls) -> StorageType:
        return StorageType.OSS

    def get_fs(self) -> AioOSSFileSystem:
        return AioOSSFileSystem(
            endpoint=self.config.endpoint,
            key=self.config.access_key_id,
            secret=self.config.access_key_secret,
            token=self.config.security_token,
        )

    def normalize_path(self, path: str) -> str:
        return self.join_path(self.config.bucket_name, self.config.directory, path)

    @cached_property
    def public_bucket(self) -> oss2.Bucket:
        """The public Bucket object, used for generating public download urls."""
        if "-internal" not in self.config.endpoint:
            public_endpoint = self.config.endpoint
        else:
            public_endpoint = self.config.endpoint.replace("-internal", "")
        auth = oss2.Auth(self.config.access_key_id, self.config.access_key_secret)
        return oss2.Bucket(auth, public_endpoint, self.config.bucket_name)

    def get_presigned_url(self, path: str, expiration: int = 1800, **kwargs) -> str:
        headers = {"content-disposition": "attachment"}
        return self.public_bucket.sign_url(
            "GET", self.join_path(self.config.directory, path), expiration, headers=headers, slash_safe=True
        )

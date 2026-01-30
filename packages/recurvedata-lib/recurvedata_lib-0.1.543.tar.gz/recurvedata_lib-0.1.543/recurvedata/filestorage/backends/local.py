import datetime
import urllib.parse
from typing import Any

from jose import JWTError, jwt
from morefs.asyn_local import AsyncLocalFileSystem
from pydantic import SecretStr

from recurvedata.filestorage.backends.fsspec import FSSpecAbstractStorage
from recurvedata.filestorage.interface import StorageConfig, StorageType
from recurvedata.utils.date_time import utcnow

ALGORITHM = "HS256"
_DEFAULT_SECRET_KEY = SecretStr("619805f2af666a623f37221ce8dfbec85ce9e83a16b20fe4a424078ed37f2a3a")


class LocalStorageConfig(StorageConfig):
    root_dir: str = "/tmp"
    auto_mkdir: bool = True

    # below are required for generating presigned url
    secret_key: SecretStr = _DEFAULT_SECRET_KEY
    """
    The secret key to sign and verify the presigned url. Although it's better to
    use a more secure key, for simplicity, we assign a default value here.
    To generate a secure key, you can use the following code:

        ```python
        import secrets
        key = secrets.token_hex(32)
        print(key)
        ```
    """
    server_base_url: str = None


class LocalStorage(FSSpecAbstractStorage):
    config_class = LocalStorageConfig
    config: LocalStorageConfig
    _fs: AsyncLocalFileSystem

    @classmethod
    def storage_type(cls) -> StorageType:
        return StorageType.LOCAL

    def get_fs(self) -> AsyncLocalFileSystem:
        return AsyncLocalFileSystem(auto_mkdir=self.config.auto_mkdir)

    def normalize_path(self, path: str) -> str:
        return self.join_path(self.config.root_dir, path)

    def get_presigned_url(self, path: str, expiration: int = 1800, **kwargs) -> str:
        if not all((self.config.secret_key, self.config.server_base_url)):
            raise ValueError("secret_key and server_base_url are required to generate presigned url")

        to_encode = {"path": path, "exp": utcnow() + datetime.timedelta(seconds=expiration)}
        encoded = jwt.encode(to_encode, self.config.secret_key.get_secret_value(), algorithm=ALGORITHM)
        base_url = str(self.config.server_base_url).rstrip("/")
        query_string = urllib.parse.urlencode({"token": encoded} | kwargs)
        return f"{base_url}/{path}?{query_string}"

    def decode_presigned_url(self, token: str) -> dict[str, Any] | None:
        try:
            payload = jwt.decode(token, self.config.secret_key.get_secret_value(), algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

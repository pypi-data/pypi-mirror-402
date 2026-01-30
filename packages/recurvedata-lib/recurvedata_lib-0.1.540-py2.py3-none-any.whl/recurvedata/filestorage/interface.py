import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict


class StorageType(str, Enum):
    LOCAL = "local"
    S3 = "s3"
    OSS = "oss"

    def __str__(self) -> str:
        return str.__str__(self)


class StorageConfig(BaseModel):
    """Base class for storage configurations."""

    model_config = ConfigDict(extra="forbid")


class AbstractFileStorage(ABC):
    config_class: ClassVar[type[StorageConfig]] = StorageConfig
    config: StorageConfig

    def __init__(self, config: StorageConfig):
        self.config = config

    @classmethod
    def from_params(cls, **kwargs) -> Self:
        return cls(cls.config_class.model_validate(kwargs))

    @classmethod
    @abstractmethod
    def storage_type(cls) -> StorageType:
        """Return the storage type."""
        ...

    @abstractmethod
    async def listdir(self, path: str) -> list[str]:
        """List the contents of a directory."""
        ...

    @abstractmethod
    async def write_bytes(self, path: str, content: bytes):
        """Write bytes content to a destination path."""
        ...

    @abstractmethod
    async def read_bytes(self, path: str) -> bytes:
        """Read bytes content from a source path."""
        ...

    @abstractmethod
    async def put(self, local_path: str, remote_path: str):
        """Upload a file from a source path to a destination path."""
        ...

    @abstractmethod
    async def get(self, remote_path: str, local_path: str):
        """Download a file from a source path to a destination path."""
        ...

    @abstractmethod
    async def delete(self, path: str):
        """Delete a file from the given path."""
        ...

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if a file exists at the given path."""
        ...

    @abstractmethod
    def get_presigned_url(self, path: str, expiration: int = 1800, **kwargs) -> str:
        """Generate a presigned URL for a file for temporary access."""
        ...

    @staticmethod
    def join_path(*parts: str) -> str:
        """Join path parts together."""
        return os.path.normpath(os.path.join(*parts))

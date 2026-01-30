from recurvedata.filestorage._factory import Factory
from recurvedata.filestorage.interface import AbstractFileStorage, StorageType

factory = Factory[StorageType, AbstractFileStorage](
    {
        StorageType.LOCAL: "recurvedata.filestorage.backends.local.LocalStorage",
        StorageType.OSS: "recurvedata.filestorage.backends.oss.OSSStorage",
    }
)

__all__ = ["AbstractFileStorage", "StorageType", "factory"]

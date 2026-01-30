from abc import ABC, abstractmethod
from functools import cached_property

from fsspec.asyn import AsyncFileSystem

from recurvedata.filestorage.interface import AbstractFileStorage


class FSSpecAbstractStorage(AbstractFileStorage, ABC):
    _fs: AsyncFileSystem

    @cached_property
    def _fs(self) -> AsyncFileSystem:
        # TODO(liyangliang): we could consider involve a pooling mechanism here
        # see discussion with ChatGPT https://chat.openai.com/share/972e3bcc-0ebc-43b8-9a49-72f3dd7dc2b6
        return self.get_fs()

    @abstractmethod
    def get_fs(self) -> AsyncFileSystem:
        ...

    def normalize_path(self, path: str) -> str:
        """Normalize a path to be used with the filesystem."""
        return path

    async def listdir(self, path: str) -> list[str]:
        return await self._fs._ls(self.normalize_path(path))

    async def write_bytes(self, path: str, content: bytes):
        await self._fs._pipe_file(self.normalize_path(path), content)

    async def read_bytes(self, path: str) -> bytes:
        return await self._fs._cat_file(self.normalize_path(path))

    async def put(self, local_path: str, remote_path: str):
        await self._fs._put_file(local_path, self.normalize_path(remote_path))

    async def get(self, remote_path: str, local_path: str):
        await self._fs._get_file(self.normalize_path(remote_path), local_path)

    async def delete(self, path: str):
        await self._fs._rm(self.normalize_path(path))

    async def exists(self, path: str) -> bool:
        return await self._fs._exists(self.normalize_path(path))

from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.connectors.fs import FileConnectorABC
from recurvedata.consts import ConnectionCategory


class FTPMixin(RecurveConnectorBase, FileConnectorABC):
    category = [
        ConnectionCategory.STORAGE,
    ]

    def __init__(self, conf: dict, *args, **kwargs):
        self.conf = conf
        self.connector = self.init_connection(conf)

    def init_connection(self, conf):
        raise NotImplementedError

    def exists(self, key) -> bool:
        return self.connector.exists(key)

    def stat(self, key):
        return self.connector.stat(key)

    def mkdir(self, key):
        return self.connector.mkdir(key)

    def test_connection(self):
        self.connector.ls("/")

    def get(self, key, local_file):
        return self.connector.get(key, local_file)

    def put(self, local_file, object_store_key):
        return self.connector.put(local_file, object_store_key)

    def delete(self, key):
        return self.connector.rm(key)

    def ls(self, key):
        return self.connector.ls(key)

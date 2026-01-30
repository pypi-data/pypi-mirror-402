from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.connectors.fs import FileConnectorABC
from recurvedata.consts import ConnectionCategory


class ObjectStoreMixin(RecurveConnectorBase, FileConnectorABC):
    category = [
        ConnectionCategory.STORAGE,
    ]

    def __init__(self, conf: dict, *args, **kwargs):
        super().__init__(conf, *args, **kwargs)
        self.connector = self.init_connection(conf)

    def init_connection(self, conf):
        raise NotImplementedError

    def exists(self, key) -> bool:
        key = self.bucket_key(key)
        return self.connector.exists(key)

    def stat(self, key):
        key = self.bucket_key(key)
        return self.connector.stat(key)

    def mkdir(self, key):
        key = self.bucket_key(key)
        return self.connector.mkdir(key)

    def test_connection(self):
        self.connector.ls(self.bucket_key("/"))

    def get(self, key, local_file):
        key = self.bucket_key(key)
        return self.connector.get(key, local_file)

    def put(self, local_file, object_store_key):
        object_store_key = self.bucket_key(object_store_key)
        return self.connector.put(local_file, object_store_key)

    def delete(self, key):
        key = self.bucket_key(key)
        return self.connector.rm(key)

    def ls(self, key):
        key = self.bucket_key(key)
        return self.connector.ls(key)

    @property
    def bucket(self):
        return self.conf.get("bucket")

    def bucket_key(self, key):
        if self.bucket:
            if key.startswith("/"):
                return f"{self.bucket}{key}"
            return f"{self.bucket}/{key}"
        return key

    # todo: delete by prefix

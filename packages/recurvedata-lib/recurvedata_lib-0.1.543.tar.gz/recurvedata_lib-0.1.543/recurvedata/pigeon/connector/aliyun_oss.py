import logging
import os

import oss2

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.utils.timing import ProgressCallback


@register_connector_class("oss")
class OSSBucketConnector(object):
    def __init__(self, access_key_id, access_key_secret, endpoint, bucket_name, **kwargs):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.endpoint = endpoint
        self.bucket_name = bucket_name

        if not all((self.access_key_id, self.access_key_secret)):
            logging.info("access_key_id or access_key_secret is missing, fallback to ")
            self._auth = oss2.AnonymousAuth()
        else:
            self._auth = oss2.make_auth(self.access_key_id, self.access_key_secret)

        self.bucket = oss2.Bucket(self._auth, self.endpoint, self.bucket_name)
        proxies = kwargs.get("proxies")
        if proxies:
            # pass proxies to the underlying requests.Session
            logging.info("use %s as proxies", proxies)
            self.bucket.session.session.proxies = proxies

    def has_object(self, key):
        return self.bucket.object_exists(key)

    def delete_key(self, key):
        self.bucket.delete_object(key)

    def delete_keys_by_prefix(self, prefix):
        keys = []
        batch_size = 100
        for obj in oss2.ObjectIteratorV2(bucket=self.bucket, prefix=prefix):
            keys.append(obj.key)
            if len(keys) >= batch_size:
                self.bucket.batch_delete_objects(keys)
                keys = []
        if keys:
            self.bucket.batch_delete_objects(keys)

    def get_keys(self, prefix="", delimiter=""):
        keys = [x.key for x in oss2.ObjectIteratorV2(bucket=self.bucket, prefix=prefix, delimiter=delimiter)]
        if delimiter:
            keys = [x for x in keys if not x.endswith(delimiter)]

        return keys

    def upload(self, filename, key=None, folder=None, overwrite=True, num_threads=4, **kwargs):
        if not key:
            key = os.path.basename(filename)
        if folder:
            key = os.path.join(folder, key)

        if not overwrite:
            if self.has_object(key=key):
                return key

        oss2.resumable_upload(self.bucket, key, filename, progress_callback=ProgressCallback(), num_threads=num_threads)
        return key

    def download(self, key, folder=None, filename=None, overwrite=True, num_threads=4, **kwargs):
        if not filename:
            filename = os.path.basename(key)
        if folder:
            filename = os.path.join(folder, filename)

        if not overwrite and os.path.exists(filename):
            return filename

        oss2.resumable_download(
            self.bucket, key, filename, progress_callback=ProgressCallback(), num_threads=num_threads
        )
        return filename

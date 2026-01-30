import os

import qcloud_cos

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.utils.timing import ProgressCallback


@register_connector_class("cos")
class COSConnector(object):
    def __init__(self, secret_id, secret_key, region, proxies=None, endpoint=None, **kwargs):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.region = region

        self.config = qcloud_cos.CosConfig(
            Region=region, SecretId=secret_id, SecretKey=secret_key, Endpoint=endpoint, Proxies=proxies
        )
        self.cos = qcloud_cos.CosS3Client(self.config)

    def has_bucket(self, bucket_name):
        return self.cos.bucket_exists(bucket_name)

    def create_bucket(self, bucket_name):
        if not self.has_bucket(bucket_name):
            self.cos.create_bucket(bucket_name)

    def delete_bucket(self, bucket_name):
        if self.has_bucket(bucket_name):
            self.cos.delete_bucket(bucket_name)

    def has_object(self, bucket_name, key):
        return self.cos.object_exists(bucket_name, key)

    def delete_object(self, bucket_name, key):
        self.cos.delete_object(bucket_name, key)

    def list_objects(self, bucket_name, prefix=""):
        res = self.cos.list_objects(Bucket=bucket_name, Prefix=prefix)
        return [x["Key"] for x in res.get("Contents", [])]

    def delete_keys_by_prefix(self, bucket_name, prefix):
        keys = self.list_objects(bucket_name, prefix)
        for key in keys:
            self.delete_object(bucket_name, key)

    def upload(self, bucket_name, filename, key=None, folder=None, overwrite=True, num_threads=4, **kwargs):
        if not key:
            key = os.path.basename(filename)
        if folder:
            key = os.path.join(folder, key)

        if not overwrite:
            if self.has_object(bucket_name=bucket_name, key=key):
                return key

        self.cos.upload_file(
            Bucket=bucket_name,
            LocalFilePath=filename,
            Key=key,
            MAXThread=num_threads,
            progress_callback=ProgressCallback(),
        )
        return key

    def download(self, bucket_name, key, folder=None, filename=None, overwrite=True, num_threads=4, **kwargs):
        if not self.has_object(bucket_name, key):
            raise ValueError(f"{key} not exists in {bucket_name}")

        if not filename:
            filename = os.path.basename(key)
        if folder:
            filename = os.path.join(folder, filename)

        if not overwrite and os.path.exists(filename):
            return filename

        self.cos.download_file(Bucket=bucket_name, Key=key, DestFilePath=filename, MAXThread=num_threads)
        return filename

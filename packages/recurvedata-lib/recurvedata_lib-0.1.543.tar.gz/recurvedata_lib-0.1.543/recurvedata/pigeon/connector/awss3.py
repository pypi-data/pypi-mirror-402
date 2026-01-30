import os
import urllib.parse

import boto3
import botocore.exceptions
from botocore.config import Config

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.utils.timing import DisplayProgress


@register_connector_class("s3")
class S3Connector(object):
    def __init__(self, aws_access_key_id, aws_secret_access_key, region="cn-north-1", proxies=None, **kwargs):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region = region

        self.s3 = boto3.resource(
            "s3",
            region_name=self.region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            config=Config(proxies=proxies),
        )

    def create_bucket(self, bucket_name):
        return self.s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": self.region})

    def has_bucket(self, bucket_name):
        exists = True
        try:
            self.s3.meta.client.head_bucket(Bucket=bucket_name)
        except botocore.exceptions.ClientError as e:
            error_code = int(e.response["Error"]["Code"])
            if error_code == 404:
                exists = False
        return exists

    def get_bucket(self, bucket_name):
        if self.has_bucket(bucket_name):
            return self.s3.Bucket(bucket_name)
        return self.create_bucket(bucket_name)

    def delete_bucket(self, bucket_name):
        bucket = self.get_bucket(bucket_name)
        for key in bucket.objects.all():
            key.delete()
        bucket.delete()

    def has_object(self, bucket_name, key):
        exists = True
        try:
            self.s3.meta.client.head_object(Bucket=bucket_name, Key=key)
        except botocore.exceptions.ClientError as e:
            error_code = int(e.response["Error"]["Code"])
            if error_code == 404:
                exists = False
        return exists

    @staticmethod
    def parse_s3_url(s3url):
        parsed_url = urllib.parse.urlparse(s3url)
        if not parsed_url.netloc:
            raise ValueError("Please provide a bucket_name")

        bucket_name = parsed_url.netloc
        key = parsed_url.path.strip("/")
        return bucket_name, key

    def delete_key(self, key, bucket_name=None):
        if bucket_name is None:
            bucket_name, key = self.parse_s3_url(key)
        bucket = self.get_bucket(bucket_name)
        bucket.Object(key).delete()

    def delete_keys_by_prefix(self, bucket_name, prefix):
        bucket = self.get_bucket(bucket_name)
        for key in bucket.objects.filter(Prefix=prefix):
            key.delete()

    def get_keys(self, bucket_name, prefix=None):
        bucket = self.get_bucket(bucket_name)
        if prefix is not None:
            all_keys = bucket.objects.filter(Prefix=prefix)
        else:
            all_keys = bucket.objects.all()

        return [x.key for x in all_keys]

    def upload(self, bucket_name, filename, key=None, folder=None, overwrite=True, **kwargs):
        if not key:
            key = os.path.basename(filename)
        if folder:
            key = os.path.join(folder, key)

        if not overwrite:
            if self.has_object(bucket_name=bucket_name, key=key):
                return key

        size = os.path.getsize(filename)
        bucket = self.get_bucket(bucket_name)
        with open(filename, "rb") as data:
            bucket.upload_fileobj(data, key, Callback=DisplayProgress(size), **kwargs)
        return key

    def download(self, bucket_name, key, folder=None, filename=None, overwrite=True, **kwargs):
        if not self.has_object(bucket_name, key):
            raise ValueError(f"{key} not exists in {bucket_name}")

        if not filename:
            filename = os.path.basename(key)
        if folder:
            filename = os.path.join(folder, filename)

        if not overwrite and os.path.exists(filename):
            return filename

        size = float(self.s3.meta.client.head_object(Bucket=bucket_name, Key=key)["ContentLength"])
        bucket = self.get_bucket(bucket_name)
        with open(filename, "wb") as data:
            bucket.download_fileobj(key, data, Callback=DisplayProgress(size), **kwargs)
        return filename

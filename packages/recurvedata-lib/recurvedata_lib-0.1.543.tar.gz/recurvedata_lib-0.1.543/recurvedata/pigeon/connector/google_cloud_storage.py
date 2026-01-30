import copy
import logging
import os

from google import auth
from google.cloud import storage
from google.oauth2 import service_account

from recurvedata.pigeon.connector._registry import register_connector_class


@register_connector_class(["google_cloud_storage", "gcs"])
class GoogleCloudStorageConnector(object):
    def __init__(
        self,
        key_path: str = None,
        key_dict: dict = None,
        project: str = None,
        proxies: dict = None,
        bucket_name: str = None,
        **kwargs,
    ):
        """
        instance of gcs
        :param project: project_id
        :param key_path: path to json key file
        :param key_dict: dict of key
        :param proxies: proxy
        :param bucket_name: bucket's name
        """
        self._project_id = project
        self._key_path = key_path
        self._key_dict = key_dict
        self._proxies = proxies
        self.bucket_name = bucket_name

        if not any([self._key_path, self._key_dict]):
            # 需要配置好 GOOGLE_APPLICATION_CREDENTIALS 环境变量
            # export GOOGLE_APPLICATION_CREDENTIALS='{service account key 文件路径}'
            self._credentials, auth_project_id = auth.default()
            self._project_id = self._project_id or auth_project_id
        elif self._key_path:
            # 传入 service account key 文件路径
            self._credentials = service_account.Credentials.from_service_account_file(filename=self._key_path)
        else:
            # 传入 service account key dict
            _key_dict = copy.deepcopy(self._key_dict)
            _key_dict["private_key"] = _key_dict["private_key"].replace("\\n", "\n")
            self._credentials = service_account.Credentials.from_service_account_info(info=_key_dict)
        self._project_id = self._project_id or self._credentials.project_id

        if self._proxies:
            for scheme in ["http", "https"]:
                os.environ[f"{scheme}_proxy"] = self._proxies[scheme]

        self.client = storage.Client(project=self._project_id, credentials=self._credentials, **kwargs)

    def create_bucket(self, bucket_name, location=None):
        logging.info(f"Start creating bucket {bucket_name} at location {location}")
        new_bucket = self.client.create_bucket(bucket_name, location=location)
        logging.info(f"Successfully created bucket {bucket_name} at location {location}")
        return new_bucket

    def get_buckets(self):
        buckets = self.client.list_buckets()
        return [bucket.name for bucket in buckets]

    def has_key(self, key, bucket_name=None):
        if not bucket_name:
            bucket_name = self.bucket_name

        bucket = self.client.bucket(bucket_name)
        return bucket.blob(key).exists()

    def get_keys(self, bucket_name=None, prefix=""):
        if not bucket_name:
            bucket_name = self.bucket_name

        keys = self.client.list_blobs(bucket_name, prefix=prefix)
        return [key.name for key in keys]

    def delete_key(self, key, bucket_name=None):
        if not bucket_name:
            bucket_name = self.bucket_name

        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(key)
        logging.info(f"Start deleting storage object {key}")
        blob.delete()
        logging.info(f"Successfully deleted storage object {key}")

    def upload(self, filename, bucket_name=None, key=None, folder=None, overwrite=True, **kwargs):
        if not bucket_name:
            bucket_name = self.bucket_name
        if not key:
            key = os.path.basename(filename)
        if folder:
            key = os.path.join(folder, key)

        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(key)

        if not overwrite and blob.exists():
            return key

        logging.info(f"Start uploading file {filename} to {key}.")
        blob.upload_from_filename(filename, **kwargs)
        logging.info(f"Successfully uploaded file {filename} to {key}.")
        return key

    def download(self, key, bucket_name=None, folder=None, filename=None, overwrite=True, **kwargs):
        if not bucket_name:
            bucket_name = self.bucket_name
        if not filename:
            filename = os.path.basename(key)
        if folder:
            filename = os.path.join(folder, filename)

        if not overwrite and os.path.exists(filename):
            return filename

        bucket = self.client.bucket(bucket_name)
        blob = bucket.get_blob(key)
        logging.info(f"Start downloading storage object {key} from bucket {bucket_name} to local file {filename}.")
        logging.info(f"Size: {round(blob.size / 1024 / 1024, 2)} MB")
        blob.download_to_filename(filename, **kwargs)
        logging.info(
            f"Successfully downloaded storage object {key} from bucket {bucket_name} to local file {filename}."
        )
        return filename

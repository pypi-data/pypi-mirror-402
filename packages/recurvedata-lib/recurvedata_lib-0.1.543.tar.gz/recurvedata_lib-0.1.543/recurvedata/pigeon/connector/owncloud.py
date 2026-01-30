import logging
import os
import traceback

import pandas as pd
from owncloud import Client, HTTPResponseError

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.utils.fs import new_tempfile, remove_files_safely


class OwncloudException(Exception):
    pass


class OwncloudDownloadException(OwncloudException):
    pass


class OwncloudUploadException(OwncloudException):
    pass


class NewOwncloudClient(Client):
    def get_webdav_url(self):
        return self._webdav_url


@register_connector_class('owncloud')
class OwncloudConnector(object):
    def __init__(self, url: str = None, user: str = None, password: str = None, **kwargs):
        self.url = url
        self.user = user
        self.password = password
        self.oc = NewOwncloudClient(url, **kwargs)
        self.oc.login(user, password)

    def download_file(self, remote_path: str, local_path: str):
        logging.info(f'Downloading remote file {remote_path} to {local_path}.')
        try:
            status = self.oc.get_file(remote_path, local_path)
            if status:
                logging.info(f'Successfully download remote file {remote_path} to {local_path}.')
            else:
                raise OwncloudDownloadException(f'Failed to download remote file {remote_path}, unknown error.')
        except HTTPResponseError as e:
            logging.error(traceback.format_exc())
            raise OwncloudDownloadException(
                f'Failed to download remote file {remote_path}, HTTPResponseError {e.res}.'
            )
        return status

    def upload_file(self, remote_path: str, local_source_file: str, **kwargs):
        logging.info(f'Uploading local file {local_source_file} to {remote_path}.')
        try:
            res = self.oc.put_file(remote_path, local_source_file, **kwargs)
            logging.info(f'Successfully upload local file {local_source_file} to remote {remote_path}.')
        except Exception as e:
            logging.error(traceback.format_exc())
            raise OwncloudUploadException(
                f'Failed to upload local file {local_source_file} to remote {remote_path}, {e.args}.'
            )
        return res

    def get_pandas_df(self, remote_path: str) -> pd.DataFrame:
        temp_file_path = new_tempfile()
        if self.download_file(remote_path, temp_file_path):
            file_type = os.path.splitext(remote_path)[-1]
            try:
                if file_type and file_type.lower() in ('.xlsx', '.xls'):
                    df = pd.read_excel(temp_file_path)
                elif file_type and file_type.lower() in ('.parquet', '.parq'):
                    df = pd.read_parquet(temp_file_path)
                elif file_type and file_type.lower() == '.json':
                    df = pd.read_json(temp_file_path)
                else:
                    df = pd.read_csv(temp_file_path)
            except Exception as e:
                logging.error(traceback.format_exc())
                raise ValueError(f'Failed to load remote file {remote_path} to pandas df, {e.args}.')
            finally:
                remove_files_safely(temp_file_path)
            logging.info(f'Successfully load remote file {remote_path} to pandas df, {len(df)} rows.')
            return df

    @property
    def webdav_url(self):
        return self.oc.get_webdav_url()

    @property
    def http_auth_conf(self):
        return {'username': f'{self.user}', 'password': f'{self.password}'}

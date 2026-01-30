import datetime
import logging
import mimetypes
import os
import urllib.parse

import requests

try:
    from recurvedata.pigeon.utils import fs, trim_suffix
except ImportError:
    pass

from recurvedata.operators.transfer_operator.task import LoadTask

logger = logging.getLogger(__name__)


class FileBrowserLoadTask(LoadTask):
    ds_name_fields = ("data_source_name",)
    ds_types = ("filebrowser",)
    should_write_header = True
    worker_install_require = ["requests", "pigeon"]

    def execute_impl(self, *args, **kwargs):
        conf = self.rendered_config
        ds = self.must_get_connection_by_name(conf["data_source_name"])
        file_to_upload = self.filename
        remote_filename = conf["filename"]

        cm = conf["compress_method"]
        if cm != "None":
            logger.info("compressing file using %s...", cm)
            if cm == "Gzip":
                ext = ".gz"
                file_to_upload = fs.gzip_compress(self.filename, using_cmd=True)
            elif cm == "Zip":
                ext = ".zip"
                arcname = trim_suffix(os.path.basename(remote_filename), ext)
                file_to_upload = fs.zip_compress(self.filename, using_cmd=False, arcname=arcname)
            else:
                # won't reach here
                raise ValueError(f"compress method {cm} is not supported")

            if not remote_filename.endswith(ext):
                remote_filename = f"{remote_filename}{ext}"

        client = FileBrowserClient(ds.host, ds.user, ds.password)

        remote_filename = os.path.join(conf["directory"], remote_filename)
        logger.info("uploading %s to %s", file_to_upload, remote_filename)
        client.upload(file_to_upload, remote_filename, override=True)
        fs.remove_files_safely([self.filename, file_to_upload])

    @classmethod
    def config_schema(cls):
        # get_choices_by_type = cls.get_connection_names_by_type
        # dss = get_choices_by_type(cls.ds_types)
        schema = {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": "FileBrowser Data Source",
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": cls.ds_types,
                    },
                    # 'default': cls.first_or_default(dss, ''),
                },
                "directory": {
                    "type": "string",
                    "title": "Directory",
                    "description": "要上传到的文件夹",
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "filename": {
                    "type": "string",
                    "title": "Filename",
                    "description": "上传后的文件名，支持模板变量",
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "compress_method": {
                    "type": "string",
                    "title": "Compress Method",
                    "enum": ["None", "Gzip", "Zip"],
                    "enumNames": ["None", "Gzip", "Zip"],
                    "default": "None",
                    "description": "文件的压缩方式，默认不压缩。如果选择了压缩，会在文件名加上相应的后缀。",
                },
            },
            "required": ["data_source_name", "directory", "filename", "compress_method"],
        }
        return schema


class FileBrowserClient(object):
    # token 有效期，实际上默认是 2 小时，这里只保留 1 小时
    TOKEN_AGE = datetime.timedelta(seconds=1 * 60 * 60)

    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self._session = requests.Session()
        self._token = None
        self._token_expires_at = datetime.datetime.fromtimestamp(0)

    def _request(self, method, url, params=None, data=None, json=None, auth=True, **kwargs):
        full_url = urllib.parse.urljoin(self.host, url)
        if auth:
            headers = {"X-Auth": self.token}
        else:
            headers = {}
        headers.update(kwargs.pop("headers", {}))
        resp = self._session.request(method, full_url, params=params, data=data, json=json, headers=headers, **kwargs)
        resp.raise_for_status()
        return resp

    @property
    def token(self):
        if self._token is None or self._token_expires_at <= datetime.datetime.now():
            self._token = self.login()
            self._token_expires_at = datetime.datetime.now() + self.TOKEN_AGE
        return self._token

    def login(self):
        params = {
            "username": self.username,
            "password": self.password,
            "recaptcha": "",
        }
        resp = self._request("POST", "/api/login", json=params, auth=False)
        token = resp.text
        return token

    def upload(self, local_filename, remote_filename, override=True):
        headers = {}
        content_type, _ = mimetypes.guess_type(local_filename)
        if content_type:
            headers = {"Content-Type": content_type}
        params = {"override": override and "true" or "false"}
        url = f"/api/resources/{urllib.parse.quote(remote_filename)}"
        with open(local_filename, "rb") as f:
            self._request("POST", url, params=params, data=f, headers=headers)

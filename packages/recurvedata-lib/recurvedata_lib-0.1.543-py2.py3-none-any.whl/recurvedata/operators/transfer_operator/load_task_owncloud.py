import os

try:
    import owncloud
except ImportError:
    pass
import logging

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator.task import LoadTask
from recurvedata.pigeon.utils import fs, trim_suffix

logger = logging.getLogger(__name__)


class OwnCloudLoadTask(LoadTask):
    ds_name_fields = ("data_source_name",)
    ds_types = ("owncloud",)
    should_write_header = True
    worker_install_require = [
        "pyocclient>=0.6",
    ]

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

        client = OwnCloudClient(ds.host, ds.user, ds.password)

        remote_fold = conf["directory"]
        remote_filename = os.path.join(conf["directory"], remote_filename)
        logger.info("uploading %s to %s", file_to_upload, remote_filename)
        client.upload(file_to_upload, remote_fold, remote_filename)
        fs.remove_files_safely([self.filename, file_to_upload])
        logger.info(f"remove {self.filename} local_file: {file_to_upload} success!")

    @classmethod
    def config_schema(cls):
        schema = {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": _l("OwnCloud Connection"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": cls.ds_types,
                    },
                    # 'default': cls.first_or_default(dss, ''),
                },
                "directory": {
                    "type": "string",
                    "title": _l("Target Directory"),
                    "description": _l("Target directory to upload files to"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "filename": {
                    "type": "string",
                    "title": _l("Filename"),
                    "description": _l("Uploaded file name, supports template variables"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "compress_method": {
                    "type": "string",
                    "title": _l("Compression Method"),
                    "description": _l("Compress file before uploading using specified method"),
                    "enum": ["None", "Gzip", "Zip"],
                    "enumNames": ["None", "Gzip", "Zip"],
                    "default": "None",
                },
            },
            "required": ["data_source_name", "directory", "filename", "compress_method"],
        }
        return schema


class OwnCloudClient(object):
    # ownCloud没有提供API关闭客户端，只需要停止与ownCloud服务器交互，Python脚本就会自动关闭连接。
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.oc = self.login()

    def login(self):
        try:
            owncloud_client = owncloud.Client(self.host)
            owncloud_client.login(self.username, self.password)
            logger.info("login owncloud success.")
        except Exception as e:
            logger.info("login owncloud failed. http error is: {}".format(e))
        return owncloud_client

    def create_owncloud_fold(self, fold):
        try:
            self.oc.file_info(fold)
            logger.info("fold {} is exists.".format(fold))
        except Exception as e:
            logger.info("{} does not exists, start creating the folder. error is: {}".format(fold, e))
            self.oc.mkdir(fold)
            logger.info("create {} success.".format(fold))

    def upload(self, local_filename, remote_fold, remote_filename):
        self.create_owncloud_fold(remote_fold)
        logger.info("start put {} to {}.".format(local_filename, remote_filename))
        try:
            self.oc.put_file(remote_path=remote_filename, local_source_file=local_filename)
            logger.info("upload {} success.".format(remote_filename))
        except Exception as e:
            logger.info("upload {} failed. http error is: {}".format(remote_filename, e))

import logging
import os

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator.task import LoadTask
from recurvedata.utils.files import remove_files_safely

logger = logging.getLogger(__name__)


class SFTPLoadTask(LoadTask):
    ds_name_fields = ("data_source_name",)
    ds_types = ("sftp",)
    should_write_header = True
    worker_install_require = ["pigeon[sftp]"]

    def execute_impl(self, *args, **kwargs):
        conf = self.rendered_config
        ds = self.must_get_connection_by_name(conf["data_source_name"])

        cm = conf["compress_method"]
        file_to_upload, ext = self.compress_file(filename=self.filename, compress_mode=cm)
        remote_filename = conf["filename"]
        if cm != "None" and not remote_filename.endswith(ext):
            remote_filename = f"{remote_filename}{ext}"

        self.ensure_directory_exists(ds, conf)
        remote_filename = os.path.join(conf["directory"], remote_filename)

        logger.info("uploading %s to %s", file_to_upload, remote_filename)
        ds.connector.upload_file(file_to_upload, remote_filename)
        remove_files_safely([self.filename, file_to_upload])

    @staticmethod
    def ensure_directory_exists(ds, conf):
        sftp = ds.connector
        # 确保目录存在
        try:
            sftp.sftp.listdir(conf["directory"])
        except OSError:
            logger.warning("failed to list directory %s, maybe not exists, try to make it", conf["directory"])
            # 这一步可以抛出异常，需要人工介入
            sftp.sftp.mkdir(conf["directory"])

    @classmethod
    def config_schema(cls):
        # get_choices_by_type = cls.get_connection_names_by_type
        # dss = get_choices_by_type(cls.ds_types)
        schema = {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": _l("SFTP Connection"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": cls.ds_types,
                    },
                    # 'default': cls.first_or_default(dss, ''),
                },
                "directory": {
                    "type": "string",
                    "title": _l("Upload Path"),
                    "description": _l("The directory to upload the file to, Jinja template supported"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "filename": {
                    "type": "string",
                    "title": _l("Filename"),
                    "description": _l("The filename to save as, Jinja template supported"),
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
            "required": ["data_source_name", "filename", "compress_method"],
        }
        return schema

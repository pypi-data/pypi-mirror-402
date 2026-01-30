import logging
import os

try:
    from recurvedata.pigeon.connector.google_cloud_storage import GoogleCloudStorageConnector
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator.task import LoadTask
from recurvedata.utils import extract_dict
from recurvedata.utils.files import is_file_empty, remove_files_safely

logger = logging.getLogger(__name__)


class GoogleCloudStorageLoadTask(LoadTask):
    ds_name_fields = ("data_source_name",)
    ds_types = ("google_cloud_storage",)
    should_write_header = True
    worker_install_require = ["pigeon[google_bigquery]"]

    def execute_impl(self, *args, **kwargs):
        if is_file_empty(self.filename):
            logger.warning("file %s not exists or has no content, skip.", self.filename)
            return

        ds = self.must_get_connection_by_name(self.config["data_source_name"])

        load_options = self.rendered_config.copy()
        ds_extra_bucket = ds.extra.get("bucket")
        config_bucket = load_options.get("bucket_name")
        bucket_upload = config_bucket if config_bucket else ds_extra_bucket

        opt_keys = ["key_path", "key_dict", "project", "proxies", "bucket_name"]
        gcs = GoogleCloudStorageConnector(**extract_dict(ds.extra, opt_keys))

        # 文件压缩
        compress_mode = load_options["compress_mode"]
        if compress_mode != "None" and not load_options["key"].endswith(("/",)):
            target_filename = os.path.join(os.path.dirname(self.filename), os.path.basename(load_options["key"]))
        else:
            target_filename = None
        file_upload, ext = self.compress_file(
            filename=self.filename, target_filename=target_filename, compress_mode=compress_mode
        )
        if compress_mode != "None" and not load_options["key"].endswith(("/", ext)):
            load_options["key"] = f"{load_options['key']}{ext}"

        # 根据 key 的内容创建 upload 方法需要的 key, folder 参数
        upload_conf = {
            "bucket_name": bucket_upload,
            "filename": file_upload,
            "overwrite": load_options["overwrite"],
        }
        if load_options["key"].endswith("/"):
            upload_conf.update({"folder": load_options["key"]})
        elif load_options["key"]:
            upload_conf.update({"key": load_options["key"]})
        else:
            upload_conf.update({"key": os.path.basename(file_upload)})

        if ext == ".zip":
            upload_conf["filename"] += ext

        logger.info("uploading...")
        logger.info(upload_conf)
        gcs.upload(**upload_conf)
        return remove_files_safely([self.filename, file_upload])

    @classmethod
    def config_schema(cls):
        # get_choices_by_type = cls.get_connection_names_by_type
        # dss = get_choices_by_type(cls.ds_types)
        schema = {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": _l("GCS Connection"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": cls.ds_types,
                    },
                    # 'default': cls.first_or_default(dss, ''),
                },
                "bucket_name": {
                    "type": "string",
                    "title": _l("GCS Bucket Name"),
                    "description": _l(
                        "The name of the Google Cloud Storage bucket to upload files to. This is required if not already configured in the data source connection."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "key": {
                    "type": "string",
                    "title": _l("Upload Path"),
                    "description": _l(
                        "Target path in the bucket. Can be an object key or folder path (ending with /). "
                        "Supports Jinja templating."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "compress_mode": {
                    "type": "string",
                    "title": _l("Compression Method"),
                    "description": _l("Compress file before uploading using specified method"),
                    "enum": ["None", "Gzip", "Zip"],
                    "enumNames": ["None", "Gzip", "Zip"],
                    "default": "None",
                },
                "overwrite": {
                    "type": "boolean",
                    "title": _l("Overwrite Existing"),
                    "description": _l("Whether to overwrite if target object already exists"),
                    "default": True,
                },
            },
            "required": ["compress_mode", "data_source_name", "key"],
        }
        return schema

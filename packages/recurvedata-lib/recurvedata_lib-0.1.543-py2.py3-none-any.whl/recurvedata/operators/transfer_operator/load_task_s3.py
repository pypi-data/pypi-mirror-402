import json
import logging
import os

import jsonschema

try:
    from recurvedata.pigeon.connector import new_s3_connector
    from recurvedata.pigeon.utils import fs
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator.task import LoadTask

logger = logging.getLogger(__name__)


class S3LoadTask(LoadTask):
    ds_name_fields = ("data_source_name",)
    ds_types = ("s3",)
    should_write_header = True
    worker_install_require = ["pigeon"]

    def execute_impl(self, *args, **kwargs):
        if fs.is_file_empty(self.filename):
            logger.warning("file %s not exists or has no content, skip.", self.filename)
            return

        s3_ds = self.must_get_connection_by_name(self.config["data_source_name"])

        load_options = self.rendered_config.copy()
        ds_extra_bucket = s3_ds.extra.get("bucket")
        config_bucket = load_options.get("bucket_name")
        bucket_upload = config_bucket if config_bucket else ds_extra_bucket

        # 文件压缩
        compress_mode = load_options["compress_mode"]
        file_upload, ext = self.compress_file(filename=self.filename, compress_mode=compress_mode)
        if compress_mode != "None" and not load_options["key"].endswith(("/", ext)):
            load_options["key"] = f"{load_options['key']}{ext}"

        # s3 connector 配置项
        s3_conf = s3_ds.extra.copy()
        if load_options.get("proxies"):
            s3_conf["proxies"] = json.loads(load_options["proxies"])

        # 创建 connector，如果不选择自动创建 Bucket，不存在则报错
        s3 = new_s3_connector(conf=s3_conf)
        if not load_options.get("auto_create_bucket") and config_bucket:
            if not s3.has_bucket(bucket_name=config_bucket):
                raise ValueError("Bucket not exists")

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

        logger.info("uploading ...")
        s3.upload(**upload_conf)
        return fs.remove_files_safely([self.filename, file_upload])

    @classmethod
    def validate(cls, configuration):
        config = super().validate(configuration)

        if not config.get("bucket_name"):
            s3_ds = cls.must_get_connection_by_name(configuration["data_source_name"])
            if not s3_ds.extra.get("bucket"):
                raise jsonschema.ValidationError(message="Unknown Bucket", path=("bucket_name",))
        return config

    @classmethod
    def config_schema(cls):
        # get_choices_by_type = cls.get_connection_names_by_type
        # dss = get_choices_by_type(cls.ds_types)
        schema = {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": _l("S3 Connection"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": cls.ds_types,
                    },
                    # 'default': cls.first_or_default(dss, ''),
                },
                "bucket_name": {
                    "type": "string",
                    "title": _l("Bucket"),
                    "description": _l("S3 bucket name, required if not set in data source"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                # "auto_create_bucket": {
                #     "type": "boolean",
                #     "title": "Auto Create Bucket",
                #     "default": False,
                #     "description": "如果 Bucket 不存在，是否需要按输入创建 Bucket，命名规则见 https://amzn.to/2HL8VDX",
                # },
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
                "proxies": {
                    "type": "string",
                    "title": _l("Proxies"),
                    "description": _l('HTTP/HTTPS proxy to use. Format: {"https": "http://example.com:3128"}'),
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
            "required": ["compress_mode", "data_source_name"],
        }
        return schema

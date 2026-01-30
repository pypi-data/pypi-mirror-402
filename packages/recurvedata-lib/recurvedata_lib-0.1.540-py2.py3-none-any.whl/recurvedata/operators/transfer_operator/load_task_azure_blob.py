import logging
import os

import jsonschema

try:
    from recurvedata.pigeon.utils import fs
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator.task import LoadTask

logger = logging.getLogger(__name__)


class AzureBlobStorageLoadTask(LoadTask):
    ds_name_fields = ("data_source_name",)
    ds_types = ("azure_blob",)
    should_write_header = True
    worker_install_require = ["pigeon"]

    def execute_impl(self, *args, **kwargs):
        if fs.is_file_empty(self.filename):
            logger.warning("file %s not exists or has no content, skip.", self.filename)
            return

        azure_blob_ds = self.must_get_connection_by_name(self.config["data_source_name"])

        azure_blob = azure_blob_ds.connector
        # 是否自动创建 container
        config_container = self.rendered_config["container"] or azure_blob_ds.extra.get("container")
        # if not self.rendered_config['auto_create_container'] and config_container:
        #     if not azure_blob.exists(container_name=config_container):
        #         raise ValueError(f'{config_container} not exists')

        # compress or not
        compress_mode = self.rendered_config["compress_mode"]
        file_upload, _ = self.compress_file(filename=self.filename, compress_mode=compress_mode)

        blob_name = self.rendered_config["blob"] or os.path.basename(self.filename)
        logger.info(f"uploading {file_upload} to {config_container}/{blob_name}...")
        config = {
            "blob_name": blob_name,
            "overwrite": self.rendered_config["overwrite"],
            "local_file_path": file_upload,
            "container_name": config_container,
        }
        azure_blob.upload(**config)
        fs.remove_files_safely([self.filename, file_upload])

    @classmethod
    def validate(cls, configuration):
        config = super().validate(configuration)
        must_get_by_name = cls.must_get_connection_by_name

        if not config.get("container"):
            azure_blob = must_get_by_name(configuration["data_source_name"])
            if not azure_blob.extra.get("container"):
                # ensure container
                raise jsonschema.ValidationError(message="Unknown Container", path=("container",))
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
                    "title": _l("Azure Blob Connection"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": cls.ds_types,
                    },
                    # 'default': cls.first_or_default(dss, ''),
                },
                "container": {
                    "type": "string",
                    "title": _l("Container"),
                    "description": _l("Container name, required if not set in data source"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "blob": {
                    "type": "string",
                    "title": _l("Blob Name"),
                    "description": _l("Blob name in the container. Jinja templating is supported."),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "compress_mode": {
                    "type": "string",
                    "title": _l("Compression Method"),
                    "description": _l("Compress file before uploading using specified method"),
                    "enum": ["None", "Gzip", "Zip", "Bzip2"],
                    "enumNames": ["None", "Gzip", "Zip", "Bzip2"],
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

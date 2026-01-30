import csv
import inspect
import logging
import os

import jsonschema

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator.const import FILE_TRANSFORM_FUNC_DEFAULT_VALUE
from recurvedata.operators.transfer_operator.mixin import HiveTextfileConverterMixin
from recurvedata.operators.transfer_operator.task import DumpTask
from recurvedata.operators.utils import file_factory as ff
from recurvedata.utils import unescape_backslash

logger = logging.getLogger(__name__)


class SFTPDumpTask(DumpTask, HiveTextfileConverterMixin):
    ds_name_fields = ("data_source_name",)

    def execute_impl(self, *args, **kwargs):
        conf = self.rendered_config

        ds = self.must_get_connection_by_name(conf["data_source_name"])
        ds.connector.download_file(conf["filepath"], self.filename)

        filename = self.process_file(conf)
        filename = self.transform_file(conf, filename)

        if filename != self.filename:
            logger.info("renaming %s to %s", filename, self.filename)
            os.rename(filename, self.filename)

        # TODO: pigeon loader 要支持不同的文件格式
        self.convert_csv_to_hive_text_if_needed()
        return None

    def process_file(self, conf):
        filename = self.filename
        if conf["decompress"] == "Gzip":
            logger.info("decompressing %s using gzip", self.filename)
            filename = ff.gzip_decompress(self.filename, inplace=True)

        skip_head_lines = conf.get("skip_head_lines", 0)
        if conf["file_format"] == "Excel":
            logger.info("converting Excel to CSV...")
            filename = ff.convert_excel_to_csv(filename, skiprows=skip_head_lines, inplace=True)
        if conf["file_format"] == "JSONLines":
            logger.info("converting JSON lines to CSV...")
            filename = ff.convert_jsonlines_to_csv(
                filename, skiprows=skip_head_lines, src_encoding=conf["encoding"], inplace=True
            )
        if conf["file_format"] == "CSV":
            logger.info("converting CSV dialect and encoding if necessary...")
            dialect_options = self._get_custom_csv_options(conf)
            filename = ff.convert_csv_dialect(
                filename,
                src_dialect_options=dialect_options,
                skiprows=skip_head_lines,
                src_encoding=conf["encoding"],
                inplace=True,
            )
        return filename

    def transform_file(self, conf, filename):
        transform_func_code = conf.get("transform_func", "").strip()
        if not transform_func_code:
            return filename

        func = validate_transform(transform_func_code)
        if not func:
            return filename

        logger.info("calling transform function with %s", (filename,))
        result_file = func(filename)
        if result_file is None or not (isinstance(result_file, str) and os.path.isabs(result_file)):
            raise ValueError("transform must return an absolute filepath, got %s instead", result_file)
        logger.info("got %s", result_file)
        return result_file

    def _get_custom_csv_options(self, conf):
        rv = {
            "delimiter": unescape_backslash(conf["csv_delimiter"]),
            "lineterminator": unescape_backslash(conf["csv_lineterminator"]),
        }
        quoting = conf["csv_quoting"]
        rv["quoting"] = {
            "QUOTE_ALL": csv.QUOTE_ALL,
            "QUOTE_MINIMAL": csv.QUOTE_MINIMAL,
            "QUOTE_NONE": csv.QUOTE_NONE,
            "QUOTE_NONNUMERIC": csv.QUOTE_NONNUMERIC,
        }[quoting]
        return rv

    @classmethod
    def config_schema(cls):
        return {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": _l("SFTP Connection"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": [
                            "sftp",
                        ],
                    },
                },
                "filepath": {
                    "type": "string",
                    "title": _l("Source File Path"),
                    "description": _l(
                        "Absolute path to the file on FTP server (e.g. /path/to/file.csv). Supports Jinja templating."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "decompress": {
                    "type": "string",
                    "title": _l("Decompression Method"),
                    "description": _l("Decompress downloaded file using specified method"),
                    "enum": ["None", "Gzip"],
                    "enumNames": ["None", "Gzip"],
                    "default": "None",
                },
                "file_format": {
                    "type": "string",
                    "title": _l("Input Format"),
                    "description": _l("Format of the source file to be converted to CSV"),
                    "enum": ["CSV", "Excel", "JSONLines"],
                    "enumNames": ["CSV", "Excel", "JSONLines"],
                    "default": "CSV",
                },
                "skip_head_lines": {
                    "type": "number",
                    "ui:options": {"controls": False},
                    "title": _l("Skip Header Rows"),
                    "description": _l("Number of rows to skip from the beginning of the file"),
                    "default": 0,
                    "minimum": 0,
                },
                "encoding": {
                    "ui:hidden": '{{parentFormData.file_format !== "CSV"}}',
                    "type": "string",
                    "title": _l("File Encoding"),
                    "description": _l("Character encoding of the CSV file (e.g. utf-8, gbk)"),
                    "default": "utf-8",
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "csv_delimiter": {
                    "ui:hidden": '{{parentFormData.file_format !== "CSV"}}',
                    "type": "string",
                    "title": _l("Field Delimiter"),
                    "description": _l("Character used to separate fields in the CSV file"),
                    "default": ",",
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "csv_lineterminator": {
                    "ui:hidden": '{{parentFormData.file_format !== "CSV"}}',
                    "type": "string",
                    "title": _l("Line Ending"),
                    "description": _l("Character sequence used to terminate lines"),
                    "enum": [r"\n", r"\r\n"],
                    "enumNames": [r"\n", r"\r\n"],
                    "default": r"\r\n",
                },
                "csv_quoting": {
                    "ui:hidden": '{{parentFormData.file_format !== "CSV"}}',
                    "type": "string",
                    "title": _l("Field Quoting"),
                    "description": _l("Strategy for quoting fields in the CSV file"),
                    "enum": ["QUOTE_ALL", "QUOTE_MINIMAL", "QUOTE_NONE", "QUOTE_NONNUMERIC"],
                    "enumNames": ["QUOTE_ALL", "QUOTE_MINIMAL", "QUOTE_NONE", "QUOTE_NONNUMERIC"],
                    "default": "QUOTE_MINIMAL",
                },
                "transform_func": {
                    "type": "string",
                    "title": _l("Custom Transformation"),
                    "description": _l(
                        "Python function to transform the downloaded file. Must accept a filepath argument and return "
                        "the path to the transformed file. Runs after built-in transformations."
                    ),
                    "default": FILE_TRANSFORM_FUNC_DEFAULT_VALUE,
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "python",
                    },
                },
            },
            "required": ["data_source_name", "filepath"],
        }

    @classmethod
    def validate(cls, configuration):
        conf = super().validate(configuration)

        transform_func_code = conf.get("transform_func", "").strip()
        if transform_func_code:
            validate_transform(transform_func_code)
        return conf


def validate_transform(raw_code):
    code = compile(raw_code, "", "exec")
    ns = {}
    exec(code, ns)
    func = ns.get("transform")
    if not func:
        return None

    if not callable(func):
        raise jsonschema.ValidationError(message="transform should be callable", path=("transform_func",))

    sig = inspect.signature(func)
    if tuple(sig.parameters.keys()) != ("filename",):
        raise jsonschema.ValidationError(
            message="transform must accept and only accept filename as parameter", path=("transform_func",)
        )
    return func

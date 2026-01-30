import csv
import glob
import logging
import os

import cytoolz as toolz

from recurvedata.pigeon import const
from recurvedata.pigeon.csv import CSV
from recurvedata.pigeon.handler.base import Handler, HandlerFactory
from recurvedata.pigeon.row_factory import get_row_keys
from recurvedata.pigeon.schema import Schema
from recurvedata.pigeon.utils import escape, extract_dict, fs
from recurvedata.pigeon.utils.json import json_dumps

logger = logging.getLogger(__name__)


class CSVFileHandler(Handler):
    def __init__(
        self,
        filename=None,
        encoding=None,
        write_header=False,
        null=None,
        delimiter=",",
        quoting=csv.QUOTE_ALL,
        escapechar=None,
        doublequote=True,
        **kwargs,
    ):
        """Transform rows and write result as CSV file.

        :param filename: result filename
        :param encoding: encoding
        :param write_header: writer headers or not
        """
        if filename is None:
            filename = fs.new_tempfile(suffix=".csv")
        self.filename = os.path.abspath(filename)
        if os.path.exists(self.filename):
            logger.info(f"found {filename}, remove before writing")
            os.unlink(self.filename)

        self.encoding = encoding
        self.null = null
        self._fd = None
        self._writer = None
        self.writer_header = write_header
        self._field_names = None

        self.csv_options = {k: v for k, v in kwargs.items() if k not in self.ERROR_HANDLE_PARAMS}
        self.csv_options.update(
            {"delimiter": delimiter, "quoting": quoting, "escapechar": escapechar, "doublequote": doublequote}
        )
        super().__init__(**extract_dict(kwargs, self.ERROR_HANDLE_PARAMS))

    def flush(self):
        if self._fd is not None:
            self._fd.flush()

    def close(self):
        super().close()

        if self._fd is not None:
            self._fd.close()

    def reset(self):
        super().reset()
        if self._fd is not None:
            self._fd.seek(0)
            self._fd.truncate(0)
            self._fd.close()
            self._fd = self._writer = None

    def _open_writer(self, row):
        self._fd = open(self.filename, "w", newline="", encoding=self.encoding)

        self._determine_header(row)

        if isinstance(row, dict):
            self._writer = csv.DictWriter(self._fd, fieldnames=self._field_names, **self.csv_options)
            if self.writer_header:
                self._writer.writeheader()
        else:
            self._writer = csv.writer(self._fd, **self.csv_options)
            if self.writer_header:
                self._writer.writerow(self._field_names)

    def _determine_header(self, row):
        logger.info("try to get schema from row (%s)", type(row))
        field_names = get_row_keys(row)
        if not field_names:
            logger.info("try to get schema from transformer")
            if self.transformer.output_schema is not None:
                field_names = [x.name for x in self.transformer.output_schema]
        logger.info("header: %s", field_names)
        self._field_names = field_names

    def emit(self, row):
        if not isinstance(row, list):
            row = [row]

        if self._fd is None:
            self._open_writer(row[0])

        for r in row:
            self._writerow(r)

        return len(row)

    def _writerow(self, row):
        if isinstance(row, dict):
            row = toolz.valmap(self._escape_item, row)
        else:
            row = [self._escape_item(x) for x in row]
        self._writer.writerow(row)

    def _escape_item(self, v):
        if v is None:
            return self.null

        # Handle dict, tuple, set and list
        if isinstance(v, (dict, tuple, set, list)):
            v = json_dumps(v, ensure_ascii=False)

        if isinstance(v, str):
            return escape.escape_string(v)
        return v

    def __str__(self):
        return "<{} (filename={})>".format(self.__class__.__name__, self.filename)


class HiveCSVFileHandler(CSVFileHandler):
    """
    The default file format of Hive is not CSV, but only delimiter-ed text file.
    """

    def __init__(
        self,
        filename=None,
        encoding=None,
        write_header=False,
        null=const.HIVE_NULL,
        delimiter=const.HIVE_FIELD_DELIMITER,
        quoting=csv.QUOTE_NONE,
        **csv_options,
    ):
        super().__init__(filename, encoding, write_header, null, delimiter, quoting, **csv_options)
        self.delimiter = delimiter

    def _writerow(self, row):
        if isinstance(row, dict):
            line = self.format_line(row.values())
        else:
            line = self.format_line(row)

        self._fd.write(line)
        self._fd.write("\n")

    def _escape_item(self, v):
        v = super()._escape_item(v)
        return str(v)

    def format_line(self, row):
        values = map(self._escape_item, row)
        return self.delimiter.join(values)


class CSVFileHandlerFactory(HandlerFactory):
    def __init__(
        self, handler_class=CSVFileHandler, filename=None, encoding=None, write_header=False, merge_files=True, **kwargs
    ):
        self.filename = filename or fs.new_tempfile(".csv")
        self.merge_files = merge_files
        options = {"filename": self.filename, "encoding": encoding, "write_header": write_header}
        options.update(kwargs)
        super().__init__(handler_class=handler_class, **options)

        self._saved_schema = False

    def meta_name(self):
        return f"<{self.__class__.__name__} ({self.filename})>"

    def create_handler(self, **kwargs):
        filename = f'{self.handler_options["filename"]}.{len(self.handlers)}'
        return super().create_handler(filename=filename)

    def join(self):
        if not self.handlers:
            return

        files = [h.filename for h in self.handlers if not fs.is_file_empty(h.filename)]
        if not files:
            return

        if self.merge_files:
            has_header = self.handler_options.get("write_header", False)
            logger.info("files have header: %s", has_header)
            logger.info("merging files %s into %s", files, self.filename)
            if not has_header:
                fs.merge_files(files, self.filename)
            else:
                base_file = files[0]  # keep header
                target = fs.merge_files(files[1:], num_skip_lines=1)
                fs.merge_files([base_file, target], self.filename)

        self.save_output_schema()

    def _determine_output_schema(self):
        if self.transformer.output_schema is not None:
            # list of Fields
            if isinstance(self.transformer.output_schema, list):
                return Schema(self.transformer.output_schema)
            return self.transformer.output_schema

        if self.handler_options.get("write_header", False):
            csv_options = self.handlers[0].csv_options
            if self.merge_files:
                f = self.filename
            else:
                # use the first non-empty file
                f = toolz.first(x for x in glob.glob(f"{self.filename}.[0-9]*") if os.path.getsize(x))
            csv_proxy = CSV(path=f, encoding=self.handler_options["encoding"], **csv_options)
            return csv_proxy.infer_schema()
        return None

    def save_output_schema(self):
        schema = self._determine_output_schema()
        if not schema:
            logger.warning("could not able to infer output schema")
            return

        filename = fs.schema_filename(self.filename)
        logger.info("saving output schema to %s", filename)
        schema.dump(filename)
        self._saved_schema = True
        return filename

    def handle_dumper_schema(self, schema):
        filename = fs.schema_filename(self.filename)
        if self._saved_schema and os.path.exists(filename):
            logger.info("file %s already exists, pass", filename)
            return

        if not isinstance(schema, Schema):
            raise TypeError(f"got {type(schema)}")

        logger.info("saving dumper schema to %s", filename)
        schema.dump(filename)
        return filename


def create_csv_file_handler_factory(
    filename=None, encoding=None, write_header=False, hive=False, transformer=None, merge_files=True, **kwargs
):
    if hive:
        handler_class = HiveCSVFileHandler
    else:
        handler_class = CSVFileHandler

    factory = CSVFileHandlerFactory(
        handler_class=handler_class,
        filename=filename,
        encoding=encoding,
        write_header=write_header,
        merge_files=merge_files,
        **kwargs,
    )
    if transformer is not None:
        factory.set_transformer(transformer)
    return factory


def convert_csv_to_hive_textfile(filename, folder=None, replace=False, has_header=False, **csv_options):
    new_name = fs.new_tempfile(prefix=os.path.basename(filename), dir=folder)
    handler = HiveCSVFileHandler(filename=new_name)
    with open(filename, newline="") as fd:
        if has_header:
            fd.readline()

        reader = csv.reader(fd, **csv_options)
        for row in reader:
            handler.handle(tuple(row))
    handler.close()

    if replace:
        os.rename(new_name, filename)
    return new_name

# flake8: noqa: E402

# pylint: disable=wrong-import-position

import os
import re
import shutil
from typing import List, Optional, Union

import pyhive.hive

_ = 0  # prevent PyCharm to auto-format
import cytoolz as toolz

# impyla breaks TCLIService, which leads to ImportError while importing pyhive
# see https://github.com/cloudera/impyla/issues/277
import impala.dbapi
import sqlalchemy
from impala.error import HiveServer2Error
from pyhive.exc import OperationalError

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.connector.dbapi import DBAPIConnector, _ShowTableLikeMixin
from recurvedata.pigeon.connector.hdfs import HDFSCliConnector, HDFSConnector
from recurvedata.pigeon.const import HIVE_FILE_FORMATS
from recurvedata.pigeon.schema import types
from recurvedata.pigeon.utils import ensure_list, trim_suffix
from recurvedata.pigeon.utils.sql import sqlformat

_hive_type_to_canonical_type = {
    "BOOLEAN": types.BOOLEAN,
    "TINYINT": types.INT8,
    "SMALLINT": types.INT16,
    "INT": types.INT32,
    "BIGINT": types.INT64,
    "FLOAT": types.FLOAT32,
    "DOUBLE": types.FLOAT64,
    "DECIMAL": types.FLOAT64,
    "REAL": types.FLOAT64,
    "TIMESTAMP": types.DATETIME,
    "DATE": types.DATE,
    "CHAR": types.STRING,
    "VARCHAR": types.STRING,
    "STRING": types.STRING,
}

_canonical_type_to_hive_type = {
    types.BOOLEAN: "BOOLEAN",
    types.INT8: "TINYINT",
    types.INT16: "SMALLINT",
    types.INT32: "INT",
    types.INT64: "BIGINT",
    types.FLOAT32: "DOUBLE",
    types.FLOAT64: "DOUBLE",
    # treat date, datetime as string
    types.DATE: "STRING",
    types.DATETIME: "STRING",
    types.STRING: "STRING",
    types.JSON: "STRING",
}


class _HiveSQLMixin:
    def create_partition_table_like(self, table, like_table, partitions):
        """建一个分区表 Like 已有的一个未分区的表，并添加分区键"""
        if not self.has_table(like_table):
            raise ValueError(f"like table {like_table!r} not exists")
        partitions = [f"`{pname}` {ptype}" for pname, ptype in partitions.items()]
        partitions = ", ".join(partitions)
        with self.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {like_table} LIMIT 0")
            columns = [(x[0], x[1]) for x in cursor.description]
        columns = ",\n".join("{} {}".format(*x) for x in columns)
        sql = f"""
            CREATE TABLE {table} (
                {columns}
            ) PARTITIONED BY ({partitions})
        """
        self.execute(sqlformat(sql))

    def is_table_partitioned(self, database, table):
        with self.cursor() as cursor:
            try:
                # 查看表的分区情况，如果没有报错就返回True
                cursor.execute(f"SHOW PARTITIONS {database}.{table}")
                return True
            except (OperationalError, HiveServer2Error) as e:
                msg = str(e).lower()
                if "table not found" in msg or "table does not exist:" in msg:
                    return False
                elif "is not a partitioned table" in msg or "table is not partitioned" in msg:
                    return False
                else:
                    raise e

    @staticmethod
    def to_canonical_type(type_code, size):
        type_code = trim_suffix(type_code, "_TYPE")
        return _hive_type_to_canonical_type.get(type_code, types.STRING)

    @staticmethod
    def from_canonical_type(canonical_type, size):
        return _canonical_type_to_hive_type.get(canonical_type, "STRING")

    def generate_create_table_ddl(self, name, schema, **kwargs):
        cols = []
        for f in schema:
            col_name = self.quote_identifier(f.name)
            if f.comment:
                cols.append(f"{col_name} {self.from_canonical_type(f.type, f.size)} COMMENT {f.comment!r}")
            else:
                cols.append(f"{col_name} {self.from_canonical_type(f.type, f.size)}")

        file_format = kwargs.get("file_format", "PARQUET")
        col_types = ", \n".join(cols)
        name = self.quote_identifier(name)
        ddl = f"CREATE TABLE {name} (\n{col_types}\n) STORED AS {file_format}"
        return ddl


@register_connector_class("hive")
class HiveConnector(_ShowTableLikeMixin, _HiveSQLMixin, DBAPIConnector):
    _sqla_driver = "hive"
    _log_query = False
    _default_port = 10000

    _complex_types = ("array", "map", "struct")

    def connect_impl(self, autocommit=False, *args, **kwargs):
        params = {
            "host": self.host,
            "port": self.port,
            "username": self.user,
            "database": self.database or "default",
        }
        if self.password:
            params.update({"password": self.password, "auth": self.kwargs["auth"]})
        hive_conf = self.hive_conf
        hive_conf.update(kwargs.get("hive_conf", {}))
        if hive_conf:
            params["configuration"] = hive_conf
        return pyhive.hive.connect(**params)

    def create_engine(self, engine_kwargs=None, url_queries=None):
        return sqlalchemy.create_engine("hive://", creator=self.connect)

    def is_hive(self):
        return True

    @toolz.memoize
    def create_hdfs_connector(self) -> Optional[HDFSConnector]:
        hdfs_options = self.kwargs.get("hdfs_options")
        if not hdfs_options:
            return None
        return HDFSConnector(**hdfs_options)

    def has_complex_type_fields(self, table):
        table = self.quote_identifier(table)
        with self.cursor() as cursor:
            cursor.execute("DESCRIBE {}".format(table))
            for r in cursor.fetchall():
                if r[0] == "":
                    break
                has_complex = any(x in r[1].lower() for x in self._complex_types)
                if has_complex:
                    return True
        return False

    def get_columns(self, table, database=None, exclude=None):
        if database is None:
            database = self.database
        with self.cursor() as cursor:
            if not self.has_table(table, database, cursor=cursor):
                raise ValueError("Table {!r} not exists in {!r}".format(table, database))
            # Hive bug https://issues.apache.org/jira/browse/HIVE-12184
            cursor.execute("USE {}".format(self.quote_identifier(database)))
            cursor.execute("DESCRIBE {}".format(self.quote_identifier(table)))
            cols = []
            for r in cursor.fetchall():
                # the following is partition information
                if r[0] == "":
                    break
                cols.append(r[0])
        if exclude:
            cols = [x for x in cols if x not in exclude]
        return cols

    def load_local_file(self, table, filepath, overwrite=True):
        hdfs_clients = []
        hdfs_cli = shutil.which("hdfs")
        if hdfs_cli:
            hdfs = HDFSCliConnector(hdfs_cli)
            hdfs_clients.append(hdfs)
        webhdfs = self.create_hdfs_connector()
        if webhdfs:
            hdfs_clients.append(webhdfs)

        exc = None
        for hdfs in hdfs_clients:
            self.logger.info(f"try to load file using {hdfs}")
            try:
                self._load_local_file_to_hive_impl(table, filepath, hdfs, overwrite)
                self.logger.info("finished load files")
            except Exception as e:
                exc = e
                self.logger.exception(f"failed to load file using {hdfs}")
            else:
                exc = None
                break

        if exc:
            raise exc

    def _load_local_file_to_hive_impl(
        self, table: str, filepath: Union[str, List[str]], hdfs: HDFSConnector, overwrite=True
    ):
        staging_folder = self.kwargs.get("hdfs_options", {}).get("staging_folder", "/tmp")
        hdfs_folder = os.path.join(staging_folder, f"{self.database}_{table}_")
        hdfs.delete_file(hdfs_folder, recursive=True)
        hdfs.make_dir(hdfs_folder)
        hdfs.upload_files(ensure_list(filepath), hdfs_folder)
        query = f"LOAD DATA INPATH '{hdfs_folder}/*' {'OVERWRITE' if overwrite else ''} INTO TABLE {table}"
        self.execute(query)
        hdfs.delete_file(hdfs_folder, recursive=True)

    def generate_ddl(self, table, database=None, if_exists=True, file_format="text"):
        file_format = file_format.lower()
        if file_format not in HIVE_FILE_FORMATS:
            raise ValueError(f"Format {file_format!r} is not supported")
        if database is None:
            database = self.database
        if not self.has_table(table, database):
            raise ValueError(f"Table {table!r} not exists in {database!r}")

        with self.cursor() as cursor:
            cursor.execute(f"USE {self.quote_identifier(database)}")
            cursor.execute(f"SHOW CREATE TABLE {self.quote_identifier(table)}")
            result = cursor.fetchall()

        body = ""
        for r in result[1:]:
            if "ROW FORMAT" in r[0]:
                break
            body += r[0]
        if_exists_stmt = " IF NOT EXISTS " if if_exists else " "
        file_format_stmt = f" STORED AS {HIVE_FILE_FORMATS[file_format]}"
        return f"CREATE TABLE{if_exists_stmt}{self.quote_identifier(table)} ({body}{file_format_stmt}"

    def _add_leading_comment_impl(self, query, comment):
        comment = self._safe_comment(comment)
        return "-- {}\n{}".format(comment, query.strip("\n"))

    @property
    def hive_conf(self):
        """
        用于设置 hive query 的参数，与在 hive 里执行 set xxx=xxx 基本一致（数字需要用字符串形式）；
        字典类型，例如 {
                    'spark.yarn.queue': 'etl',
                    'spark.app.name': 'pigeon',
                    'spark.executor.instances': '3'
                  }
        注意字典里数字要写成字符串的形式
        """
        if "hive_conf" in self.kwargs:
            # 考虑到 hive_conf 都是单层 k,v ，不使用 deepcopy
            return self.kwargs["hive_conf"].copy()
        return {}

    def generate_load_staging_table_ddl(self, staging_table, table, database=None, exclude_columns=None):
        if database is None:
            database = self.database
        if exclude_columns:
            exclude_columns = [col.lower().replace("`", "") for col in exclude_columns]

        with self.cursor() as cursor:
            cursor.execute(f"USE {self.quote_identifier(database)}")
            cursor.execute(f"SHOW CREATE TABLE {self.quote_identifier(table)}")
            result = cursor.fetchall()

        body = pre_row = ""
        for r in result[1:]:
            row = r[0].lower().strip()
            if row.startswith("partitioned by ("):
                continue
            if row.startswith("comment"):
                continue
            if exclude_columns:
                col_name = row.split(" ")[0].strip("`")
                if col_name in exclude_columns:
                    continue
            if row.endswith(")"):
                row = ",".join(row.rsplit(")", 1))
            if row.startswith("row format"):
                pre_row = ")".join(pre_row.rsplit(",", 1))
                body += pre_row
                break
            body += pre_row
            pre_row = row

        return f"CREATE TABLE {self.quote_identifier(staging_table)} ({body}"


@register_connector_class("impala")
class ImpalaConnector(_ShowTableLikeMixin, _HiveSQLMixin, DBAPIConnector):
    _sqla_driver = "impala"
    _default_port = 21050

    def connect_impl(self, autocommit=False, *args, **kwargs):
        params = {
            "host": self.host,
            "port": self.port,
            "database": self.database or "default",
            "user": self.user,
            "password": self.password,
        }
        if "auth_mechanism" in self.kwargs:
            params["auth_mechanism"] = self.kwargs["auth_mechanism"]
        return impala.dbapi.connect(**params)

    def create_engine(self, engine_kwargs=None, url_queries=None):
        return sqlalchemy.create_engine("impala://", creator=self.connect)

    def is_impala(self):
        return True

    def get_columns(self, table, database=None, exclude=None):
        if database is None:
            database = self.database
        with self.cursor() as cursor:
            if not self.has_table(table, database, cursor=cursor):
                raise ValueError("Table {!r} not exists in {!r}".format(table, database))
            cursor.execute("DESCRIBE {}.{}".format(self.quote_identifier(database), self.quote_identifier(table)))
            cols = [x[0] for x in cursor.fetchall()]
        if exclude:
            cols = [x for x in cols if x not in exclude]
        return cols

    def invalidate_metadata(self, table=None):
        if table:
            table = self.quote_identifier(table)
        else:
            table = ""
        query = f"INVALIDATE METADATA {table}"
        self.execute(query)

    def refresh(self, table, compute_stats=True):
        table = self.quote_identifier(table)
        queries = "REFRESH {}".format(table)
        try:
            self.execute(queries)
        except Exception as e:
            self.logger.error(f"failed to refresh, err: {e}, use INVALIDATE")
            queries = "INVALIDATE METADATA {}".format(table)
            self.execute(queries)
        if compute_stats:
            queries = "COMPUTE INCREMENTAL STATS {}".format(table)
            self.execute(queries)

    def generate_ddl(self, table, database=None, if_exists=True, file_format="text"):
        file_format = file_format.lower()
        # ORC is not supported in Impala
        # https://www.cloudera.com/documentation/enterprise/5-12-x/topics/impala_file_formats.html
        if file_format == "orc" or file_format not in HIVE_FILE_FORMATS:
            raise ValueError(f"Format {file_format!r} is not supported")
        if database is None:
            database = self.database
        if not self.has_table(table, database):
            raise ValueError(f"Table {table!r} not exists in {database!r}")

        with self.cursor() as cursor:
            cursor.execute(f"USE {self.quote_identifier(database)}")
            cursor.execute(f"SHOW CREATE TABLE {self.quote_identifier(table)}")
            body = re.search(r"\.(.*)\nSTORED", cursor.fetchall()[0][0], flags=re.S).group(1)
        if_exists_stmt = " IF NOT EXISTS " if if_exists else " "
        file_format_stmt = f" STORED AS {HIVE_FILE_FORMATS[file_format]}"
        return f"CREATE TABLE{if_exists_stmt}{body}{file_format_stmt}"

    @toolz.memoize
    def create_hdfs_connector(self):
        hdfs_options = self.kwargs.get("hdfs_options")
        if not hdfs_options:
            return None
        return HDFSConnector(**hdfs_options)

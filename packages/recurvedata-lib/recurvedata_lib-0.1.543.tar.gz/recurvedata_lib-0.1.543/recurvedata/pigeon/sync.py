import logging
import os.path
from urllib.parse import urlparse

from slugify import slugify

from recurvedata.pigeon.connector import get_connector, get_connector_class
from recurvedata.pigeon.const import LOAD_APPEND, LOAD_MERGE
from recurvedata.pigeon.handler.csv_handler import create_csv_file_handler_factory
from recurvedata.pigeon.loader import CSVToHiveLoader, CSVToMySQLLoader, CSVToRedshiftLoader
from recurvedata.pigeon.utils import ensure_list, fs

logger = logging.getLogger(__name__)


def _parse_db_table(db_table):
    t_db_table = db_table.split(".")
    if len(t_db_table) == 2:
        db, table = t_db_table
        schema = None
    elif len(t_db_table) == 3:
        db, schema, table = t_db_table
    else:
        raise ValueError(f"Invalid database and table {db_table!r}")
    return {
        "database": db,
        "schema": schema,
        "table": table,
    }


class Location:
    """
    Syntax:
        完整URL形式：{protocol}://{user}:{password}@{host}:{port}/{database}.{table}
        简写形式：   {dbconf}:{database}.{table}
        本地文件：   file://{path}
        本地文件简写：file:{path}
    Example:
        mysql://dev:pass@172.16.24.93:3306/testdb.test
        tidb:testdb.test
        file:///tmp/result.csv
        file:/tmp/result.csv
    """

    ATTRS = ["protocol", "user", "password", "host", "port", "database", "schema", "table", "dbconf", "path"]

    def __init__(self, spec=None, **kwargs):
        if not kwargs:
            if not spec:
                raise ValueError("Location spec is required")
            if spec.startswith("file:"):
                self._from_file(spec)
            elif "://" in spec:
                self._from_url(spec)
            else:
                self._from_simple(spec)
        else:
            if spec is not None:
                kwargs["dbconf"] = spec
            self._from_dict(kwargs)

    def __str__(self):
        if self.protocol == "file":
            return self._format_file()
        if self.dbconf:
            return self._format_simple()
        else:
            return self._format_url()

    def _format_file(self):
        return f"{self.protocol}:{self.path}"

    def _format_url(self, hide_password=True):
        ret = [f"{self.protocol}://"]
        if self.user:
            ret.append(str(self.user))
            if self.password:
                password = "***" if hide_password else self.passsword
                ret.append(f":{password}")
            ret.append("@")
        if self.host:
            if ":" in self.host:
                ret.append(f"[{self.host}]")
            else:
                ret.append(str(self.host))
            if self.port:
                ret.append(f":{self.port}")
        if self.database:
            ret.append(f"/{self.database}")
            if self.schema:
                ret.append(f".{self.schema}")
            if self.table:
                ret.append(f".{self.table}")
        return "".join(ret)

    def _format_simple(self):
        ret = [f"{self.dbconf}:"]
        if self.database:
            ret.append(f"{self.database}")
            if self.schema:
                ret.append(f".{self.schema}")
            if self.table:
                ret.append(f".{self.table}")
        return "".join(ret)

    def __repr__(self):
        return f"<{type(self).__name__} {str(self)}>"

    def _from_file(self, url):
        """
        Syntax:
            file://{path}
            file:{path}
        """
        protocol, path = url.split(":", maxsplit=1)
        if path.startswith("//"):
            path = path[2:]
        params = {"protocol": protocol, "path": path}
        self._from_dict(params)

    def _from_url(self, url):
        """
        Syntax:
            {protocol}://{user}:{password}@{host}:{port}/{database}.{table}
        """
        parsed = urlparse(url)
        params = {
            "protocol": parsed.scheme,
            "user": parsed.username,
            "password": parsed.password,
            "host": parsed.hostname,
            "port": parsed.port,
        }
        params.update(_parse_db_table(parsed.path.strip("/")))
        self._from_dict(params)

    def _from_simple(self, spec):
        """
        Syntax:
            {dbconf}:{database}.{table}
        """
        dbconf, db_table = spec.strip().split(":")
        params = {"dbconf": dbconf}
        params.update(_parse_db_table(db_table))
        self._from_dict(params)

    def _from_dict(self, params):
        unknown_params = set(params) - set(self.ATTRS)
        if unknown_params:
            raise ValueError(f"Unknown params {unknown_params}")
        if not params.get("protocol") and not params.get("dbconf"):
            raise ValueError("protocol or dbconf is required")
        if params.get("protocol") == "file" and not params.get("path"):
            raise ValueError("path is required")
        for k in self.ATTRS:
            setattr(self, k, params.get(k))

    def to_dict(self):
        ret = {}
        for k in self.ATTRS:
            v = getattr(self, k, None)
            if v is not None and v != "":
                ret[k] = v
        return ret

    @property
    def is_local(self):
        return self.dbconf == "file" or self.protocol == "file"


def _get_dumper_cls(dtype):
    # XXX: so ugly here
    if dtype in ["cassandra"]:
        from recurvedata.pigeon.dumper.cass import CassandraDumper

        return CassandraDumper

    from recurvedata.pigeon.dumper.dbapi import DBAPIDumper

    return DBAPIDumper


def _get_connector(location):
    if location.protocol:
        # only support dbapi
        _conn_cls = get_connector_class(location.protocol)
        connector = _conn_cls(
            host=location.host,
            port=location.port,
            user=location.user,
            password=location.passsword,
            database=location.database,
        )
    else:
        connector = get_connector(location.dbconf, database=location.database)
    return connector


def _dump(src, handler_factory):
    connector = _get_connector(src)
    if src.schema:
        table = f"{src.schema}.{src.table}"
    else:
        table = src.table
    dumper = _get_dumper_cls(src.protocol or src.dbconf)(
        connector,
        table=table,
        handler_factories=[handler_factory],
    )
    logger.info("Dump start".center(40, "="))
    dumper.execute()


_loader_config = {
    "hive": {
        "cls": CSVToHiveLoader,
        "connector": "hive_connector",
    },
    "redshift": {
        "cls": CSVToRedshiftLoader,
        "connector": "redshift_connector",
    },
    "mysql": {
        "cls": CSVToMySQLLoader,
        "connector": "connector",
    },
}
_loader_config["tidb"] = _loader_config["mysql"]


def _load(dst, filename, mode, merge_keys=()):
    connector = _get_connector(dst)

    cfg = _loader_config[dst.protocol or dst.dbconf]
    cls, connector_name = cfg["cls"], cfg["connector"]
    kwargs = {
        "database": dst.database,
        "table": dst.table,
        "filename": filename,
        connector_name: connector,
    }
    if mode.upper() == LOAD_MERGE:
        logger.info(f"Primary keys: {merge_keys} in {dst}")
        kwargs.update({"mode": LOAD_MERGE, "primary_keys": ensure_list(merge_keys)})
    elif mode.upper() == LOAD_APPEND:
        kwargs.update({"mode": LOAD_APPEND})
    loader = cls(**kwargs)
    logger.info("Load start".center(40, "="))
    loader.execute()


def _get_stage_filename(src, dst):
    if src.is_local:
        return src.path
    if dst.is_local:
        if not os.path.isabs(dst.path):
            return os.path.abspath(dst.path)
        return dst.path
    tmpdir = f"{src.protocol or src.dbconf}_to_{dst.protocol or dst.dbconf}"
    new_stagefile = fs.new_stagefile_factory(tmpdir)
    return new_stagefile(slugify(f"{src}_to_{dst}") + ".txt")


def sync(src, dst, mode, merge_keys=()):
    """同步一个表"""
    if not isinstance(src, Location):
        src = Location(src)
    if not isinstance(dst, Location):
        dst = Location(dst)

    if dst.protocol and dst.protocol != "file":
        raise NotImplementedError("暂不支持URL形式的目标")

    filename = _get_stage_filename(src, dst)
    logger.info(f"Dump to file: {filename}")

    if not src.is_local:
        for_hive = (dst.protocol or dst.dbconf) in ["impala", "hive"]
        handler_factory = create_csv_file_handler_factory(filename=filename, hive=for_hive)
        _dump(src, handler_factory)
    if not dst.is_local:
        _load(dst, filename, mode=mode, merge_keys=merge_keys)

import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property, wraps
from io import StringIO
from typing import TYPE_CHECKING, Any, Optional

import sqlalchemy
import sqlalchemy.sql.schema
import sqlglot
from sqlalchemy import create_engine, insert, inspect
from sqlalchemy import text as sqlalchemy_text
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.engine.url import URL
from sqlalchemy.schema import CreateTable, MetaData
from sqlalchemy.sql.compiler import DDLCompiler
from sqlglot import exp

from recurvedata.connectors.base import RecurveConnectorBase
from recurvedata.connectors.const import ENV_VAR_DBT_PASSWORD, ENV_VAR_DBT_USER, set_env_dbt_password, set_env_dbt_user
from recurvedata.consts import ConnectionCategory
from recurvedata.utils.imports import MockModule

if TYPE_CHECKING:
    from recurvedata.executors.schemas import ColumnItem

# Lazy imports for non-simple dependencies
try:
    import pandas as pd
    import sqlparse
    import sshtunnel
    from paramiko import RSAKey
except ImportError:
    pd = MockModule("pandas")
    sqlparse = MockModule("sqlparse")
    sshtunnel = MockModule("sshtunnel")
    RSAKey = MockModule("paramiko.RSAKey")

if sqlalchemy.__version__ >= "2":
    text = sqlalchemy_text
else:

    def text(v):
        return v


class DBAPIABC(ABC):
    @property
    @abstractmethod
    def sqlalchemy_url(self) -> URL:
        ...

    @property
    @abstractmethod
    def test_query(self) -> str:
        ...

    @abstractmethod
    def test_connection(self):
        ...

    @property
    @abstractmethod
    def connect_args(self) -> Optional[dict]:
        ...

    @abstractmethod
    def connect(self):
        ...

    @abstractmethod
    def execute(self, query: str):
        ...

    @property  # todo: cache
    @abstractmethod
    def inspector(self) -> Inspector:
        ...

    @abstractmethod
    def has_table(self, table, database=None):
        ...

    @abstractmethod
    def get_columns(self, table: str, database=None):
        ...

    @abstractmethod
    def _reflect_table(self, table: str, database=None, engine=None) -> sqlalchemy.sql.schema.Table:
        ...

    @abstractmethod
    def generate_ddl(self, table: str, database=None):
        ...

    @abstractmethod
    def fetchall(self, query: str):
        ...

    @abstractmethod
    def fetchmany(self, query: str, size=None):
        ...

    @abstractmethod
    def fetchone(self, query: str):
        ...

    @abstractmethod
    def get_pandas_df(self, query: str, parameters=None, **kwargs):
        ...

    # def commit(self):
    #     raise NotImplementedError

    @abstractmethod
    def insert(self, table: str, data: list[dict], database: str = None):
        ...


def with_ssh_tunnel(func):
    """
    a decorator that wrap func with a ssh tunnel
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        tunnel = self.ssh_tunnel
        if not tunnel:
            return func(self, *args, **kwargs)
        try:
            with tunnel:
                return func(self, *args, **kwargs)
        finally:
            tunnel.stop()

    return wrapper


class DBAPIBase(RecurveConnectorBase):
    SYSTEM_DATABASES = []
    setup_extras_require = ["sqlalchemy", "sshtunnel", "paramiko"]
    driver = ""
    config_schema = {}
    category = [
        ConnectionCategory.DATABASE,
    ]
    column_type_mapping = {}
    # Common data types supported by all connectors
    # each connector can add its own types
    available_column_types = [
        "smallint",
        "int",
        "bigint",
        "float",
        "double",
        "decimal",
        "date",
        "timestamp",
        "char",
        "varchar",
        "json",
    ]

    def __init__(self, conf, *args, **kwargs):
        if conf.get("password") == "":
            conf["password"] = None
        super().__init__(conf, *args, **kwargs)

    @property
    def sqlalchemy_url(self):
        host, port = self.host, self.port
        if self.ssh_tunnel and self.ssh_tunnel.is_active:
            host, port = self.ssh_tunnel.local_bind_host, self.ssh_tunnel.local_bind_port

        if sqlalchemy.__version__ >= "2":
            return URL(self.driver, self.user, self.password, host, port, self.database, query={})
        return URL(self.driver, self.user, self.password, host, port, self.database)

    @property
    def test_query(self):
        return "select 1"

    @cached_property
    @with_ssh_tunnel
    def type_code_mapping(self) -> dict:
        """
        type_code from sqlalchemy's cursor.description -> database's dialect data type name
        """
        raise NotImplementedError

    def sqlalchemy_column_type_code_to_name(self, type_code: Any, size: int | None = None) -> str:
        """
        since cursor.description return type code only, we need to map it to dialect data type name

        :param type_code: an object returned by cursor.description
        :return: a string of column type name, in lower case
        """
        raise NotImplementedError

    def test_connection(self):
        self.execute(self.test_query)

    @property
    def connect_args(self):
        return {}

    def connect(self):
        engine = create_engine(
            self.sqlalchemy_url,
            max_overflow=0,  # todo: add to const
            pool_recycle=10 * 60,  # todo: add to const
            connect_args=self.connect_args,
            echo=False,
        )
        return engine  # todo: thread safe? use session to wrap?

    @with_ssh_tunnel
    def execute(self, query: str):
        if isinstance(query, list):
            queries = list(itertools.chain(*map(sqlparse.split, query)))
        else:
            queries = sqlparse.split(query)

        engine = self.connect()
        with engine.connect() as con:
            for q in queries:
                con.execute(text(q))

    @property
    def inspector(self) -> Inspector:
        engine = self.connect()
        inspector: Inspector = inspect(engine)
        return inspector

    @with_ssh_tunnel
    def has_table(self, table, database=None):
        database = database or self.database
        return self.inspector.has_table(table, schema=database)

    def _extract_column_name(self, column_type):
        return column_type.__visit_name__

    @with_ssh_tunnel
    def get_columns(self, table: str, database: str = None) -> list[str]:
        database = database or self.database
        column_dcts = self.inspector.get_columns(table, schema=database)
        for dct in column_dcts:
            dct["type"] = self._extract_column_name(dct["type"]).lower()
        return column_dcts

    @staticmethod
    def format_key(key):
        key = key.strip("`")
        return f"`{key}`"

    def _reflect_table(self, table, database=None, engine=None) -> sqlalchemy.sql.schema.Table:
        if not engine:
            engine = self.connect()
        meta = MetaData()
        meta.reflect(
            bind=engine,
            schema=database,
            only=[
                table,
            ],
        )
        table = meta.sorted_tables[0]
        return table

    @with_ssh_tunnel
    def generate_ddl(self, table, database=None):
        engine = self.connect()
        table = self._reflect_table(table, database=database, engine=engine)
        ddl: DDLCompiler = CreateTable(table).compile(engine)
        return ddl.string

    @with_ssh_tunnel
    def fetchall(self, query):
        engine = self.connect()
        connection = engine.raw_connection()
        with connection.cursor() as cursor:
            cursor.execute(query)
            res = cursor.fetchall()
        connection.close()
        return res

    @with_ssh_tunnel
    def fetchmany(self, query, size=None):
        engine = self.connect()
        connection = engine.raw_connection()
        with connection.cursor() as cursor:
            cursor.execute(query)
            res = cursor.fetchmany(size=size)
        connection.close()
        return res

    @with_ssh_tunnel
    def fetchone(self, query):
        engine = self.connect()
        connection = engine.raw_connection()
        with connection.cursor() as cursor:
            cursor.execute(query)
            res = cursor.fetchone()
        connection.close()
        return res

    @with_ssh_tunnel
    def get_pandas_df(self, query, parameters=None, **kwargs):
        engine = self.connect()
        try:
            df = pd.read_sql_query(sql=query, con=engine, params=parameters, **kwargs)
        finally:
            engine.dispose()
        return df

    # def commit(self):
    #     raise NotImplementedError

    @with_ssh_tunnel
    def insert(self, table: str, data: list[dict], database: str = None):
        engine = self.connect()
        table = self._reflect_table(table, database=database, engine=engine)
        with engine.connect() as conn:
            conn.execute(insert(table), data)
        engine.dispose()

    @with_ssh_tunnel
    def get_databases(self):
        return [d for d in self.inspector.get_schema_names() if d.lower() not in self.SYSTEM_DATABASES]

    @with_ssh_tunnel
    def get_tables(self, database: str = None):
        database = database or self.database
        return self.inspector.get_table_names(database)

    @with_ssh_tunnel
    def get_views(self, database: str = None):
        database = database or self.database
        return self.inspector.get_view_names(database)

    def _init_ssh_tunnel(self):
        """
        init a ssh tunnel based on self.ssh_tunnel_config
        """

        def _init_private_key(config: SSHTunnelConfig):
            if config.private_key_str:
                pk_str = config.private_key_str.replace("\\n", "\n")
                return RSAKey.from_private_key(StringIO(pk_str), password=config.private_key_passphrase)

        tunnel_config = self.ssh_tunnel_config
        if not tunnel_config:
            return

        tunnel = sshtunnel.SSHTunnelForwarder(
            ssh_address_or_host=(tunnel_config.host, tunnel_config.port),
            ssh_username=tunnel_config.user,
            ssh_password=tunnel_config.password,
            ssh_pkey=_init_private_key(tunnel_config),
            remote_bind_address=(self.host, self.port),
        )

        return tunnel

    @property
    def ssh_tunnel(self):
        tunnel_config = self.ssh_tunnel_config
        if not tunnel_config:
            return
        if not hasattr(self, "_ssh_tunnel"):
            self._ssh_tunnel = self._init_ssh_tunnel()
        return self._ssh_tunnel

    @property
    def ssh_tunnel_config(self) -> Optional["SSHTunnelConfig"]:
        ssh_config = self.conf.get("ssh_tunnel", {})
        if not (ssh_config and ssh_config.get("host")):
            return
        return SSHTunnelConfig(**ssh_config)

    @classmethod
    def get_sql_operator_types(cls):
        return [
            cls.connection_type,
        ]

    def convert_config_to_dbt_profile(self, database: str, schema: str = None) -> dict:
        return {
            "server": self.host,
            "port": self.port,
            "user": ENV_VAR_DBT_USER,
            "password": ENV_VAR_DBT_PASSWORD,
            "schema": database or self.database,
            "type": self.connection_type,
            "threads": 10,
        }

    def set_env_when_get_dbt_connection(self):
        set_env_dbt_user(self.user or "")
        set_env_dbt_password(self.password or "")

    @classmethod
    def get_dialect(cls):
        # dialect impala -> hive, cuz there is no dialect 'impala' in sqlglot
        return "hive" if cls.connection_type == "impala" else (cls.connection_type or None)

    @classmethod
    def clean_sql(cls, sql):
        dialect = cls.get_dialect()
        # Parse the SQL query
        parsed = sqlglot.parse_one(sql, read=dialect)
        # since some sql dialects have special identifier, we need to use the dialect to generate the clean sql
        return parsed.sql(dialect=dialect, comments=False)

    @classmethod
    def order_sql(cls, sql: str, orders: list[dict[str, str]] = None, return_sql: bool = True):
        """
        order the sql by the orders
        """
        dialect = cls.get_dialect()
        # Wrap the entire query with a subquery
        alias = "_recurve_limit_subquery"
        subquery = exp.Subquery(this=cls.clean_sql(sql), alias=alias)

        # Create a new SELECT statement with the subquery and the LIMIT clause
        outer_select = exp.select("*").from_(subquery)
        if orders:
            order_clauses = []
            for order in orders:
                if cls.connection_type in ["postgres", "redshift"]:
                    field_expr = f'{alias}."{order["field"]}"'
                else:
                    field_expr = exp.Column(this=order["field"], table=alias)
                    field_expr = field_expr.sql(dialect=dialect)

                order_clauses.append(f'{field_expr} {order["order"]}')

            order_stmt = ", ".join(order_clauses)
            outer_select = outer_select.order_by(order_stmt)

        return outer_select.sql(dialect=dialect) if return_sql else outer_select

    @classmethod
    def limit_sql(cls, sql: str, limit: int = 100, orders: list[dict[str, str]] = None, offset: int = 0) -> str:
        """
        used for preview, parse sql and wrap sql with limit.
        no validation on sql.
        If the sql is DML, then execute it will raise an error.
        """
        dialect = cls.get_dialect()

        outer_select = cls.order_sql(sql, orders, return_sql=False)

        if offset:
            outer_select = outer_select.offset(offset)

        outer_select = outer_select.limit(limit)

        result = outer_select.sql(dialect=dialect)

        return result

    @classmethod
    def count_sql(cls, sql: str) -> str:
        """
        used for preview, parse sql and wrap sql with count.
        no validation on sql.
        If the sql is DML, then execute it will raise an error.
        """
        return f"SELECT COUNT(1) FROM ({cls.clean_sql(sql)}) AS cnt_subquery"

    @classmethod
    def create_table_sql(
        cls,
        table: str,
        columns: list["ColumnItem"],
        keys: list[str] = None,
        database: str = None,
        schema: str = None,
        if_not_exists: bool = True,
        **kwargs,
    ) -> str:
        """
        Generate CREATE TABLE DDL
        """
        if schema:  # postgres
            table = f"{schema}.{table}"
        elif database:  # mysql
            table = f"{database}.{table}"

        _columns = []
        for column in columns:
            ctype = cls.convert_normalized_type_to_db_type(column.normalized_type)
            _columns.append(f"{column.name} {ctype}")

        if keys:
            _columns.append(f"PRIMARY KEY ({', '.join(keys)})")

        sql = "CREATE TABLE"
        if if_not_exists:
            sql += " IF NOT EXISTS"
        sql += f" {table} ({', '.join(_columns)})"

        from loguru import logger

        logger.info(f"create_table_sql: {sql}")
        return sql

    @classmethod
    def convert_normalized_type_to_db_type(cls, normalized_type: str) -> str:
        """
        Convert normalized type to current database data type name.
        """
        return normalized_type


@dataclass
class SSHTunnelConfig:
    host: str
    port: int
    user: str
    password: str = None
    private_key_str: str = None  # 私钥字符串，非文件名
    private_key_passphrase: str = None  # 私钥的 passphrase

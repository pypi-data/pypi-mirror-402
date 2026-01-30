from functools import cached_property

try:
    import re

    from pyhive.sqlalchemy_hive import HiveDialect, exc
    from sqlalchemy import text

    def _get_table_columns(self, connection, table_name, schema):
        full_table = table_name
        if schema:
            full_table = schema + "." + table_name
        # TODO using TGetColumnsReq hangs after sending TFetchResultsReq.
        # Using DESCRIBE works but is uglier.
        try:
            # This needs the table name to be unescaped (no backticks).
            rows = connection.execute(text("DESCRIBE {}".format(full_table))).fetchall()
        except exc.OperationalError as e:
            # Does the table exist?
            regex_fmt = r"TExecuteStatementResp.*SemanticException.*Table not found {}"
            regex = regex_fmt.format(re.escape(full_table))
            if re.search(regex, e.args[0]):
                raise exc.NoSuchTableError(full_table)
            else:
                raise
        else:
            # Hive is stupid: this is what I get from DESCRIBE some_schema.does_not_exist
            regex = r"Table .* does not exist"
            if len(rows) == 1:
                # recurvedata changed
                if "name" not in rows[0].keys():  # hive
                    if re.match(regex, rows[0].col_name):
                        raise exc.NoSuchTableError(full_table)
                else:
                    if re.match(regex, rows[0].name):  # impala
                        raise exc.NoSuchTableError(full_table)
                # recurvedata changed finish pyhive==0.6.5
            return rows

    HiveDialect._get_table_columns = _get_table_columns
except ImportError:
    pass

from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.const import ENV_VAR_DBT_PASSWORD, ENV_VAR_DBT_USER
from recurvedata.connectors.dbapi import DBAPIBase, with_ssh_tunnel
from recurvedata.consts import ConnectionCategory, ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "impala"
UI_CONNECTION_TYPE = "Apache Impala"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class ImpalaConnector(DBAPIBase):
    SYSTEM_DATABASES = [
        "information_schema",
        "_impala_builtins",
    ]
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    setup_extras_require = ["PyHive", "thrift-sasl"]
    driver = "hive"  # todo: 先用 hive 的
    category = [ConnectionCategory.WAREHOUSE]
    group = [ConnectorGroup.DESTINATION]

    config_schema = {
        "type": "object",
        "properties": {
            "host": {
                "type": "string",
                "title": _l("Host Address"),
                "default": "127.0.0.1",
            },
            "port": {
                "type": "number",
                "title": _l("Port Number"),
                "default": 21050,
            },
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
            "database": {
                "type": "string",
                "title": _l("Database"),
                "description": _l("The name of the database to connect to"),
                "default": "default",
            },
            "hdfs_options": {
                "type": "object",
                "title": _l("HDFS Configuration"),
                "description": _l("Configuration options for HDFS connection"),
                "properties": {
                    "host": {
                        "type": "string",
                        "title": _l("Host"),
                        "description": _l("HDFS namenode hostname or IP address"),
                    },
                    "port": {
                        "type": "number",
                        "title": _l("Port Number"),
                        "description": _l("HDFS namenode port number"),
                        "default": 50070,
                    },
                    "user": {"type": "string", "title": _l("Username")},
                },
                "order": ["host", "port", "user"],
            },
            "auth_mechanism": {
                "type": "string",
                "title": _l("Authentication Mechanism"),
                "description": _l("Impala authentication mechanism (e.g. PLAIN, GSSAPI, LDAP)"),
                "default": "PLAIN",
            },
            "auth": {
                "type": "string",
                "title": _l("Authentication Type"),
                "default": "LDAP",
            },
            "use_http_transport": {
                "type": "boolean",
                "title": _l("Use HTTP Transport"),
                "default": True,
            },
            "use_ssl": {
                "type": "boolean",
                "title": _l("Use SSL"),
                "default": True,
            },
            "http_path": {
                "type": "string",
                "title": _l("HTTP Path"),
                "default": "",
            },
        },
        "order": [
            "host",
            "port",
            "user",
            "password",
            "database",
            "hdfs_options",
            "auth",
            "auth_mechanism",
            "use_http_transport",
            "use_ssl",
            "http_path",
        ],
        "required": ["host", "port"],
        "secret": ["password"],
    }

    @property
    def connect_args(self):
        if not self.password and not self.user:
            return {"auth": "NOSASL"}
        if self.password:
            return {"auth": "LDAP"}  # 先粗暴处理
        if self.auth == "LDAP":
            return {"auth": "LDAP"}  # todo
        return {}

    # generate_ddl todo: stored as parquet

    def _extract_column_name(self, column_type):
        visit_type = column_type.__visit_name__
        if visit_type == "type_decorator":
            return column_type.impl.__visit_name__
        return visit_type

    @with_ssh_tunnel
    def get_tables(self, database: str = None):
        database = database or self.database
        result = self.fetchall(f"SHOW TABLES IN {database}")
        return [r[0] for r in result]

    @with_ssh_tunnel
    def get_views(self, database: str = None):
        database = database or self.database
        result = self.fetchall(f"SHOW VIEWS IN {database}")
        return [r[0] for r in result]

    def get_columns(self, table, database=None):
        database = database or self.database
        column_dcts = self.inspector.get_columns(self.format_key(table), schema=self.format_key(database))
        for dct in column_dcts:
            dct["type"] = self._extract_column_name(dct["type"]).lower()
        return column_dcts

    def convert_config_to_dbt_profile(self, database: str, schema: str = None) -> dict:
        return {
            "type": "impala",
            "host": self.host,
            "http_path": self.http_path,
            "port": self.port,
            "auth_type": self.auth.lower(),
            "use_http_transport": self.use_http_transport,
            "use_ssl": self.use_ssl,
            "username": ENV_VAR_DBT_USER,
            "password": ENV_VAR_DBT_PASSWORD,
            "schema": database or self.database,
            "threads": 10,
        }

    @cached_property
    @with_ssh_tunnel
    def type_code_mapping(self) -> dict:
        return {}

    def sqlalchemy_column_type_code_to_name(self, code: str, size: int | None = None) -> str:
        return code.lower()

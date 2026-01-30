from recurvedata.connectors._register import register_connector_class
from recurvedata.connectors.dbapi import DBAPIBase, with_ssh_tunnel
from recurvedata.consts import ConnectorGroup
from recurvedata.core.translation import _l

CONNECTION_TYPE = "tidb"
UI_CONNECTION_TYPE = "TiDB"


@register_connector_class([CONNECTION_TYPE, UI_CONNECTION_TYPE])
class TidbConnector(DBAPIBase):
    SYSTEM_DATABASES = ["information_schema", "mysql", "performance_schema", "sys"]
    connection_type = CONNECTION_TYPE
    ui_connection_type = UI_CONNECTION_TYPE
    group = [ConnectorGroup.DESTINATION]
    setup_extras_require = ["mysql-connector-python"]
    # pip install git+https://github.com/pingcap/sqlalchemy-tidb.git@main
    # manually run setup.py and upload to Recurvedata pypi

    driver = "mysql+mysqlconnector"
    config_schema = {
        "type": "object",
        "properties": {
            "host": {"type": "string", "title": _l("Host Address"), "default": "127.0.0.1"},
            "port": {
                "type": "number",
                "title": _l("Port Number"),
                "default": 4000,
            },
            "user": {"type": "string", "title": _l("Username")},
            "password": {"type": "string", "title": _l("Password")},
            "database": {
                "type": "string",
                "title": _l("Database Name"),
                "description": _l("The name of the database to connect to"),
            },
        },
        "order": ["host", "port", "user", "password", "database"],
        "required": ["host"],
        "secret": ["password"],
    }

    @with_ssh_tunnel
    def get_columns(self, table, database=None):
        database = database or self.database
        column_dcts = self.inspector.get_columns(table, schema=database)
        for dct in column_dcts:
            dct["type"] = self._extract_column_name(dct["type"]).lower()
        return column_dcts

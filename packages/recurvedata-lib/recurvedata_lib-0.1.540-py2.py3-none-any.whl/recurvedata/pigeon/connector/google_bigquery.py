import copy
import os
from urllib import parse

import cytoolz as toolz
from google import auth
from google.cloud.bigquery import Client, LoadJobConfig, SourceFormat, dbapi, enums, job
from google.cloud.bigquery.dataset import DatasetReference
from google.cloud.bigquery.table import TableReference
from google.cloud.exceptions import BadRequest, NotFound
from google.oauth2 import service_account
from requests import Session

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.connector.dbapi import ClosingCursor, DBAPIConnector, NullCursor
from recurvedata.pigeon.schema import types

_bigquery_type_to_canonical_type = {
    enums.SqlTypeNames.STRING: types.STRING,
    enums.SqlTypeNames.INT64: types.INT64,
    enums.SqlTypeNames.INTEGER: types.INT64,
    enums.SqlTypeNames.FLOAT: types.FLOAT64,
    enums.SqlTypeNames.FLOAT64: types.FLOAT64,
    enums.SqlTypeNames.NUMERIC: types.FLOAT64,
    enums.SqlTypeNames.BOOLEAN: types.BOOLEAN,
    enums.SqlTypeNames.BOOL: types.BOOLEAN,
    enums.SqlTypeNames.TIMESTAMP: types.DATETIME,
    enums.SqlTypeNames.DATETIME: types.DATETIME,
    enums.SqlTypeNames.DATE: types.DATE,
}

GOOGLE_DRIVE_API = (
    "https://www.googleapis.com/auth/drive"  # external table linked with google sheet, need google drive api enabled
)


class IterCursor(ClosingCursor):
    def __init__(self, connection, commit_on_close=True, pagesize=None):
        super().__init__(connection, commit_on_close)
        self._cursor.arraysize = pagesize

    def __iter__(self):
        self._cursor._try_fetch()
        return self._cursor._query_data


@register_connector_class(["google_bigquery", "gbq"])
class GoogleBigqueryConnector(DBAPIConnector):
    _sqla_driver = "bigquery"

    if GOOGLE_DRIVE_API in Client.SCOPE:
        _scopes = Client.SCOPE
    else:
        _scopes = Client.SCOPE + (GOOGLE_DRIVE_API,)

    def __init__(
        self,
        key_path: str = None,
        key_dict: dict = None,
        project: str = None,
        http: Session = None,
        proxies: dict = None,
        location: str = None,
        dataset: str = None,
        pagesize: int = None,
        *args,
        **kwargs,
    ):
        """
        instance of gbq
        :param project: project_id
        :param key_path: path to json key file
        :param key_dict: dict of key
        :param http: requests session
        :param proxies: proxy
        :param location: location
        :param dataset: dataset_id
        """
        super().__init__(host=None, database=dataset, *args, **kwargs)
        self._project_id = project
        self._key_path = key_path
        self._key_dict = key_dict
        self._http = http
        self._proxies = proxies
        self._location = location
        self.dataset = dataset
        self.pagesize = pagesize

    def is_google_bigquery(self):
        return True

    def get_credentials(self):
        if not any([self._key_path, self._key_dict]):
            credentials, project_id = auth.default(scopes=self._scopes, request=self._http)
            self._project_id = self._project_id or project_id
        elif self._key_path:
            credentials = service_account.Credentials.from_service_account_file(
                filename=self._key_path, scopes=self._scopes
            )
        else:
            _key_dict = copy.deepcopy(self._key_dict)
            # Fix private key format with robust conversion
            _key_dict["private_key"] = self._convert_private_key(_key_dict["private_key"])
            credentials = service_account.Credentials.from_service_account_info(info=_key_dict, scopes=self._scopes)
        self._project_id = self._project_id or credentials.project_id

        return credentials

    @staticmethod
    def _convert_private_key(private_key: str) -> str:
        """
        Convert private key from various escape formats to proper PEM format.
        Handles multiple levels of escaping that can occur during transmission/storage.
        """
        if not private_key:
            return private_key
            
        # Remove any leading/trailing whitespace
        private_key = private_key.strip()
        
        # Handle various escape sequence patterns
        # Multiple replacement passes to handle nested escaping
        
        # Replace quadruple-escaped newlines (\\\\n -> \\n)
        private_key = private_key.replace("\\\\n", "\\n")
        
        # Replace double-escaped newlines (\\n -> \n) 
        private_key = private_key.replace("\\n", "\n")
        
        # Handle edge case where literal \n strings need to become actual newlines
        # This covers cases where the key was stored as a literal string
        if "-----BEGIN PRIVATE KEY-----" in private_key and "\n" not in private_key:
            # If we have the BEGIN marker but no actual newlines, it's likely escaped
            private_key = private_key.replace("-----BEGIN PRIVATE KEY-----", "-----BEGIN PRIVATE KEY-----\n")
            private_key = private_key.replace("-----END PRIVATE KEY-----", "\n-----END PRIVATE KEY-----")
            
            # Split the key content and add newlines every 64 characters (standard PEM format)
            lines = private_key.split('\n')
            if len(lines) >= 2:
                # Extract the key content between BEGIN and END
                begin_line = lines[0]
                end_line = lines[-1] 
                key_content = ''.join(lines[1:-1])
                
                # Split key content into 64-character lines
                formatted_lines = [begin_line]
                for i in range(0, len(key_content), 64):
                    formatted_lines.append(key_content[i:i+64])
                formatted_lines.append(end_line)
                
                private_key = '\n'.join(formatted_lines)
        
        return private_key

    @toolz.memoize
    def connect_impl(self, *args, **kwargs):
        return dbapi.connect(client=self.client())

    def client(self):
        if self._proxies:
            for scheme in ["http", "https"]:
                os.environ[f"{scheme}_proxy"] = self._proxies[scheme]

        client = Client(
            project=self._project_id, credentials=self.get_credentials(), location=self._location, _http=self._http
        )
        return client

    def cursor(self, autocommit=False, dryrun=False, commit_on_close=True, **kwargs):
        if dryrun:
            return NullCursor()
        conn = self.connect(autocommit, **kwargs)
        return IterCursor(conn, commit_on_close=commit_on_close, pagesize=self.pagesize)

    def _get_sqlalchemy_uri(self):
        params = {"location": self._location}
        if self._key_path:
            params.update({"credentials_path": self._key_path})
        uri = f"{self._sqla_driver}://{self._project_id}"
        if self.dataset:
            uri = os.path.join(uri, self.dataset)
        return f"{uri}?{parse.urlencode(params)}"

    def get_pandas_df(self, query, parameters=None, **kwargs):
        """Get pandas dataframe
        Note: pd.read_gbq 无法正常工作，改用 client to_dataframe()
        """
        format_operation = dbapi.cursor._format_operation(query, parameters=parameters)
        query_parameters = dbapi._helpers.to_query_parameters(parameters)
        config = job.QueryJobConfig(use_legacy_sql=False)
        config.query_parameters = query_parameters
        result = self.client().query(format_operation, job_config=config).result()
        return result.to_dataframe()

    def table_ref(self, table, dataset):
        return TableReference(DatasetReference(self._project_id, dataset), table)

    def has_table(self, table, dataset=None, **kwargs):
        if dataset is None:
            dataset = self.dataset
        try:
            self.client().get_table(self.table_ref(table, dataset))
            return True
        except NotFound:
            return False

    def list_partitions(self, table, dataset):
        """查询 partition keys"""
        try:
            return self.client().list_partitions(self.table_ref(table, dataset))
        except BadRequest:
            return []

    @staticmethod
    def to_canonical_type(type_code, size):
        return _bigquery_type_to_canonical_type.get(type_code, types.STRING)

    @staticmethod
    def from_canonical_type(canonical_type, size):
        _canonical_type_to_bigquery_type = {v: k for k, v in _bigquery_type_to_canonical_type.items()}
        return _canonical_type_to_bigquery_type.get(canonical_type, "STRING")

    def generate_ddl(self, table, dataset=None, if_exists=True):
        cols = [f"{col.name} {col.field_type}" for col in self.get_schema(table, dataset)]
        if_exists_stmt = " IF NOT EXISTS " if if_exists else " "
        full_table_name = f"{self.quote_identifier(dataset)}.{self.quote_identifier(table)}"
        return f'CREATE TABLE{if_exists_stmt}{full_table_name} ({", ".join(cols)})'

    def get_columns(self, table, dataset=None, exclude=()):
        cols = []
        for col in self.get_schema(table, dataset):
            if col.name in exclude:
                continue
            cols.append(col.name)
        return cols

    def get_schema(self, table, dataset):
        if dataset is None:
            dataset = self.dataset
        if not self.has_table(table, dataset):
            raise ValueError(f"Table {table} not exists in {dataset!r}")
        table = self.client().get_table(self.table_ref(table, dataset))
        return table.schema

    def load_csv(
        self,
        table,
        filename=None,
        gcs_uri=None,
        delimiter=",",
        quotechar='"',
        skiprows=0,
        write_disposition="WRITE_APPEND",
        schema=None,
        **kwargs,
    ):
        dataset, table = table.split(".")
        job_config = LoadJobConfig(
            source_format=SourceFormat.CSV,
            skip_leading_rows=skiprows,
            # autodetect=True,
            field_delimiter=delimiter,
            quote_character=quotechar,
            write_disposition=write_disposition,
            schema=schema,
            **kwargs,
        )

        if filename:
            with open(filename, "rb") as file:
                load_job = self.client().load_table_from_file(
                    file_obj=file, destination=self.table_ref(table, dataset), job_config=job_config
                )
        elif gcs_uri:
            load_job = self.client().load_table_from_uri(
                source_uris=gcs_uri, destination=self.table_ref(table, dataset), job_config=job_config
            )
        else:
            self.logger.error("no file or gcs uri is provided")

        self.logger.info("start loading csv to bigquery")
        load_job.result()
        self.logger.info("finish loading csv to bigquery")

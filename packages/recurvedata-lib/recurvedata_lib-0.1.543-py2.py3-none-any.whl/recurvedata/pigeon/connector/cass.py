import retrying
from cassandra import ReadTimeout, cqltypes
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, default_lbp_factory
from cassandra.encoder import Encoder
from cassandra.policies import ConstantReconnectionPolicy, RetryPolicy
from cassandra.query import bind_params

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.schema import Schema, types
from recurvedata.pigeon.utils import LoggingMixin


class NullSession(LoggingMixin):
    """
    NullCursor implements some methods of Cassandra Session, but does nothing at all.
    """

    def execute(self, query, parameters=None, *args, **kwargs):
        query_string = bind_params(query, parameters, Encoder())
        self.logger.info(query_string)
        return None

    def shutdown(self):
        self.logger.info("shutting down null session")
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


class ClosingSession(object):
    def __init__(self, session):
        self._session = session
        self._cluster = session.cluster

    def __getattr__(self, name):
        return getattr(self._session, name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def close(self):
        self.shutdown()

    def shutdown(self):
        self._session.shutdown()
        self._cluster.shutdown()


@register_connector_class("cassandra")
class CassandraConnector(object):
    _cqltype_to_canonical_type = {
        cqltypes.BooleanType: types.BOOLEAN,
        cqltypes.ByteType: types.INT8,
        cqltypes.ShortType: types.INT16,
        cqltypes.Int32Type: types.INT32,
        cqltypes.IntegerType: types.INT64,
        cqltypes.LongType: types.INT64,
        cqltypes.TimeType: types.INT64,
        cqltypes.FloatType: types.FLOAT32,
        cqltypes.DoubleType: types.FLOAT64,
        cqltypes.Decimal: types.FLOAT64,
        cqltypes.SimpleDateType: types.DATE,
        cqltypes.DateType: types.DATETIME,
        cqltypes.TimestampType: types.DATETIME,
        cqltypes.VarcharType: types.STRING,
        cqltypes.UUIDType: types.STRING,
        cqltypes.UTF8Type: types.STRING,
    }

    _canonical_type_to_cqltype = {
        types.BOOLEAN: cqltypes.BooleanType.typename,
        types.INT8: cqltypes.ByteType.typename,
        types.INT16: cqltypes.ShortType.typename,
        types.INT32: cqltypes.Int32Type.typename,
        types.INT64: cqltypes.LongType.typename,
        types.FLOAT32: cqltypes.FloatType.typename,
        types.FLOAT64: cqltypes.DoubleType.typename,
        types.DATE: cqltypes.SimpleDateType.typename,
        types.DATETIME: cqltypes.TimestampType.typename,
        types.STRING: cqltypes.UTF8Type.typename,
        types.JSON: cqltypes.UTF8Type.typename,
    }

    def __init__(self, host, port, database=None, user=None, password=None, *args, **kwargs):
        self.host = host
        self.port = int(port)
        self.database = database
        self.user = user
        self.password = password
        self.args = args
        self.kwargs = kwargs

    def connect(self, *args, **kwargs):
        auth = PlainTextAuthProvider(username=self.user, password=self.password)
        cluster = Cluster(
            contact_points=self.host,
            auth_provider=auth,
            protocol_version=3,
            load_balancing_policy=default_lbp_factory(),
            default_retry_policy=RetryPolicy(),
            reconnection_policy=ConstantReconnectionPolicy(delay=1, max_attempts=10),
            *args,
            **kwargs,
        )
        return cluster

    def session(self, *args, **kwargs):
        cluster = self.connect(*args, **kwargs)
        return cluster.connect(self.database)

    def closing_session(self, dryrun=False, *args, **kwargs):
        if dryrun:
            session = NullSession()
        else:
            real_session = self.session(*args, **kwargs)
            session = ClosingSession(real_session)
        return session

    def execute(self, query, parameters=None, timeout=20, retry=3):
        with self.closing_session() as session:
            retry_handler = retrying.Retrying(retry_on_exception=_retry_if_timeout, stop_max_attempt_number=retry)
            return retry_handler.call(_execute_query, session, query, parameters, timeout)

    def get_data_schema(self, result_set):
        schema = Schema()
        for name, ctype in zip(result_set.column_names, result_set.column_types):
            ttype = self.to_canonical_type(ctype)
            schema.add_field_by_attrs(name, ttype)
        return schema

    def to_canonical_type(self, ctype):
        return self._cqltype_to_canonical_type.get(ctype, types.STRING)

    def from_canonical_type(self, canonical_type, size):
        return self._canonical_type_to_cqltype.get(canonical_type, cqltypes.UTF8Type.typename)


def _retry_if_timeout(exc):
    return isinstance(exc, ReadTimeout)


def _execute_query(session, query, parameters, timeout, *args, **kwargs):
    return session.execute(query, parameters, timeout=timeout, *args, **kwargs)

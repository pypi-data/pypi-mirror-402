import datetime
import logging
import re
from collections import namedtuple
from typing import Union

try:
    import sqlparse
    from sql_metadata.keywords_lists import QueryType, TokenType
    from sql_metadata.parser import Parser
    from sql_metadata.utils import UniqueList
except ImportError:
    Parser = object
logger = logging.getLogger(__name__)
Table = namedtuple("Table", ["data_source", "database", "table"])
VERSION = 1


class LineageParser(Parser):
    """
    2.5.1 sql-metadata 发现的问题，都已处理：
        1. 需要屏蔽 _preprocess_query，否则 hive / impala 里很多 " 被替换成 `，容易造成后续解析错误
        2. 有挺多不支持的 sql，都列在 NOT_SUPPORT_PREFIXES 里
        3. with xxx insert into 这种会被误认为 select 类型，已处理
        4. insert overwrite table 语句，要写入的表，识别不到
        5. insert into xxx partition (dt) 里的 dt 会被识别成表
        6. create table xxx(xxx) partitioned by (dt string) 里的 dt 会被识别成表
        7. 有些注释好像会导致解析错误（待确认），现在会提前去掉注释
    """

    NOT_SUPPORT_PREFIXES = (
        "SET",
        "COMPUTE",
        "REFRESH",
        "DROP STATS",
        "DROP INCREMENTAL STATS",
        "INVALIDATE METADATA",
        "SHOW TABLE",
        "DESCRIBE ",
        "TRUNCATE ",
        "MSCK REPAIR TABLE ",
        "USE ",
        "CREATE DATABASE",
        "CREATE EXTERNAL TABLE",
        "CREATE VIEW",
        "DROP VIEW",  # todo: view 表看要不要解析
        "DROP FUNCTION",
        "CREATE FUNCTION",
        "SHOW FUNCTIONS",
        "COMMENT ON",
        "GRANT ",
        "IF NOT EXISTS",
        "UNLOAD",
        "VACUUM",  # redshift ,
    )

    NOT_TABLE_KEYS = ("PARTITION", "TABLE", "WHERE")

    def __init__(self, sql: str, default_db: str, ds_name: str, ds_type: str) -> None:
        super().__init__(sql)
        self.default_db = default_db
        self.ds_name = ds_name
        self.dialect = ds_type  # todo: current not used

    def _preprocess_query(self):
        """
        sql-metadata 会特殊处理 "，导致后续解析报错。
        这里先替换掉，后续可能需要对不同的 dialect 分别处理
            比如: hive/impala 不需要把 " 替换成 `
        :return:
        """
        query = self._raw_query
        query = re.sub(r"as\(", "AS (", query, flags=re.I)
        return query

    def __repr__(self):
        return f"parser: query_type {self.query_type};tables {self.tables}"

    @classmethod
    def not_supported_query(cls, ds_type, query):
        query = query.strip().upper()
        for prefix in cls.NOT_SUPPORT_PREFIXES:
            if query.startswith(prefix):
                return True
        return False

    @property
    def query_type(self) -> "QueryType":
        if self._query_type:
            return self._query_type
        query_type = super().query_type
        if query_type == QueryType.SELECT:  # with xxx insert into 这种会被误认为 select 类型
            insert_table = self.get_insert_table_name()
            if insert_table:
                self._query_type = query_type = QueryType.INSERT
        return query_type

    @property
    def tables(self):
        """
        1. 防止把 partition (dt) 也误认为 tables
        2. 防止把 insert into table 中的 table 当做 tables
        """
        if self._tables is not None:
            return self._tables

        tables = UniqueList()
        with_names = self.with_names

        for token in self._not_parsed_tokens:
            if not token.is_potential_table_name:
                continue
            if (
                token.is_alias_of_table_or_alias_of_subquery
                or token.is_with_statement_nested_in_subquery
                or token.is_constraint_definition_inside_create_table_clause(query_type=self.query_type)
                or token.is_columns_alias_of_with_query_or_column_in_insert_query(with_names=with_names)
            ):
                continue

            if token.normalized in self.NOT_TABLE_KEYS:
                continue

            # 防止 insert into xxx partition (dt) 里的 dt 被识别成 table
            # 防止 create table xxx(xxx) partitioned by (dt string) 里的 dt 被识别成 table
            left_parenthesis = token.find_nearest_token(
                value=True, value_attribute="is_left_parenthesis", direction="left"
            )
            right_parenthesis = token.find_nearest_token(
                value=True, value_attribute="is_right_parenthesis", direction="left"
            )
            if (left_parenthesis and right_parenthesis and left_parenthesis.position > right_parenthesis.position) or (
                left_parenthesis and not right_parenthesis
            ):
                if left_parenthesis.previous_token and left_parenthesis.previous_token.normalized in (
                    "PARTITION",
                    "BY",
                ):
                    continue

            table_name = str(token.value.strip("`"))
            token.token_type = TokenType.TABLE
            tables.append(table_name.lower())  # # 额外添加了 lower()，防止 with_names 和 tables 大小写不一致

        self._tables = []
        for table in tables - UniqueList([name.lower() for name in with_names]):
            self._tables.append(table)
        return self._tables

    def get_insert_table_name(self):
        sql = self._query.lower()
        if "insert into" not in sql and "insert overwrite" not in sql:
            return

        insert_token = None
        for try_num in range(99):
            if insert_token is None:
                if self.tokens[0].normalized == "INSERT":
                    insert_token = self.tokens[0]
                else:
                    insert_token = self.tokens[0].find_nearest_token(
                        "INSERT", value_attribute="normalized", direction="right"
                    )
            else:
                insert_token = insert_token.find_nearest_token(
                    "INSERT", value_attribute="normalized", direction="right"
                )
            if insert_token.position < 0:
                return
            if insert_token.next_token.normalized in ("INTO", "OVERWRITE"):
                break
        else:
            return

        table_token = insert_token.next_token.next_token
        if table_token.normalized == "TABLE":
            table_token = table_token.next_token
        insert_table_name = table_token.value.lower()
        if insert_table_name not in self.tables:
            logger.warning(
                f"get_insert_table_name error: " f"table_token {insert_table_name} _tables {self._tables}, please check"
            )
        return insert_table_name

    def get_create_table_name(self):
        if self.query_type != QueryType.CREATE:
            return
        return (self.tables and self.tables[0]) or None

    def get_lineage(self):
        if self.query_type == QueryType.DROP:
            return LineageResult([], self._format_table(self.tables[0]), self.query_type, self._raw_query)
        if self.query_type in (QueryType.ALTER, QueryType.DELETE):
            return
        tables = self.tables[:]
        downstream_table = (
            self.get_create_table_name() or self.get_insert_table_name()
        )  # todo: update/upsert table not supported
        if downstream_table:
            if downstream_table in tables:
                tables.remove(downstream_table)
            if not tables:
                return
            return LineageResult(
                self._format_table(tables), self._format_table(downstream_table), self.query_type, self._raw_query
            )

    def _format_table(self, table_or_tables: Union[list[str], str]):
        if isinstance(table_or_tables, list):
            res_lst = []
            for table in table_or_tables:
                if "." in table:
                    db, table = table.split(".")  # todo: redshift
                else:
                    db = self.default_db
                res_lst.append(Table(data_source=self.ds_name, database=db, table=table))
            return res_lst
        else:
            if "." in table_or_tables:
                db, table = table_or_tables.split(".")  # todo: redshift
            else:
                db, table = self.default_db, table_or_tables
            return Table(data_source=self.ds_name, database=db, table=table)


class LineageResult(object):
    def __init__(self, upstream_tables: list[Table], downstream_table: Table, query_type: "QueryType", sql: str):
        self.upstream_tables = upstream_tables
        self.downstream_table = downstream_table
        self.query_type = query_type
        self.sql = sql

    def to_dict(self):
        return {
            "upstream": [dict(table._asdict()) for table in self.upstream_tables],
            "downstream": dict(self.downstream_table._asdict()),
            "query_type": self.query_type.value,
            "sql": self.sql,
            "version": VERSION,
            "created_at": datetime.datetime.now(),
        }


def parse_lineage(sql, default_db, recurve_ds_name, recurve_ds_type):
    lineage_lst = []
    raw_sql = sql
    remove_comment_sql = sqlparse.format(raw_sql, strip_comments=True)
    for sql in sqlparse.split(remove_comment_sql):
        sql = sql.strip(";\n\r\t ")
        if not sql:
            continue
        if LineageParser.not_supported_query(recurve_ds_type, sql):
            logger.debug(f"currently lineage not support ds_type {recurve_ds_type}")
            continue
        parser = LineageParser(sql, default_db, recurve_ds_name, recurve_ds_type)
        lineage_result = parser.get_lineage()
        if not lineage_result:
            continue
        lineage_lst.append(lineage_result.to_dict())

    return lineage_lst


def supported_recurve_ds_type(ds_type):
    return ds_type in ("hive", "impala")

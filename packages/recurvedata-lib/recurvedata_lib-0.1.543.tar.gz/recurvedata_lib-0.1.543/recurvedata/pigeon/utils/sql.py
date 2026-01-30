from typing import Callable

import sqlparse
import sqlparse.keywords
import sqlparse.sql
import sqlparse.tokens


def staging_table_of(table: str) -> str:
    return f"z_{table}_staging"


def reconcile_table_of(table: str) -> str:
    return f"z_{table}_reconcile"


def bak_table_of(table: str) -> str:
    return f"z_{table}_bak"


def trim_prefix(s: str, sub: str, ignore_case: bool = True) -> str:
    head = s[: len(sub)]
    if ignore_case:
        has_prefix = head.lower() == sub.lower()
    else:
        has_prefix = head == sub
    if not has_prefix:
        return s
    return s[len(sub) :]


def apply_where_naively(query: str, where: str) -> str:
    if not where:
        return query

    where = trim_prefix(where, "where")
    if "where" in query.lower():
        query = "{} AND {}".format(query, where)
    else:
        query = "{} WHERE {}".format(query, where)
    return query


def apply_where_safely(query: str, where: str) -> str:
    if not where:
        return query

    where = trim_prefix(where, "where")

    parsed = sqlparse.parse(query)[0]

    idx, old_where_token = parsed.token_next_by(i=sqlparse.sql.Where)
    # there is already a WHERE clause, replace it
    if idx is not None:
        # add the new condition to an new line, see https://gitlab.yimian.com.cn/etl/pigeon/issues/4
        new_where = "{}\nAND {}\n".format(old_where_token.value, where)
        new_where_token = sqlparse.sql.Where([sqlparse.sql.Token(None, new_where)])
        parsed.tokens[idx] = new_where_token
        return str(parsed)

    # there is no WHERE clause, so we should create a new one and insert into the right place
    next_idx = None
    for i, token in enumerate(parsed.tokens):
        if token.is_keyword and token.value.upper() in ("ORDER", "GROUP", "LIMIT", "HAVING"):
            next_idx = i
            break

    # add WHERE clause to an new line, see https://gitlab.yimian.com.cn/etl/pigeon/issues/4
    new_where = "\nWHERE {}\n".format(where)
    # sqlparse.sql.Where.ttype is None
    new_where_token = sqlparse.sql.Where([sqlparse.sql.Token(None, new_where)])
    if next_idx is None:
        next_idx = len(parsed.tokens)
    parsed.insert_before(next_idx, new_where_token)
    return str(parsed)


def extract_from_clause(query: str) -> str:
    """Extract the FROM clause from a SQL query.

    Args:
        query (str): The SQL query

    Returns:
        str: The FROM clause without GROUP BY, ORDER BY, HAVING, or LIMIT
    """
    parsed = sqlparse.parse(query)[0]

    start_idx = None
    end_idx = None

    # Find FROM token
    for i, t in enumerate(parsed.tokens):
        if t.value.upper() == "FROM":
            start_idx = i + 1
            break

    if start_idx is None:
        return ""

    # Find the end of FROM clause by looking for GROUP BY, ORDER BY, HAVING, LIMIT
    for i, t in enumerate(parsed.tokens[start_idx:], start=start_idx):
        if t.is_keyword and t.value.upper() in ("GROUP", "ORDER", "LIMIT", "HAVING"):
            end_idx = i
            break
        elif isinstance(t, sqlparse.sql.Where):
            end_idx = i
            break

    if end_idx is None:
        end_idx = len(parsed.tokens)

    tokens = parsed.tokens[start_idx:end_idx]
    tl = sqlparse.sql.TokenList(tokens)
    return str(tl).strip()


def extract_where_clause(query: str) -> str:
    parsed = sqlparse.parse(query)[0]
    idx, where_token = parsed.token_next_by(i=sqlparse.sql.Where)
    if idx is None:
        return ""

    return where_token.value


def extract_limit_count(query: str) -> int | None:
    parsed = sqlparse.parse(query)[0]
    idx = 0
    for i, t in enumerate(parsed.tokens):
        if t.value.upper() == "LIMIT":
            idx = i + 2
            break
    if not idx:
        return None
    return int(parsed.tokens[idx].value)


def mssql_extract_limit_count(query: str) -> int | None:
    """Extract the TOP limit from a SQL Server query.

    Args:
        query (str): The SQL query

    Returns:
        int | None: The TOP limit value, or None if not found
    """

    def _get_first_token_from_identifier_list(token):
        if isinstance(token, (sqlparse.sql.IdentifierList, sqlparse.sql.Identifier)):
            return _get_first_token_from_identifier_list(token.token_first(skip_cm=True))
        return token

    if "TOP" not in sqlparse.keywords.KEYWORDS:
        sqlparse.keywords.KEYWORDS["TOP"] = sqlparse.tokens.Keyword

    parsed = sqlparse.parse(query)[0]
    idx = 0
    for i, t in enumerate(parsed.tokens):
        if t.value.upper() == "TOP":
            idx = i + 2
            break
    if not idx:
        return None

    value_token = _get_first_token_from_identifier_list(parsed.tokens[idx])
    # Remove parentheses if present
    value = value_token.value.strip("()")
    return int(value)


def apply_limit(query: str, count: int) -> str:
    parsed = sqlparse.parse(query)[0]
    idx = 0
    for i, t in enumerate(parsed.tokens):
        if t.value.upper() == "LIMIT":
            idx = i + 2
            break
    if not idx:
        return f"{query} LIMIT {count}"
    parsed.tokens[idx].value = str(count)
    return str(parsed)


def mssql_apply_limit(query: str, count: int) -> str:
    parsed = sqlparse.parse(query)[0]

    select_idx = top_idx = sel_start_idx = None
    for i, t in enumerate(parsed.tokens):
        if select_idx is None and t.value.upper() == "SELECT":
            select_idx = i
        if select_idx is not None and sel_start_idx is None:
            if isinstance(t, (sqlparse.sql.IdentifierList, sqlparse.sql.Identifier)):
                sel_start_idx = i
            if isinstance(t, sqlparse.sql.Token) and t.ttype == sqlparse.tokens.Wildcard:
                sel_start_idx = i
        if t.value.upper() == "TOP":
            top_idx = i + 2
            break
    if not top_idx:
        white_space = sqlparse.sql.Token(sqlparse.tokens.Whitespace, " ")
        add_tokens = [
            sqlparse.sql.Token(sqlparse.tokens.Keyword, "TOP"),
            white_space,
            sqlparse.sql.Token(sqlparse.tokens.Number, count),
            white_space,
        ]
        parsed.tokens = parsed.tokens[:sel_start_idx] + add_tokens + parsed.tokens[sel_start_idx:]
        return str(parsed)
    parsed.tokens[top_idx].value = str(count)
    return str(parsed)


def apply_sql_no_cache(query: str) -> str:
    """Add SQL_NO_CACHE hint to a SELECT query.

    Args:
        query (str): The SQL query

    Returns:
        str: Query with SQL_NO_CACHE hint added
    """
    parsed = sqlparse.parse(query)[0]
    if "/*" in query:
        return query

    comment = "/*!40001 SQL_NO_CACHE*/"
    token = sqlparse.sql.Comment([sqlparse.sql.Token(None, comment)])

    # Find SELECT token and insert hint right after it
    for i, t in enumerate(parsed.tokens):
        if t.value.upper() == "SELECT":
            # Add a single space after SELECT
            space_token = sqlparse.sql.Token(sqlparse.tokens.Whitespace, " ")
            parsed.tokens.insert(i + 1, space_token)
            parsed.tokens.insert(i + 2, token)

            # Add a space after the comment
            space_token2 = sqlparse.sql.Token(sqlparse.tokens.Whitespace, " ")
            parsed.tokens.insert(i + 3, space_token2)

            break
    return str(parsed)


def sqlformat(query: str, reindent: bool = False, **kwargs) -> str:
    kwargs.update({"reindent": True, "keyword_case": "upper"})
    rv = sqlparse.format(query.strip(), **kwargs)
    if not reindent:
        rv = " ".join(x.strip() for x in rv.splitlines())
    return rv


def add_schema_to_create_table(
    create_table_ddl: str, schema: str, quote_callback: Callable[[str], str] | None = None
) -> str:
    """Add schema to a CREATE TABLE statement if the table name doesn't already have a schema.

    Args:
        create_table_ddl (str): The CREATE TABLE DDL statement
        schema (str): The schema name to add
        quote_callback (Optional[QuoteCallback]): Optional callback function to quote table names.
            The callback should accept a string (either 'table' or 'schema.table')
            and return the properly quoted string.

    Returns:
        str: Modified CREATE TABLE statement with schema added, or original if no modification needed
    """
    if not schema or not create_table_ddl or "CREATE TABLE" not in create_table_ddl.upper():
        return create_table_ddl

    parsed = sqlparse.parse(create_table_ddl)[0]

    # Find the CREATE TABLE tokens
    for token in parsed.tokens:
        if isinstance(token, sqlparse.sql.Identifier):
            token_str = str(token)

            # Check if it already has a schema
            if "." in token_str:
                # Already has schema, if we have a quote callback, apply it
                if quote_callback:
                    parts = token_str.split(".")
                    schema_part = parts[0].strip()
                    table_part = ".".join(parts[1:]).strip()

                    # Extract actual names without quotes
                    quote_chars = ["`", '"', "[", "]"]
                    clean_schema = schema_part
                    clean_table = table_part

                    for char in quote_chars:
                        clean_schema = clean_schema.replace(char, "")
                        clean_table = clean_table.replace(char, "")

                    # Apply quote callback to the extracted schema.table
                    qualified_name = f"{clean_schema}.{clean_table}"
                    new_name = quote_callback(qualified_name)

                    # Replace the token
                    token.tokens = [sqlparse.sql.Token(sqlparse.tokens.Name, new_name)]
                return str(parsed)

            # No schema, need to add one
            table_name = token.get_real_name()
            original = token.value

            # Special case for SQL Server bracket style
            if original.startswith("[") and original.endswith("]"):
                new_name = f"{schema}.{table_name}"
            # Handle other quoted identifiers
            elif "`" in original:
                new_name = f"{schema}.`{table_name}`"
            elif '"' in original:
                new_name = f'{schema}."{table_name}"'
            else:
                new_name = f"{schema}.{table_name}"

            if quote_callback:
                # Apply quote callback to new schema.table
                qualified_name = f"{schema}.{table_name}"
                new_name = quote_callback(qualified_name)

            # Replace the token
            token.tokens = [sqlparse.sql.Token(sqlparse.tokens.Name, new_name)]
            break

    return str(parsed)

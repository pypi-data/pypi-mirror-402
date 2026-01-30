import logging

import sqlglot
from sqlglot import exp

logger = logging.getLogger(__name__)


def trim_replace_special_character(sql: str, strip_sufix: bool = False) -> str:
    sql = sql.replace("\\n", "\n")  # todo: may cause error if \\n is in `like '%\\n%'` format
    # process \\n in sql
    if strip_sufix:
        sql = sql.strip(";")
    return sql


def extract_order_by_from_sql(sql: str, dialect: str | None) -> list[dict[str, str]] | None:
    """
    Extract ORDER BY clause from SQL and convert to orders format.

    Args:
        sql: SQL statement to parse
        dialect: Database dialect (e.g., 'mysql', 'postgres')

    Returns:
        List of order dicts in format [{"field": "col1", "order": "ASC"}, ...] or None if no ORDER BY
    """
    try:
        parsed = sqlglot.parse_one(sql, read=dialect)
        if not parsed:
            return None

        # Find ORDER BY in the parsed SQL
        order_by = None
        # Check if it's a SELECT statement with ORDER BY
        if isinstance(parsed, exp.Select):
            order_by = parsed.args.get("order")
        else:
            # Try to find ORDER BY in subqueries or CTEs
            for select in parsed.find_all(exp.Select):
                if select.args.get("order"):
                    order_by = select.args.get("order")
                    break

        if not order_by:
            return None

        orders = []
        # order_by is an exp.Order object, which contains exp.Ordered expressions
        # Access expressions via args.get("expressions") or direct attribute
        expressions = order_by.expressions if hasattr(order_by, "expressions") else order_by.args.get("expressions", [])

        for ordered_expr in expressions:
            if isinstance(ordered_expr, exp.Ordered):
                # Get the column/expression being ordered
                expr = ordered_expr.this
                # Extract field name
                if isinstance(expr, exp.Column):
                    # For columns, get the name (ignore table alias as order_sql will use subquery alias)
                    field_name = expr.name
                elif isinstance(expr, exp.Identifier):
                    field_name = expr.name
                else:
                    # For complex expressions (e.g., functions, calculations), use the SQL representation
                    # But try to extract column name if it's a simple expression
                    if hasattr(expr, "name"):
                        field_name = expr.name
                    else:
                        # For complex expressions, we'll use the SQL representation
                        # This might not work perfectly with order_sql, but it's better than nothing
                        field_name = expr.sql(dialect=dialect) if dialect else str(expr)

                # Get sort direction (ASC/DESC)
                # Check if desc is True (DESC) or False/None (ASC)
                direction = ordered_expr.args.get("desc", False)
                order = "DESC" if direction else "ASC"

                orders.append({"field": field_name, "order": order})

        return orders if orders else None
    except Exception as e:
        # If parsing fails, log and return None (fallback to original behavior)
        logger.warning(f"Failed to extract ORDER BY from SQL: {e}")
        return None

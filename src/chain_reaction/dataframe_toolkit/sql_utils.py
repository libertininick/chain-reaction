"""SQL utilities for parsing and validating SQL queries.

This module provides functions for validating SQL syntax using SQLglot.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import Final

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import Scope, build_scope, find_all_in_scope

from chain_reaction.dataframe_toolkit.exceptions import (
    ParseErrorDict,
    SQLBlacklistedCommandError,
    SQLColumnError,
    SQLSyntaxError,
    SQLTableError,
)

__all__ = ["DESTRUCTIVE_COMMANDS", "parse_sql", "validate_sql_columns", "validate_sql_tables"]

# Common destructive SQL commands that modify or delete data/schema.
# Use with parse_sql's blacklist parameter to block these operations.
DESTRUCTIVE_COMMANDS: Final[frozenset[str]] = frozenset({
    "DROP",
    "DELETE",
    "INSERT",
    "UPDATE",
    "TRUNCATE",
    "ALTER",
    "CREATE",
})


# --- Public Interface ---


def parse_sql(
    query: str, *, dialect: str | None = None, blacklist: Collection[str] | None = None
) -> sqlglot.Expression:
    """Parses the query using SQLglot to detect syntax errors and returns the parsed expression.

    If the query is syntactically valid, returns normally. If the query has syntax
    errors, raises SQLSyntaxError with details about the parse errors. Optionally
    validates the command type against a blacklist of disallowed commands.

    Args:
        query (str): The SQL query string to validate.
        dialect (str | None): Optional SQL dialect to use for parsing. Defaults to None.
        blacklist (Collection[str] | None): Optional collection of SQL command types to block
            (e.g., {"DELETE", "DROP"}). Matching is case-insensitive. Use
            DESTRUCTIVE_COMMANDS for a pre-defined set of data-modifying commands.
            Defaults to None (no blacklist checking).

    Returns:
        sqlglot.Expression: The parsed SQL expression if the query is valid.

    Raises:
        SQLSyntaxError: If the query is empty, contains only whitespace, or has
            invalid SQL syntax. The exception's `errors` attribute contains a list
            of details about each parse error (description, line, col, context).
        SQLBlacklistedCommandError: If the query's command type is in the blacklist.
            The exception includes the detected command_type and the blacklist.

    Examples:
        Valid SQL query:
        >>> expression = parse_sql("SELECT a FROM t")

        Invalid SQL query:
        >>> try:
        ...     parse_sql("SELECT * FROM (SELECT a FROM t") # Missing closing parenthesis
        ... except SQLSyntaxError as e:
        ...     print("Syntax error caught")
        Syntax error caught

        Blocking destructive commands:
        >>> try:
        ...     parse_sql("DELETE FROM users", blacklist=DESTRUCTIVE_COMMANDS)
        ... except SQLBlacklistedCommandError as e:
        ...     print(f"Blocked: {e.command_type}")
        Blocked: DELETE
    """
    if not query or not query.strip():
        raise SQLSyntaxError("SQL query cannot be empty or whitespace-only", query=query, errors=[])

    try:
        expression = sqlglot.parse_one(query, dialect=dialect)
    except sqlglot.errors.ParseError as e:
        errors: list[ParseErrorDict] = [
            ParseErrorDict(
                description=error_dict.get("description", ""),
                line=error_dict.get("line", 0),
                col=error_dict.get("col", 0),
                start_context=error_dict.get("start_context", ""),
                highlight=error_dict.get("highlight", ""),
                end_context=error_dict.get("end_context", ""),
            )
            for error_dict in e.errors
        ]

        raise SQLSyntaxError(
            message=f"SQL syntax error: {e}",
            query=query,
            errors=errors,
        ) from e

    if blacklist and (command_type := _get_sql_command_type(expression)) is not None:
        normalized_blacklist = {cmd.upper() for cmd in blacklist}
        if command_type.upper() in normalized_blacklist:
            raise SQLBlacklistedCommandError(
                message=f"SQL command '{command_type}' is not allowed.",
                query=query,
                command_type=command_type,
                blacklist=normalized_blacklist,
            )

    return expression


def validate_sql_tables(query: str | exp.Expression, valid_tables: set[str], *, dialect: str | None = None) -> None:
    """Validate that a SQL query only references allowed tables (`valid_tables`).

    Parses the query (if string) and extracts all table references using scope
    analysis to correctly distinguish actual database tables from CTEs. Validates
    that at least one valid table is referenced and no unknown tables are used.

    Note:
        When passing a string query, SQLSyntaxError may be raised by the
        underlying parse_sql() call if the SQL syntax is invalid.

    Args:
        query (str | exp.Expression): The SQL query string or a pre-parsed
            sqlglot Expression (e.g., from parse_sql()).
        valid_tables (set[str]): Set of allowed table names. Matching is
            case-insensitive.
        dialect (str | None): Optional SQL dialect to use for parsing if
            `query` is a string. Defaults to None.

    Raises:
        SQLTableError: If no valid tables are referenced, or if unknown tables
            are referenced. The exception includes the list of invalid table names.

    Examples:
        >>> validate_sql_tables("SELECT a FROM users", {"users"})

        >>> try:
        ...     validate_sql_tables("SELECT a FROM unknown_table", {"users"})
        ... except SQLTableError as e:
        ...     print(f"Invalid tables: {e.invalid_tables}")
        Invalid tables: ['unknown_table']
    """
    if isinstance(query, str):
        expression = parse_sql(query, dialect=dialect)
        query_str = query
    else:
        expression = query
        query_str = expression.sql()

    referenced_table_names = _extract_table_names(expression)

    if not referenced_table_names:
        raise SQLTableError(
            message="Query does not reference any tables. At least one table from valid_tables must be referenced.",
            query=query_str,
            invalid_tables=[],
        )

    normalized_valid_tables = {t.lower() for t in valid_tables}
    invalid_tables = sorted(set(referenced_table_names) - normalized_valid_tables)

    if invalid_tables:
        raise SQLTableError(
            message=f"Query references invalid tables: {invalid_tables}",
            query=query_str,
            invalid_tables=invalid_tables,
        )


def validate_sql_columns(
    query: str | exp.Expression,
    table_columns: dict[str, set[str]],
    *,
    dialect: str | None = None,
) -> None:
    """Validate that a SQL query only references valid columns for base tables.

    Parses the query (if string) and extracts column references, validating them
    against the provided schema (`table_columns`). Only validates columns on base
    (real) tables; columns from derived tables (CTEs, subqueries) or tables not
    in the schema are intentionally skipped.

    Note:
        When passing a string query, SQLSyntaxError may be raised by the
        underlying parse_sql() call if the SQL syntax is invalid.

    Args:
        query (str | exp.Expression): The SQL query string or a pre-parsed
            sqlglot Expression (e.g., from parse_sql()).
        table_columns (dict[str, set[str]]): Mapping of table names to their
            valid column names. Matching is case-insensitive for both table
            names and column names.
        dialect (str | None): Optional SQL dialect to use for parsing if
            `query` is a string. Defaults to None.

    Raises:
        SQLColumnError: If invalid columns are referenced on base tables. The
            exception includes the invalid columns grouped by table and the
            available columns for each table.

    Examples:
        Valid columns on base tables:
        >>> validate_sql_columns(
        ...     "SELECT id, name FROM users",
        ...     {"users": {"id", "name", "email"}},
        ... )

        Invalid column referenced:
        >>> try:
        ...     validate_sql_columns(
        ...         "SELECT id, foo FROM users",
        ...         {"users": {"id", "name"}},
        ...     )
        ... except SQLColumnError as e:
        ...     print(e.format_details())
        Column "foo" not found in table "users". Available columns: id, name

        Table not in schema is skipped:
        >>> validate_sql_columns(
        ...     "SELECT id, bar FROM external_table",
        ...     {"users": {"id", "name"}},
        ... )
    """
    if isinstance(query, str):
        expression = parse_sql(query, dialect=dialect)
        query_str = query
    else:
        expression = query
        query_str = expression.sql()

    normalized_schema: dict[str, set[str]] = {
        table_name.lower(): {col.lower() for col in columns} for table_name, columns in table_columns.items()
    }

    invalid_columns = _collect_invalid_columns(expression, normalized_schema)

    if invalid_columns:
        raise SQLColumnError(
            message=f"Invalid column references: {_build_column_error_message(invalid_columns, table_columns)}",
            query=query_str,
            invalid_columns=invalid_columns,
            table_columns=table_columns,
        )


# --- Private Helpers ---

# Mapping of sqlglot expression types to SQL command type strings for blacklist checking.
# Set operations (Union, Intersect, Except) are considered SELECT queries.
_EXPRESSION_TYPE_MAP: dict[type[exp.Expression], str] = {
    exp.Select: "SELECT",
    exp.Delete: "DELETE",
    exp.Insert: "INSERT",
    exp.Update: "UPDATE",
    exp.Drop: "DROP",
    exp.Create: "CREATE",
    exp.TruncateTable: "TRUNCATE",
    exp.Alter: "ALTER",
    exp.Union: "SELECT",
    exp.Intersect: "SELECT",
    exp.Except: "SELECT",
}


def _get_sql_command_type(expression: exp.Expression) -> str | None:
    """Map a sqlglot expression to its SQL command type string.

    Args:
        expression (exp.Expression): A parsed sqlglot expression.

    Returns:
        str | None: The SQL command type (e.g., "SELECT", "DELETE") or None if
            the expression type is not recognized.
    """
    return _EXPRESSION_TYPE_MAP.get(type(expression))


def _extract_table_names(expression: exp.Expression) -> list[str]:
    """Extract table names from a parsed SQL expression using scope traversal.

    Uses sqlglot's scope analysis to correctly distinguish actual database tables
    from CTEs and subqueries.

    Args:
        expression (exp.Expression): A parsed sqlglot expression.

    Returns:
        list[str]: List of lowercase table names referenced in the query.
            May contain duplicates if the same table is referenced multiple times
            (e.g., in self-joins). Returns empty list if no tables are found.
    """
    root = build_scope(expression)
    if root is None:
        return []  # pragma: no cover

    tables: list[exp.Table] = [
        source
        for scope in root.traverse()
        for _alias, (_node, source) in scope.selected_sources.items()
        if isinstance(source, exp.Table)
    ]

    return [table.name.lower() for table in tables]


def _collect_invalid_columns(
    expression: exp.Expression,
    normalized_schema: dict[str, set[str]],
) -> dict[str, list[str]]:
    """Collect invalid column references from a SQL expression.

    Traverses all scopes in the expression and validates column references
    against the provided schema.

    Args:
        expression (exp.Expression): The parsed SQL expression.
        normalized_schema (dict[str, set[str]]): Lowercase schema mapping table names to column sets.

    Returns:
        dict[str, list[str]]: Mapping of table names to lists of invalid columns.
    """
    root = build_scope(expression)
    if root is None:
        return {}

    invalid_columns: dict[str, list[str]] = {}

    for scope in root.traverse():
        alias_to_table = _build_alias_to_table_map(scope)
        for column in find_all_in_scope(scope.expression, exp.Column):
            _validate_column_in_scope(column, alias_to_table, normalized_schema, invalid_columns)

    return invalid_columns


def _build_alias_to_table_map(scope: Scope) -> dict[str, str]:
    """Build a mapping from table aliases to base table names for a scope.

    Args:
        scope (Scope): A sqlglot scope object with selected_sources attribute.

    Returns:
        dict[str, str]: Mapping from lowercase alias to lowercase base table name.
            Only includes sources that are actual database tables, not CTEs or subqueries.
    """
    return {
        alias.lower(): source.name.lower()
        for alias, (_node, source) in scope.selected_sources.items()
        if isinstance(source, exp.Table)
    }


def _resolve_column_to_base_table(
    column: exp.Column,
    alias_to_table: dict[str, str],
) -> str | None:
    """Resolve a column reference to its base table name.

    Args:
        column (exp.Column): The column expression to resolve.
        alias_to_table (dict[str, str]): Mapping from alias to base table name.

    Returns:
        str | None: The lowercase base table name, or None if the column cannot
            be resolved to a base table (e.g., references a CTE or is ambiguous).
    """
    table_alias = column.table.lower() if column.table else ""

    if table_alias:
        return alias_to_table.get(table_alias)

    # Unqualified column - only resolve if there's exactly one base table
    base_tables = list(alias_to_table.values())
    return base_tables[0] if len(base_tables) == 1 else None


def _validate_column_in_scope(
    column: exp.Column,
    alias_to_table: dict[str, str],
    normalized_schema: dict[str, set[str]],
    invalid_columns: dict[str, list[str]],
) -> None:
    """Validate a single column reference against the schema.

    Args:
        column (exp.Column): The column expression to validate.
        alias_to_table (dict[str, str]): Mapping from alias to base table name.
        normalized_schema (dict[str, set[str]]): Lowercase schema mapping table names to column sets.
        invalid_columns (dict[str, list[str]]): Mutable mapping to collect invalid columns.
    """
    col_name = column.name.lower()
    base_table = _resolve_column_to_base_table(column, alias_to_table)

    # Skip if column doesn't resolve to a base table in our schema
    if base_table is None or base_table not in normalized_schema:
        return

    # Record invalid column if it doesn't exist in the base table's schema
    if col_name not in normalized_schema[base_table]:
        if base_table not in invalid_columns:
            invalid_columns[base_table] = []
        if col_name not in invalid_columns[base_table]:
            invalid_columns[base_table].append(col_name)


def _build_column_error_message(
    invalid_columns: dict[str, list[str]],
    table_columns: dict[str, set[str]],
) -> str:
    """Build a user-friendly error message for invalid column references.

    Args:
        invalid_columns (dict[str, list[str]]): Mapping of table names to lists of invalid column names.
        table_columns (dict[str, set[str]]): Original schema for looking up original-case table names.

    Returns:
        str: Semicolon-separated error message listing all invalid columns.
    """
    return "; ".join(
        f'Column "{col}" not found in table "{_find_original_table_name(table_name, table_columns)}"'
        for table_name, cols in sorted(invalid_columns.items())
        for col in sorted(cols)
    )


def _find_original_table_name(table_name: str, table_columns: dict[str, set[str]]) -> str:
    """Find the original-case table name from the schema.

    Args:
        table_name (str): Lowercase table name to look up.
        table_columns (dict[str, set[str]]): Original schema with potentially mixed-case table names.

    Returns:
        str: The original-case table name from the schema, or the input if not found.
    """
    return next(
        (orig_name for orig_name in table_columns if orig_name.lower() == table_name),
        table_name,
    )

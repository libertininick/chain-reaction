"""SQL utilities for parsing and validating SQL queries.

This module provides functions for validating SQL syntax using SQLglot.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import Final

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import build_scope

from chain_reaction.dataframe_toolkit.exceptions import (
    ParseErrorDict,
    SQLBlacklistedCommandError,
    SQLSyntaxError,
    SQLTableError,
)

__all__ = ["DESTRUCTIVE_COMMANDS", "parse_sql", "validate_sql_tables"]

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


def parse_sql(
    query: str, *, dialect: str | None = None, blacklist: Collection[str] | None = None
) -> sqlglot.Expression:
    """Parses the query using SQLglot to detect syntax errors and returns the parsed expression.

    Parses the query using SQLglot to detect syntax errors. If the query is
    syntactically valid, returns normally. If the query has syntax errors,
    raises SQLSyntaxError with details about the parse errors. Optionally
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
    # Validate non-empty query
    if not query or not query.strip():
        raise SQLSyntaxError("SQL query cannot be empty or whitespace-only", query=query, errors=[])

    try:
        expression = sqlglot.parse_one(query, dialect=dialect)
    except sqlglot.errors.ParseError as e:
        # Extract structured error details from SQLglot's ParseError
        # Only include the keys defined in ParseErrorDict
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

    # Check if the query's command type is blacklisted (if provided)
    if blacklist and (command_type := _get_sql_command_type(expression)) is not None:
        # Normalize to uppercase for case-insensitive comparison
        normalized_blacklist = {cmd.upper() for cmd in blacklist}
        if command_type.upper() in normalized_blacklist:
            raise SQLBlacklistedCommandError(
                message=f"SQL command '{command_type}' is not allowed.",
                query=query,
                command_type=command_type,
                blacklist=normalized_blacklist,
            )

    return expression


def validate_sql_tables(query: str | exp.Expression, valid_tables: set[str]) -> None:
    """Validate that a SQL query only references allowed tables.

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
    # Parse the query if it's a string
    if isinstance(query, str):
        expression = parse_sql(query)
        query_str = query
    else:
        expression = query
        query_str = expression.sql()

    # Extract table names using scope traversal (correctly handles CTEs)
    referenced_table_names = _extract_table_names(expression)

    if not referenced_table_names:
        raise SQLTableError(
            message="Query does not reference any tables.",
            query=query_str,
            invalid_tables=[],
        )

    # Normalize valid_tables to lowercase for case-insensitive matching
    normalized_valid_tables = {t.lower() for t in valid_tables}

    # Find invalid table references
    invalid_tables = sorted(set(referenced_table_names) - normalized_valid_tables)

    if invalid_tables:
        raise SQLTableError(
            message=f"Query references invalid tables: {invalid_tables}",
            query=query_str,
            invalid_tables=invalid_tables,
        )


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
            Returns empty list if no tables are found.
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

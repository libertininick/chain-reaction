"""SQL utilities for parsing and validating SQL queries.

This module provides functions for validating SQL syntax using SQLglot.
"""

from __future__ import annotations

from collections.abc import Collection

import sqlglot
from sqlglot import exp

from chain_reaction.dataframe_toolkit.exceptions import ParseErrorDict, SQLBlacklistedCommandError, SQLSyntaxError

# Common destructive SQL commands that modify or delete data/schema.
# Use with parse_sql's blacklist parameter to block these operations.
DESTRUCTIVE_COMMANDS: frozenset[str] = frozenset({"DROP", "DELETE", "INSERT", "UPDATE", "TRUNCATE", "ALTER", "CREATE"})

# Mapping of sqlglot expression types to SQL command type strings.
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

    # Check if the query's command type is blacklisted (if a blacklist is provided)
    if (
        blacklist
        and (command_type := _get_sql_command_type(expression)) is not None
        and _in_blacklist(expression, blacklist)
    ):
        raise SQLBlacklistedCommandError(
            message="SQL command not allowed.",
            query=query,
            command_type=command_type,
            blacklist={cmd.upper() for cmd in blacklist},
        )

    return expression


def _get_sql_command_type(expression: exp.Expression) -> str | None:
    """Map a sqlglot expression to its SQL command type string.

    Args:
        expression (exp.Expression): A parsed sqlglot expression.

    Returns:
        str | None: The SQL command type (e.g., "SELECT", "DELETE") or None if
            the expression type is not recognized.
    """
    return _EXPRESSION_TYPE_MAP.get(type(expression))


def _in_blacklist(expression: exp.Expression, blacklist: Collection[str]) -> bool:
    """Check if the expression's command type is in the blacklist.

    Args:
        expression (exp.Expression): A parsed sqlglot expression.
        blacklist (Collection[str]): Collection of SQL command types to block (case-insensitive).

    Returns:
        bool: True if the command type is in the blacklist, False otherwise.
            Returns False if the expression type is not recognized.
    """
    command_type = _get_sql_command_type(expression)
    if command_type is None:
        return False

    # Normalize both sides to uppercase for case-insensitive comparison
    normalized_blacklist = {cmd.upper() for cmd in blacklist}
    return command_type.upper() in normalized_blacklist

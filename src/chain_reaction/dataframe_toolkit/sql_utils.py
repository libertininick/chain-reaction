"""SQL utilities for parsing and validating SQL queries.

This module provides functions for validating SQL syntax using SQLglot.
"""

from __future__ import annotations

import sqlglot
import sqlglot.errors

from chain_reaction.dataframe_toolkit.exceptions import ParseErrorDict, SQLSyntaxError

__all__ = ["parse_sql"]


def parse_sql(query: str, *, dialect: str | None = None) -> sqlglot.Expression:
    """Parses the query using SQLglot to detect syntax errors and returns the parsed expression.

    Parses the query using SQLglot to detect syntax errors. If the query is
    syntactically valid, returns normally. If the query has syntax errors,
    raises SQLSyntaxError with details about the parse errors.

    Args:
        query (str): The SQL query string to validate.
        dialect (str | None): Optional SQL dialect to use for parsing. Defaults to None.

    Returns:
        sqlglot.Expression: The parsed SQL expression if the query is valid.

    Raises:
        SQLSyntaxError: If the query is empty, contains only whitespace, or has
            invalid SQL syntax. The exception's `errors` attribute contains a list
            of details about each parse error (description, line, col, context).

    Examples:
        Valid SQL query:
        >>> expression = parse_sql("SELECT a FROM t")

        Invalid SQL query:
        >>> try:
        ...     parse_sql("SELECT * FROM (SELECT a FROM t") # Missing closing parenthesis
        ... except SQLSyntaxError as e:
        ...     print("Syntax error caught")
        Syntax error caught
    """
    # Validate non-empty query
    if not query or not query.strip():
        raise SQLSyntaxError("SQL query cannot be empty or whitespace-only", query=query, errors=[])

    try:
        return sqlglot.parse_one(query, dialect=dialect)
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

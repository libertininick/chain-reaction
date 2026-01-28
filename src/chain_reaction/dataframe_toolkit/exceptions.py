"""Custom exceptions for SQL validation in the DataFrame toolkit.

This module defines a hierarchy of exceptions for SQL validation errors:

- SQLValidationError: Base class for all SQL validation errors. Catch this to
  handle any SQL validation failure.
- SQLSyntaxError: Raised when SQL has invalid syntax (parse errors).
- SQLTableError: Raised when SQL references non-existent tables.
- SQLColumnError: Raised when SQL references non-existent columns.

All exceptions store the query that caused the error and additional
context-specific information for debugging.
"""

from __future__ import annotations

from typing import TypedDict


class ParseErrorDict(TypedDict, total=False):
    """Typed dictionary representing a single SQL parse error.

    All fields are optional to support partial error information from different
    SQL parsers that may not provide all details.

    Attributes:
        description (str): Human-readable explanation of the error.
        line (int): Line number where the error occurred (1-indexed).
        col (int): Column number where the error occurred (1-indexed).
        start_context (str): Text appearing before the error location.
        highlight (str): The problematic text segment that caused the error.
        end_context (str): Text appearing after the error location.
    """

    description: str
    line: int
    col: int
    start_context: str
    highlight: str
    end_context: str


class SQLValidationError(Exception):
    """Base exception for all SQL validation errors.

    Use this as the base class for SQL-related validation failures. Catching
    this exception will catch all SQL validation errors from the toolkit.

    Attributes:
        query (str | None): The SQL query that failed validation.
    """

    query: str | None

    def __init__(self, message: str, query: str | None = None) -> None:
        """Initialize SQLValidationError.

        Args:
            message (str): Description of the validation error.
            query (str | None): The SQL query that failed validation.
        """
        super().__init__(message)
        self.query = query

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        return f"{self.__class__.__name__}(message={str(self)!r}, query={self.query!r})"


class SQLSyntaxError(SQLValidationError):
    """Raised when a SQL query has invalid syntax.

    This exception is raised when the SQL parser cannot parse the query
    due to malformed SQL syntax. Supports multiple parse errors similar to
    SQLglot's ParseError, with each error containing optional location and
    context information.

    Attributes:
        errors (list[ParseErrorDict]): List of parse error dictionaries, each
            containing optional keys: description, line, col, start_context,
            highlight, end_context.

    Examples:
        >>> err = SQLSyntaxError(
        ...     message="Multiple syntax errors",
        ...     errors=[
        ...         {"description": "Missing FROM", "line": 1},
        ...         {"description": "Invalid column", "line": 2},
        ...     ],
        ... )
        >>> len(err.errors)
        2
    """

    errors: list[ParseErrorDict]

    def __init__(
        self,
        message: str,
        query: str | None = None,
        errors: list[ParseErrorDict] | None = None,
    ) -> None:
        """Initialize SQLSyntaxError.

        Args:
            message (str): Description of the syntax error.
            query (str | None): The SQL query that failed parsing.
            errors (list[ParseErrorDict] | None): List of parse error dictionaries
                with optional keys: description, line, col, start_context,
                highlight, end_context.
        """
        super().__init__(message, query=query)
        self.errors = errors or []

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        return f"{self.__class__.__name__}(message={str(self)!r}, query={self.query!r}, errors={self.errors!r})"


class SQLTableError(SQLValidationError):
    """Raised when a SQL query references invalid tables.

    This exception is raised when the SQL query references table names
    that are not registered in the DataFrame context.

    Attributes:
        invalid_tables (list[str]): List of table names that are not registered.
    """

    invalid_tables: list[str]

    def __init__(
        self,
        message: str,
        query: str | None = None,
        invalid_tables: list[str] | None = None,
    ) -> None:
        """Initialize SQLTableError.

        Args:
            message (str): Description of the table error.
            query (str | None): The SQL query with invalid table references.
            invalid_tables (list[str] | None): List of table names that are not registered.
        """
        super().__init__(message, query=query)
        self.invalid_tables = invalid_tables or []

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message={str(self)!r}, query={self.query!r}, "
            f"invalid_tables={self.invalid_tables!r})"
        )


class SQLColumnError(SQLValidationError):
    """Raised when a SQL query references invalid columns.

    This exception is raised when the SQL query references column names
    that do not exist in the specified tables.

    Attributes:
        invalid_columns (dict[str, list[str]]): Mapping of table names to lists of invalid column names.
    """

    invalid_columns: dict[str, list[str]]

    def __init__(
        self,
        message: str,
        query: str | None = None,
        invalid_columns: dict[str, list[str]] | None = None,
    ) -> None:
        """Initialize SQLColumnError.

        Args:
            message (str): Description of the column error.
            query (str | None): The SQL query with invalid column references.
            invalid_columns (dict[str, list[str]] | None): Mapping of table names to
                lists of invalid column names referenced for that table.
        """
        super().__init__(message, query=query)
        self.invalid_columns = invalid_columns or {}

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message={str(self)!r}, query={self.query!r}, "
            f"invalid_columns={self.invalid_columns!r})"
        )

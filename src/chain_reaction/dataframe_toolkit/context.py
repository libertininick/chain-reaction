"""DataFrame context for managing a registry of Polars DataFrames with SQL support."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import Self

import polars as pl


class DataFrameContext:
    """A registry of Polars DataFrames with SQL query support.

    Manages DataFrames by name and provides access via a Polars SQLContext
    for SQL queries. When frames are registered or unregistered, both the
    internal mapping and the underlying SQLContext are updated.

    Examples:
        >>> import polars as pl
        >>> df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

        Initialize context and register a DataFrame
        >>> ctx = DataFrameContext()
        >>> ctx.register("my_table", df)
        DataFrameContext(frames=['my_table'])

        List registered frames
        >>> ctx.frame_names
        ['my_table']

        Number of registered frames
        >>> len(ctx)
        1

        Register another DataFrame
        >>> df2 = pl.DataFrame({"a": [1, 1, 2], "c": ["apple", "banana", "cherry"]})
        >>> ctx.register("another_table", df2)
        DataFrameContext(frames=['my_table', 'another_table'])

        Execute a SQL query against the registered DataFrame
        >>> result = ctx.execute_sql(
        ...     "SELECT my_table.a FROM my_table JOIN another_table ON my_table.a = another_table.a WHERE c = 'banana'"
        ... )

        Get a registered DataFrame by name
        >>> retrieved_df = ctx.get_frame("my_table")

        Unregister a DataFrame
        >>> ctx.unregister("my_table")
        DataFrameContext(frames=['another_table'])
        >>> len(ctx)
        1

        Clear all registered DataFrames
        >>> ctx.clear()
        DataFrameContext(frames=[])
        >>> len(ctx)
        0
    """

    def __init__(self, frames: Mapping[str, pl.DataFrame | pl.LazyFrame] | None = None) -> None:
        """Initialize the DataFrameContext.

        Args:
            frames (Mapping[str, pl.DataFrame | pl.LazyFrame] | None): Optional mapping of names to DataFrames to
                register on initialization. Defaults to None.
        """
        # Initialize internal mapping of registered DataFrames
        self._frames: dict[str, pl.DataFrame | pl.LazyFrame] = {}
        self._sql_context = pl.SQLContext()

        self.register_many(frames or {})

    def __len__(self) -> int:
        """int: Number of registered frames."""
        return len(self._frames)

    def __contains__(self, name: str) -> bool:
        """Check if a frame is registered.

        Args:
            name (str): The name to check.

        Returns:
            bool: True if the frame is registered, False otherwise.
        """
        return name in self._frames

    def __repr__(self) -> str:
        """Return repr(self)."""
        frame_names = ", ".join(f"'{name}'" for name in self._frames)
        return f"DataFrameContext(frames=[{frame_names}])"

    @property
    def frame_names(self) -> list[str]:
        """list[str]: Names of all registered DataFrames (alias for `frames`)."""
        return list(self._frames.keys())

    def execute_sql(self, query: str, *, eager: bool | None = None) -> pl.DataFrame | pl.LazyFrame:
        """Execute a SQL query against the registered DataFrames.

        Args:
            query (str): The SQL query to execute.
            eager (bool | None): Whether to return an eager DataFrame (True) or LazyFrame (False).
                If None, defaults to eager if any registered frames are eager. Defaults to None.

        Returns:
            pl.DataFrame | pl.LazyFrame: The result of the SQL query as a Polars DataFrame or LazyFrame.

        Raises:
            ValueError: If the query is empty or contains only whitespace.
        """
        if not query or not query.strip():
            msg = "SQL query cannot be empty or whitespace-only"
            raise ValueError(msg)

        return self._sql_context.execute(query, eager=eager)

    def get_frame(self, name: str) -> pl.DataFrame | pl.LazyFrame:
        """Get a registered DataFrame by name.

        Args:
            name (str): The name of the registered frame.

        Returns:
            pl.DataFrame | pl.LazyFrame: The registered DataFrame or LazyFrame.

        Raises:
            KeyError: If the name is not registered.
        """
        if name not in self._frames:
            msg = f"Frame '{name}' is not registered"
            raise KeyError(msg)

        return self._frames[name]

    def register(self, name: str, frame: pl.DataFrame | pl.LazyFrame) -> Self:
        """Register a DataFrame or LazyFrame with the given name.

        Args:
            name (str): The name to register the frame under.
            frame (pl.DataFrame | pl.LazyFrame): The DataFrame or LazyFrame to register.

        Returns:
            Self: Self for method chaining.

        Raises:
            KeyError: If the name is already registered.
        """
        # Check for existing registration
        if name in self._frames:
            msg = f"Frame '{name}' is already registered"
            raise KeyError(msg)

        # Register in internal mapping and SQL context
        self._frames[name] = frame
        self._sql_context.register(name, frame)

        return self

    def register_many(self, frames: Mapping[str, pl.DataFrame | pl.LazyFrame]) -> Self:
        """Register multiple DataFrames or LazyFrames.

        Args:
            frames (Mapping[str, pl.DataFrame | pl.LazyFrame]): Mapping of names to DataFrames to register.

        Returns:
            Self: Self for method chaining.
        """
        for name, frame in frames.items():
            self.register(name, frame)
        return self

    def unregister(self, names: str | Collection[str]) -> Self:
        """Unregister a DataFrames by name.

        Args:
            names (str | Collection[str]): The name or names of the frames to unregister.

        Returns:
            Self: Self for method chaining.

        Raises:
            KeyError: If the name is not registered.
        """
        if isinstance(names, str):
            names = [names]

        for name in names:
            # Verify registration exists
            if name not in self._frames:
                msg = f"Frame '{name}' is not registered"
                raise KeyError(msg)

            # Unregister from SQL context
            self._sql_context.unregister(name)

            # Remove from internal mapping
            self._frames.pop(name)

        return self

    def clear(self) -> Self:
        """Unregister all DataFrames.

        Returns:
            Self: Self for method chaining.
        """
        for name in list(self._frames):  # Copy keys to avoid mutation during iteration
            self.unregister(name)
        return self

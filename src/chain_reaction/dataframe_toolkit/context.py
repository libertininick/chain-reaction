"""DataFrame context for managing a registry of Polars DataFrames with SQL support."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import Self

import polars as pl

from chain_reaction.dataframe_toolkit.identifier import DataFrameId


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
        >>> ctx.register("df_abcd1234", df)
        DataFrameContext(frames=['df_abcd1234'])

        List registered frames
        >>> ctx.frame_ids
        ['df_abcd1234']

        Number of registered frames
        >>> len(ctx)
        1

        Register another DataFrame
        >>> df2 = pl.DataFrame({"a": [1, 1, 2], "c": ["apple", "banana", "cherry"]})
        >>> ctx.register("df_efgh5678", df2)
        DataFrameContext(frames=['df_abcd1234', 'df_efgh5678'])

        Execute a SQL query against the registered DataFrame
        >>> result = ctx.execute_sql(
        ...     "SELECT df_abcd1234.a"
        ...     " FROM df_abcd1234 JOIN df_efgh5678 ON df_abcd1234.a = df_efgh5678.a"
        ...     " WHERE c = 'banana'"
        ... )

        Get a registered DataFrame by its identifier
        >>> retrieved_df = ctx.get_frame("df_abcd1234")

        Unregister a DataFrame
        >>> ctx.unregister("df_abcd1234")
        DataFrameContext(frames=['df_efgh5678'])
        >>> len(ctx)
        1

        Clear all registered DataFrames
        >>> ctx.clear()
        DataFrameContext(frames=[])
        >>> len(ctx)
        0
    """

    def __init__(self, frames: Mapping[DataFrameId, pl.DataFrame | pl.LazyFrame] | None = None) -> None:
        """Initialize the DataFrameContext.

        Args:
            frames (Mapping[DataFrameId, pl.DataFrame | pl.LazyFrame] | None): Optional mapping of identifiers to
                DataFrames to register on initialization. Defaults to None.
        """
        # Initialize internal mapping of registered DataFrames
        self._frames: dict[str, pl.DataFrame | pl.LazyFrame] = {}
        self._sql_context = pl.SQLContext()

        self.register_many(frames or {})

    def __len__(self) -> int:
        """int: Number of registered frames."""
        return len(self._frames)

    def __contains__(self, frame_id: DataFrameId) -> bool:
        """Check if a frame is registered.

        Args:
            frame_id (DataFrameId): The identifier to check.

        Returns:
            bool: True if the frame is registered, False otherwise.
        """
        return frame_id in self._frames

    def __repr__(self) -> str:
        """Return repr(self)."""
        frame_names = ", ".join(f"'{name}'" for name in self._frames)
        return f"DataFrameContext(frames=[{frame_names}])"

    @property
    def frame_ids(self) -> list[DataFrameId]:
        """list[DataFrameId]: Identifiers of all registered DataFrames."""
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

    def get_frame(self, fame_id: DataFrameId) -> pl.DataFrame | pl.LazyFrame:
        """Get a registered DataFrame by its identifier.

        Args:
            fame_id (DataFrameId): The identifier of the registered frame.

        Returns:
            pl.DataFrame | pl.LazyFrame: The registered DataFrame or LazyFrame.

        Raises:
            KeyError: If the name is not registered.
        """
        if fame_id not in self._frames:
            msg = f"Frame '{fame_id}' is not registered"
            raise KeyError(msg)

        return self._frames[fame_id]

    def register(self, frame_id: DataFrameId, frame: pl.DataFrame | pl.LazyFrame) -> Self:
        """Register a DataFrame or LazyFrame with the given name.

        Args:
            frame_id (DataFrameId): The identifier to register the frame under.
            frame (pl.DataFrame | pl.LazyFrame): The DataFrame or LazyFrame to register.

        Returns:
            Self: Self for method chaining.

        Raises:
            KeyError: If the identifier is already registered.
        """
        # Check for existing registration
        if frame_id in self._frames:
            msg = f"Frame '{frame_id}' is already registered"
            raise KeyError(msg)

        # Register in internal mapping and SQL context
        self._frames[frame_id] = frame
        self._sql_context.register(frame_id, frame)

        return self

    def register_many(self, frames: Mapping[DataFrameId, pl.DataFrame | pl.LazyFrame]) -> Self:
        """Register multiple DataFrames or LazyFrames.

        Args:
            frames (Mapping[DataFrameId, pl.DataFrame | pl.LazyFrame]): Mapping of names to DataFrames to register.

        Returns:
            Self: Self for method chaining.
        """
        for frame_id, frame in frames.items():
            self.register(frame_id, frame)
        return self

    def unregister(self, frame_ids: str | Collection[str]) -> Self:
        """Unregister a DataFrames by name.

        Args:
            frame_ids (str | Collection[str]): The name or names of the frames to unregister.

        Returns:
            Self: Self for method chaining.

        Raises:
            KeyError: If the name is not registered.
        """
        if isinstance(frame_ids, str):
            frame_ids = [frame_ids]

        for frame_id in frame_ids:
            # Verify registration exists
            if frame_id not in self._frames:
                msg = f"Frame '{frame_id}' is not registered"
                raise KeyError(msg)

            # Unregister from SQL context
            self._sql_context.unregister(frame_id)

            # Remove from internal mapping
            self._frames.pop(frame_id)

        return self

    def clear(self) -> Self:
        """Unregister all DataFrames.

        Returns:
            Self: Self for method chaining.
        """
        all_frame_ids = list(self._frames.keys())
        for frame_id in all_frame_ids:
            self.unregister(frame_id)
        return self

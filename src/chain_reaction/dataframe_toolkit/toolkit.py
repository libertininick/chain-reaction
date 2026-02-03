"""DataFrame toolkit for managing DataFrames with LangChain tool integration."""

from __future__ import annotations

from collections.abc import Mapping

import polars as pl

from chain_reaction.dataframe_toolkit.context import DataFrameContext
from chain_reaction.dataframe_toolkit.identifier import DataFrameId
from chain_reaction.dataframe_toolkit.models import DataFrameReference


class DataFrameToolkit:
    """A toolkit for registering and managing Polars DataFrames for LLM tool access.

    This toolkit provides a high-level interface for working with DataFrames in
    LLM agent contexts. It maintains a registry of DataFrames with descriptive
    metadata that helps agents understand and query the data.

    The toolkit uses composition to manage an internal DataFrameContext for SQL
    query execution while exposing a user-friendly API based on DataFrame names
    rather than internal identifiers.

    Design Note - ID as Primary Key:
        Internally, DataFrames are keyed by their generated ID (e.g., "df_00000001"),
        not by user-provided names. This design choice ensures:

        1. **Single source of truth**: Both the reference registry and the SQL context
           use the same key (ID), eliminating synchronization bugs.
        2. **SQL safety**: User-provided names may contain spaces, reserved words, or
           special characters. The generated ID is always SQL-safe.
        3. **LLM consistency**: LLMs should always use IDs in SQL queries. Keying by
           ID reinforces this as the canonical identifier.

        User-friendly names are stored in the DataFrameReference and resolved via
        O(n) scan when needed. This is acceptable because:
        - Typical usage involves 2-20 DataFrames, making O(n) effectively O(1).
        - Name lookups happen at registration/unregistration, not during queries.

    Examples:
        >>> import polars as pl

        Register a DataFrame with metadata:
        >>> toolkit = DataFrameToolkit()
        >>> df = pl.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        >>> ref = toolkit.register_dataframe(
        ...     "sales",
        ...     df,
        ...     description="Daily sales data",
        ... )
        >>> ref.name
        'sales'

        Register multiple DataFrames at once:
        >>> toolkit = DataFrameToolkit()
        >>> df1 = pl.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        >>> df2 = pl.DataFrame({"id": [1, 2], "name": ["A", "B"]})
        >>> refs = toolkit.register_dataframes({"sales": df1, "products": df2})
        >>> len(refs)
        2

        Unregister a DataFrame:
        >>> toolkit.unregister_dataframe("products")
    """

    def __init__(self) -> None:
        """Initialize the toolkit with an empty DataFrame registry."""
        self._context = DataFrameContext()
        self._references: dict[DataFrameId, DataFrameReference] = {}

    @property
    def references(self) -> tuple[DataFrameReference, ...]:
        """tuple[DataFrameReference, ...]: All registered DataFrame references."""
        return tuple(self._references.values())

    def register_dataframe(
        self,
        name: str,
        dataframe: pl.DataFrame,
        *,
        description: str | None = None,
        column_descriptions: dict[str, str] | None = None,
    ) -> DataFrameReference:
        """Register a DataFrame with the toolkit.

        Creates a DataFrameReference containing metadata about the DataFrame and
        registers it for SQL query access. A generated unique ID is assigned for SQL queries.
        The user-provided name is stored in the DataFrameReference for reference.

        Args:
            name (str): A unique name to identify this DataFrame.
            dataframe (pl.DataFrame): The Polars DataFrame to register.
            description (str | None): Optional description of the DataFrame's contents
                and purpose. Helps LLM agents understand the data. Defaults to None.
            column_descriptions (dict[str, str] | None): Optional mapping of column
                names to descriptions. Helps LLM agents understand column semantics.
                Defaults to None.

        Returns:
            DataFrameReference: A reference containing metadata about the registered
                DataFrame, including its unique ID for SQL queries.

        Raises:
            ValueError: If a DataFrame with the given name is already registered.

        Examples:
            >>> import polars as pl
            >>> toolkit = DataFrameToolkit()
            >>> df = pl.DataFrame({"user_id": [1, 2], "score": [85, 92]})
            >>> ref = toolkit.register_dataframe(
            ...     "user_scores",
            ...     df,
            ...     description="User performance scores",
            ...     column_descriptions={"score": "Performance score from 0-100"},
            ... )
            >>> ref.name
            'user_scores'
        """
        if self._name_exists(name):
            msg = f"DataFrame '{name}' is already registered"
            raise ValueError(msg)

        reference = DataFrameReference.from_dataframe(
            dataframe,
            name=name,
            description=description,
            column_descriptions=column_descriptions,
        )

        # Store by ID to align with _context (both keyed by ID = single source of truth)
        self._context.register(reference.id, dataframe)
        self._references[reference.id] = reference

        return reference

    def register_dataframes(
        self,
        dataframes: Mapping[str, pl.DataFrame],
        *,
        descriptions: Mapping[str, str] | None = None,
        column_descriptions: Mapping[str, dict[str, str]] | None = None,
    ) -> list[DataFrameReference]:
        """Register multiple DataFrames with the toolkit.

        Validates that all names are unique before registering any DataFrames,
        ensuring atomicity of the operation.

        Args:
            dataframes (Mapping[str, pl.DataFrame]): Mapping of names to DataFrames.
            descriptions (Mapping[str, str] | None): Optional mapping of names to
                descriptions. Defaults to None.
            column_descriptions (Mapping[str, dict[str, str]] | None): Optional mapping of names to
                column descriptions. Defaults to None.

        Returns:
            list[DataFrameReference]: List of references for all registered DataFrames,
                in the same order as the input mapping.

        Raises:
            ValueError: If any name is already registered in the toolkit.

        Examples:
            >>> import polars as pl
            >>> toolkit = DataFrameToolkit()
            >>> dfs = {
            ...     "users": pl.DataFrame({"id": [1, 2]}),
            ...     "orders": pl.DataFrame({"id": [1], "user_id": [1]}),
            ... }
            >>> refs = toolkit.register_dataframes(
            ...     dfs,
            ...     descriptions={"users": "User accounts", "orders": "User orders"},
            ... )
            >>> len(refs)
            2
        """
        descriptions = descriptions or {}
        column_descriptions = column_descriptions or {}

        # Validate all names are available before modifying state (O(n*m) but n,m are tiny)
        existing_names = {ref.name for ref in self._references.values()}
        for name in dataframes:
            if name in existing_names:
                msg = f"DataFrame '{name}' is already registered"
                raise ValueError(msg)

        # Build all references first without modifying state (can fail without side effects)
        references = [
            DataFrameReference.from_dataframe(
                dataframe,
                name=name,
                description=descriptions.get(name),
                column_descriptions=column_descriptions.get(name),
            )
            for name, dataframe in dataframes.items()
        ]

        # Commit all at once (only after all references built successfully)
        # Store by ID to align with _context (both keyed by ID = single source of truth)
        for dataframe, reference in zip(dataframes.values(), references, strict=True):
            self._context.register(reference.id, dataframe)
            self._references[reference.id] = reference

        return references

    def unregister_dataframe(self, name: str) -> None:
        """Unregister a DataFrame from the toolkit.

        Removes the DataFrame from both the internal registry and the SQL context.

        Args:
            name (str): The name of the DataFrame to unregister.

        Examples:
            >>> import polars as pl
            >>> toolkit = DataFrameToolkit()
            >>> df = pl.DataFrame({"a": [1, 2, 3]})
            >>> _ = toolkit.register_dataframe("test", df)
            >>> toolkit.unregister_dataframe("test")
        """
        # Resolve name to reference, raising KeyError if not found
        reference = self._get_reference_by_name(name)

        # Delete by ID from both stores (aligned keys = no sync bugs)
        self._context.unregister(reference.id)
        del self._references[reference.id]

    # Private helpers

    def _get_reference_by_name(self, name: str) -> DataFrameReference:
        """Resolve a user-friendly name to its DataFrameReference.

        Performs O(n) scan over registered references. This is acceptable because
        typical usage involves few DataFrames (2-20), and name resolution only
        occurs during registration/unregistration, not during queries.

        Args:
            name (str): The user-friendly name to look up.

        Returns:
            DataFrameReference: The reference with the matching name.

        Raises:
            KeyError: If no DataFrame with the given name is registered.
        """
        for ref in self._references.values():
            if ref.name == name:
                return ref
        msg = f"DataFrame '{name}' is not registered"
        raise KeyError(msg)

    def _name_exists(self, name: str) -> bool:
        """Check if a name is already registered.

        Args:
            name (str): The name to check.

        Returns:
            bool: True if a DataFrame with this name exists, False otherwise.
        """
        return any(ref.name == name for ref in self._references.values())

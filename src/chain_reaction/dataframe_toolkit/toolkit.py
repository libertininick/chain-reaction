"""DataFrame toolkit for managing DataFrames with LangChain tool integration."""

from __future__ import annotations

from collections.abc import Mapping

import polars as pl
from langchain_core.tools import BaseTool, tool

from chain_reaction.dataframe_toolkit.identifier import (
    DATAFRAME_ID_PATTERN,
    DataFrameId,
)
from chain_reaction.dataframe_toolkit.models import (
    DataFrameReference,
    DataFrameToolkitState,
    ToolCallError,
)
from chain_reaction.dataframe_toolkit.persistence import REL_TOL_DEFAULT, restore_registry_from_state
from chain_reaction.dataframe_toolkit.registry import DataFrameRegistry


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

        Restore from saved state:
        >>> state = toolkit.export_state()
        >>> new_toolkit = DataFrameToolkit.from_state(state, {"sales": df1})
    """

    def __init__(self, registry: DataFrameRegistry | None = None) -> None:
        """Initialize the toolkit with an optional DataFrame registry.

        Args:
            registry (DataFrameRegistry | None): An existing registry to use.
                If None, a new empty registry is created. Defaults to None.
        """
        self._registry = registry if registry is not None else DataFrameRegistry()
        self._core_tools = (
            tool(self.get_dataframe_id),
            tool(self.get_dataframe_reference),
        )

    # -------------------------------------------------------------------------
    # Tool Access (Main API)
    # -------------------------------------------------------------------------

    def get_tools(self) -> list[BaseTool]:
        """Return all LangChain tools for this toolkit.

        Combines tools from all categories (core, statistical, plotting, etc.)
        into a single list for convenient agent configuration.

        Returns:
            list[BaseTool]: All available tools for this toolkit instance.

        Examples:
            >>> import polars as pl
            >>> toolkit = DataFrameToolkit()
            >>> _ = toolkit.register_dataframe("test", pl.DataFrame({"a": [1, 2, 3]}))
            >>> tools = toolkit.get_tools()
            >>> len(tools) >= 1
            True
        """
        return [
            *self._core_tools,
        ]

    def get_core_tools(self) -> list[BaseTool]:
        """Return core DataFrame management tools.

        Core tools provide essential DataFrame operations like ID lookup,
        schema inspection, and SQL querying.

        Returns:
            list[BaseTool]: Core tools for DataFrame management.

        Examples:
            >>> import polars as pl
            >>> toolkit = DataFrameToolkit()
            >>> _ = toolkit.register_dataframe("test", pl.DataFrame({"a": [1, 2, 3]}))
            >>> core_tools = toolkit.get_core_tools()
            >>> len(core_tools) >= 1
            True
        """
        return list(self._core_tools)

    # -------------------------------------------------------------------------
    # Public Methods
    # -------------------------------------------------------------------------

    @property
    def references(self) -> tuple[DataFrameReference, ...]:
        """tuple[DataFrameReference, ...]: All registered DataFrame references."""
        return tuple(self._registry.references.values())

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
        if DATAFRAME_ID_PATTERN.match(name):
            msg = f"DataFrame name '{name}' cannot match ID pattern 'df_<8 hex chars>'"
            raise ValueError(msg)

        if self._name_exists(name):
            msg = f"DataFrame '{name}' is already registered"
            raise ValueError(msg)

        reference = DataFrameReference.from_dataframe(
            name,
            dataframe,
            description=description,
            column_descriptions=column_descriptions,
        )

        self._registry.register(reference, dataframe)

        return reference

    def register_dataframes(
        self,
        dataframes: Mapping[str, pl.DataFrame],
        *,
        descriptions: Mapping[str, str] | None = None,
        column_descriptions: Mapping[str, dict[str, str]] | None = None,
    ) -> list[DataFrameReference]:
        """Register multiple DataFrames with the toolkit.

        Validates all inputs before modifying state and commits to the SQL
        context before updating references, so the two stores stay in sync.

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

        # Validate all names before modifying state
        existing_names = {ref.name for ref in self._registry.references.values()}
        for name in dataframes:
            if DATAFRAME_ID_PATTERN.match(name):
                msg = f"DataFrame name '{name}' cannot match ID pattern 'df_<8 hex chars>'"
                raise ValueError(msg)
            if name in existing_names:
                msg = f"DataFrame '{name}' is already registered"
                raise ValueError(msg)

        # Build all references first without modifying state (can fail without side effects)
        references = [
            DataFrameReference.from_dataframe(
                name,
                dataframe,
                description=descriptions.get(name),
                column_descriptions=column_descriptions.get(name),
            )
            for name, dataframe in dataframes.items()
        ]

        # Register each dataframe with its reference atomically
        for ref, df in zip(references, dataframes.values(), strict=True):
            self._registry.register(ref, df)

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

        self._registry.unregister(reference.id)

    def get_dataframe_id(self, name: str) -> DataFrameId | ToolCallError:
        """Get the DataFrameId for a DataFrame by its name.

        Use this tool when you need the unique identifier for a DataFrame
        to use in SQL queries. DataFrame names are human-readable labels
        while IDs are the actual table names in SQL.

        Args:
            name (str): The human-readable name of the DataFrame.

        Returns:
            DataFrameId | ToolCallError: DataFrameId if found, or ToolCallError if
                name not registered or if an ID was passed instead of a name.

        Examples:
            >>> import polars as pl
            >>> toolkit = DataFrameToolkit()
            >>> _ = toolkit.register_dataframe("sales", pl.DataFrame({"a": [1]}))
            >>> toolkit.get_dataframe_id("sales")  # doctest: +ELLIPSIS
            'df_...'
            >>> toolkit.get_dataframe_id("nonexistent")  # doctest: +ELLIPSIS
            ToolCallError(error_type='DataFrameNotFound', ...)
            >>> toolkit.get_dataframe_id("df_1a2b3c4d")  # doctest: +ELLIPSIS
            ToolCallError(error_type='InvalidArgument', ...)
        """
        # Guard: detect if an ID was passed instead of a name
        if DATAFRAME_ID_PATTERN.match(name):
            return ToolCallError(
                error_type="InvalidArgument",
                message=(
                    f"'{name}' is already an ID, not a name. "
                    "This tool converts names to IDs. "
                    "Use the name to look up the ID, or use get_dataframe_reference "
                    "if you need schema details from an ID."
                ),
                details={"available_names": [ref.name for ref in self._registry.references.values()]},
            )

        try:
            reference = self._get_reference_by_name(name)
            return reference.id
        except KeyError:
            return ToolCallError(
                error_type="DataFrameNotFound",
                message=f"DataFrame '{name}' is not registered",
                details={"available_names": [ref.name for ref in self._registry.references.values()]},
            )

    def get_dataframe_reference(self, identifier: str) -> DataFrameReference | ToolCallError:
        """Get detailed information about a DataFrame by name or ID.

        Use this tool to understand a DataFrame schema, column statistics,
        and metadata before writing SQL queries. Returns comprehensive
        information including column names, data types, and summaries.

        Args:
            identifier (str): Either the DataFrame name or its ID (df_xxxxxxxx).

        Returns:
            DataFrameReference | ToolCallError: DataFrameReference with full schema
                info, or ToolCallError if not found.

        Examples:
            >>> import polars as pl
            >>> toolkit = DataFrameToolkit()
            >>> ref = toolkit.register_dataframe("sales", pl.DataFrame({"a": [1]}))
            >>> toolkit.get_dataframe_reference("sales")  # doctest: +ELLIPSIS
            DataFrameReference(...)
            >>> toolkit.get_dataframe_reference(ref.id)  # doctest: +ELLIPSIS
            DataFrameReference(...)
        """
        # Try lookup by ID first (O(1) since registry.references is keyed by ID)
        if identifier in self._registry.references:
            return self._registry.references[identifier]

        # Try lookup by name (O(n) scan)
        try:
            return self._get_reference_by_name(identifier)
        except KeyError:
            pass

        return ToolCallError(
            error_type="DataFrameNotFound",
            message=f"DataFrame '{identifier}' not found by name or ID",
            details={
                "available_names": [ref.name for ref in self._registry.references.values()],
                "available_ids": list(self._registry.references.keys()),
            },
        )

    def export_state(self) -> DataFrameToolkitState:
        """Export the current toolkit state for serialization.

        Returns a DataFrameToolkitState containing all registered references.
        The actual DataFrame data is NOT included - only metadata and provenance.

        Returns:
            DataFrameToolkitState: Serializable state containing all references.

        Examples:
            >>> import polars as pl
            >>> toolkit = DataFrameToolkit()
            >>> _ = toolkit.register_dataframe("sales", pl.DataFrame({"a": [1, 2, 3]}))
            >>> state = toolkit.export_state()
            >>> len(state.references)
            1
        """
        return DataFrameToolkitState(references=list(self._registry.references.values()))

    # -------------------------------------------------------------------------
    # Public Class Methods
    # -------------------------------------------------------------------------

    @classmethod
    def from_state(
        cls,
        state: DataFrameToolkitState,
        base_dataframes: Mapping[str, pl.DataFrame],
        *,
        rel_tol: float = REL_TOL_DEFAULT,
    ) -> DataFrameToolkit:
        """Create a toolkit from saved state and base dataframes.

        This is the recommended way to restore a toolkit from serialized state.
        Matches base dataframes to their state references by name or ID,
        preserving original IDs for proper derivative reconstruction.

        Provided base dataframes are validated against the expected schema
        and column statistics from the saved state to ensure data consistency.

        Validation checks: shape, column names/order, dtype, count, null_count,
        unique_count, min, max, mean, std, p25, p50, p75.

        Args:
            state (DataFrameToolkitState): Serialized state from export_state().
            base_dataframes (Mapping[str, pl.DataFrame]): Mapping of identifier to
                DataFrame for all base tables. Keys can be either names or IDs
                (df_xxxxxxxx format). DataFrames must match the schema and
                statistics from when the state was exported.
            rel_tol (float): Relative tolerance for floating point comparisons
                during validation. Defaults to 1e-9.

        Returns:
            DataFrameToolkit: Fully reconstructed toolkit with all base and
                derivative dataframes.

        Examples:
            Restore by name (most common):

            >>> import polars as pl
            >>> toolkit = DataFrameToolkit()
            >>> df = pl.DataFrame({"a": [1, 2, 3]})
            >>> _ = toolkit.register_dataframe("sales", df)
            >>> state = toolkit.export_state()
            >>> new_toolkit = DataFrameToolkit.from_state(state, {"sales": df})
            >>> len(new_toolkit.references)
            1

            Restore by ID:

            >>> ref = toolkit.references[0]
            >>> new_toolkit = DataFrameToolkit.from_state(state, {ref.id: df})
            >>> len(new_toolkit.references)
            1
        """
        registry = restore_registry_from_state(
            state=state,
            base_dataframes=base_dataframes,
            rel_tol=rel_tol,
        )
        return cls(registry=registry)

    # -------------------------------------------------------------------------
    # Private Helpers
    # -------------------------------------------------------------------------

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
        for ref in self._registry.references.values():
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
        return any(ref.name == name for ref in self._registry.references.values())

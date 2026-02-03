"""State persistence and restoration for DataFrameToolkit.

This module contains functions for restoring a DataFrameToolkit from serialized
state. The main entry point is `restore_from_state()`, which reconstructs all
base and derivative dataframes from a saved DataFrameToolkitState.

The restoration process:
1. Normalizes user-provided dataframe keys to DataFrameIds
2. Validates base dataframes match expected schema and statistics
3. Registers base dataframes with their original references
4. Reconstructs derivative dataframes by replaying SQL queries in dependency order
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from graphlib import CycleError, TopologicalSorter

import polars as pl

from chain_reaction.dataframe_toolkit.context import DataFrameContext
from chain_reaction.dataframe_toolkit.identifier import (
    DATAFRAME_ID_PATTERN,
    DataFrameId,
)
from chain_reaction.dataframe_toolkit.models import (
    ColumnSummary,
    DataFrameReference,
    DataFrameToolkitState,
)

__all__ = ["restore_from_state"]


def restore_from_state(
    state: DataFrameToolkitState,
    base_dataframes: Mapping[str, pl.DataFrame],
    context: DataFrameContext,
    references: dict[DataFrameId, DataFrameReference],
) -> None:
    """Restore DataFrameToolkit state by registering base dataframes and reconstructing derivatives.

    This function mutates the provided context and references in place. It is the
    main entry point for state restoration, handling:

    1. Finding all base references in the state (those without parent dependencies)
    2. Normalizing user-provided dataframe keys to DataFrameIds
    3. Validating all base refs are provided and match expected schema/statistics
    4. Registering base dataframes with their references
    5. Reconstructing derivatives via SQL replay in dependency order

    Args:
        state (DataFrameToolkitState): Serialized state from export_state().
        base_dataframes (Mapping[str, pl.DataFrame]): Mapping of identifier to
            DataFrame for all base tables. Keys can be either names or IDs
            (df_xxxxxxxx format). DataFrames must match the schema and
            statistics from when the state was exported.
        context (DataFrameContext): The DataFrameContext to restore into. Modified in place.
        references (dict[DataFrameId, DataFrameReference]): The references dict
            to restore into. Modified in place.

    Raises:
        ValueError: If a provided key doesn't match any base reference,
            if required base dataframes are missing, or if a DataFrame's
            schema or statistics don't match the expected state.

    Examples:
        Restore a toolkit from saved state:

        >>> from chain_reaction.dataframe_toolkit.persistence import restore_from_state
        >>> from chain_reaction.dataframe_toolkit.context import DataFrameContext
        >>> from chain_reaction.dataframe_toolkit.models import DataFrameToolkitState
        >>> import polars as pl
        >>> # Create empty context and references to restore into
        >>> context = DataFrameContext()
        >>> references = {}
        >>> # Deserialize state from JSON
        >>> state = DataFrameToolkitState(references=[])
        >>> # Restore with base dataframes
        >>> restore_from_state(state, {}, context, references)
    """
    # 1. Find all base references in the state (those without parent dependencies)
    base_refs = {ref.id: ref for ref in state.references if not ref.parent_ids}

    # 2. Normalize user keys to DataFrameId
    normalized_bases = _normalize_dataframe_mapping(
        dataframes=base_dataframes,
        names_to_ids={ref.name: ref.id for ref in base_refs.values()},
    )

    # 3. Validate all base refs in state are provided
    missing_ids = base_refs.keys() - normalized_bases.keys()
    if missing_ids:
        missing_info = [(base_refs[df_id].name, df_id) for df_id in missing_ids]
        msg = f"Missing base dataframes (name, id): {missing_info}"
        raise ValueError(msg)

    # 4. Validate each provided dataframe matches its reference
    for df_id, dataframe in normalized_bases.items():
        ref = base_refs[df_id]
        _validate_dataframe_matches_reference(dataframe, ref)

    # 5. Register base dataframes with their references
    for df_id, dataframe in normalized_bases.items():
        _register_with_reference(base_refs[df_id], dataframe, context, references)

    # 6. Reconstruct derivative dataframes via SQL replay in dependency order
    _reconstruct_derivatives(state, context, references)


# Private helpers


def _normalize_dataframe_mapping(
    *,
    dataframes: Mapping[str, pl.DataFrame],
    names_to_ids: dict[str, DataFrameId],
) -> dict[DataFrameId, pl.DataFrame]:
    """Convert a mapping of names/IDs to DataFrames into a mapping of IDs to DataFrames.

    Args:
        dataframes (Mapping[str, pl.DataFrame]): Dataframes keyed by name or ID (df_xxxxxxxx format).
        names_to_ids (dict[str, DataFrameId]): Mapping from names to DataFrameIds.

    Returns:
        dict[DataFrameId, pl.DataFrame]: Dataframes keyed by their DataFrameId.

    Raises:
        ValueError: If a key doesn't match any base reference.
    """
    ids = set(names_to_ids.values())

    normalized: dict[DataFrameId, pl.DataFrame] = {}
    for key, dataframe in dataframes.items():
        if DATAFRAME_ID_PATTERN.match(key):
            if key not in ids:
                msg = f"ID '{key}' not found in state's base references. Available IDs: {ids}"
                raise ValueError(msg)
            normalized[key] = dataframe
        else:
            if key not in names_to_ids:
                available = list(names_to_ids.keys())
                msg = f"Name '{key}' not found in state's base references. Available names: {available}"
                raise ValueError(msg)
            normalized[names_to_ids[key]] = dataframe
    return normalized


def _validate_dataframe_matches_reference(
    dataframe: pl.DataFrame,
    reference: DataFrameReference,
    *,
    rel_tol: float = 1e-9,
) -> None:
    """Validate that a DataFrame matches the expected schema and statistics from a reference.

    Checks that column names, shape (rows, columns), and column summaries match
    the reference metadata. This ensures data consistency when reconstructing
    from saved state.

    Args:
        dataframe (pl.DataFrame): The DataFrame to validate.
        reference (DataFrameReference): The reference containing expected metadata.
        rel_tol (float): Relative tolerance for floating point comparisons. Defaults to 1e-9.

    Raises:
        ValueError: If column names, shape, or column summaries do not match.
    """
    # Check shapes match
    actual_shape = dataframe.shape
    expected_shape = (reference.num_rows, reference.num_columns)
    if actual_shape != expected_shape:
        msg = f"DataFrame '{reference.name}' shape mismatch. Expected: {expected_shape}, got: {actual_shape}"
        raise ValueError(msg)

    # Check columns match
    actual_columns = dataframe.columns
    expected_columns = reference.column_names

    if actual_columns != expected_columns:
        msg = f"DataFrame '{reference.name}' column mismatch. Expected: {expected_columns}, got: {actual_columns}"
        raise ValueError(msg)

    # Check column summaries match
    for col_name in actual_columns:
        actual_summary = ColumnSummary.from_series(dataframe[col_name])
        expected_summary = reference.column_summaries[col_name]

        mismatches = _compare_column_summaries(actual_summary, expected_summary, rel_tol=rel_tol)
        if mismatches:
            msg = f"DataFrame '{reference.name}' column '{col_name}' statistics mismatch. Differences: {mismatches}"
            raise ValueError(msg)


def _compare_column_summaries(
    actual: ColumnSummary,
    expected: ColumnSummary,
    *,
    rel_tol: float = 1e-9,
) -> dict[str, tuple[object, object]]:
    """Compare two column summaries and return any mismatches.

    Args:
        actual (ColumnSummary): The actual column summary from the DataFrame.
        expected (ColumnSummary): The expected column summary from the reference.
        rel_tol (float): Relative tolerance for floating point comparisons.

    Returns:
        dict[str, tuple[object, object]]: Dictionary of field names to (actual, expected)
            tuples for any fields that don't match. Empty if all fields match.
    """
    mismatches: dict[str, tuple[object, object]] = {}

    exact_fields = ["dtype", "count", "null_count", "unique_count"]
    for field in exact_fields:
        actual_val = getattr(actual, field)
        expected_val = getattr(expected, field)
        if actual_val != expected_val:
            mismatches[field] = (actual_val, expected_val)

    approx_fields = ["min", "max", "mean", "std", "p25", "p50", "p75"]
    for field in approx_fields:
        actual_val = getattr(actual, field)
        expected_val = getattr(expected, field)
        if not _values_nearly_equal(actual_val, expected_val, rel_tol=rel_tol):
            mismatches[field] = (actual_val, expected_val)

    return mismatches


def _floats_nearly_equal(actual: float, expected: float, *, rel_tol: float) -> bool:
    """Compare two floats for near-equality, treating NaN == NaN as True.

    Args:
        actual (float): The actual value to compare.
        expected (float): The expected value to compare against.
        rel_tol (float): Relative tolerance for the comparison.

    Returns:
        bool: True if values are considered equal.
    """
    if math.isnan(actual) and math.isnan(expected):
        return True
    if math.isnan(actual) or math.isnan(expected):
        return False
    return math.isclose(actual, expected, rel_tol=rel_tol)


def _values_nearly_equal(
    actual: float | str | None,
    expected: float | str | None,
    *,
    rel_tol: float = 1e-9,
) -> bool:
    """Check if two values are nearly equal, handling floats, strings, and None.

    Args:
        actual (float | str | None): The actual value to compare.
        expected (float | str | None): The expected value to compare against.
        rel_tol (float): Relative tolerance for float comparisons. Defaults to 1e-9.

    Returns:
        bool: True if values are considered equal.
    """
    if actual is None and expected is None:
        return True
    if actual is None or expected is None:
        return False
    if isinstance(actual, str) and isinstance(expected, str):
        return actual == expected
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return _floats_nearly_equal(actual, expected, rel_tol=rel_tol)
    return False


def _register_with_reference(
    reference: DataFrameReference,
    dataframe: pl.DataFrame,
    context: DataFrameContext,
    references: dict[DataFrameId, DataFrameReference],
) -> None:
    """Register a dataframe with an existing reference, preserving the original ID.

    This is used during state reconstruction to re-associate dataframe data
    with its original reference metadata and ID.

    Args:
        reference (DataFrameReference): The reference containing the original ID
            and metadata.
        dataframe (pl.DataFrame): The actual dataframe data to register.
        context (DataFrameContext): The context to register the dataframe in.
        references (dict[DataFrameId, DataFrameReference]): The references dict to update.
    """
    context.register(reference.id, dataframe)
    references[reference.id] = reference


def _reconstruct_derivatives(
    state: DataFrameToolkitState,
    context: DataFrameContext,
    references: dict[DataFrameId, DataFrameReference],
) -> None:
    """Reconstruct and register derivative dataframes from state.

    Replays SQL queries for derivatives in dependency order.

    Args:
        state (DataFrameToolkitState): The state containing derivative references.
        context (DataFrameContext): The context for SQL execution and registration.
        references (dict[DataFrameId, DataFrameReference]): The registered references.
    """
    for ref in _sort_references_by_dependency_order(state.references):
        if ref.id in references:
            continue

        result_df = _reconstruct_dataframe(ref, context, references)
        _validate_dataframe_matches_reference(result_df, ref)

        context.register(ref.id, result_df)
        references[ref.id] = ref


def _sort_references_by_dependency_order(references: list[DataFrameReference]) -> list[DataFrameReference]:
    """Sort references by dependency order (parents before children).

    Args:
        references (list[DataFrameReference]): References to sort.

    Returns:
        list[DataFrameReference]: Sorted references with parents before children.

    Raises:
        ValueError: If cyclic dependencies are detected in the references.
    """
    refs_by_id = {ref.id: ref for ref in references}

    graph = {ref.id: [pid for pid in ref.parent_ids if pid in refs_by_id] for ref in references}

    try:
        sorted_ids = list(TopologicalSorter(graph).static_order())
    except CycleError as e:
        msg = f"Cyclic dependency detected in references, state may be corrupted: {e}"
        raise ValueError(msg) from e

    return [refs_by_id[ref_id] for ref_id in sorted_ids]


def _reconstruct_dataframe(
    ref: DataFrameReference,
    context: DataFrameContext,
    references: dict[DataFrameId, DataFrameReference],
) -> pl.DataFrame:
    """Reconstruct a single derivative dataframe from its reference.

    Args:
        ref (DataFrameReference): The reference to reconstruct.
        context (DataFrameContext): The context for SQL execution.
        references (dict[DataFrameId, DataFrameReference]): The registered references.

    Returns:
        pl.DataFrame: The reconstructed dataframe.

    Raises:
        ValueError: If the reference is a base dataframe (no source_query),
            if required parents are missing, or if SQL execution fails.
    """
    if not ref.parent_ids:
        available = [r.name for r in references.values()]
        msg = (
            f"Base dataframe '{ref.name}' (id={ref.id}) is not registered. "
            f"Base dataframes must be re-registered before reconstruction. "
            f"Available dataframes: {available}"
        )
        raise ValueError(msg)

    missing_parents = [pid for pid in ref.parent_ids if pid not in references]
    if missing_parents:
        available_ids = list(references.keys())
        msg = (
            f"Cannot reconstruct '{ref.name}': missing parent dataframes {missing_parents}. "
            f"Available IDs: {available_ids}"
        )
        raise ValueError(msg)

    return _execute_reconstruction_query(ref, context)


def _execute_reconstruction_query(ref: DataFrameReference, context: DataFrameContext) -> pl.DataFrame:
    """Execute the SQL query to reconstruct a dataframe.

    Args:
        ref (DataFrameReference): The reference containing the source_query.
        context (DataFrameContext): The context for SQL execution.

    Returns:
        pl.DataFrame: The reconstructed dataframe.

    Raises:
        ValueError: If SQL query is None or execution fails.
        TypeError: If execute_sql(eager=True) returns non-DataFrame type.
    """
    if not ref.source_query:
        msg = f"Reference '{ref.name}' has no source_query for reconstruction"
        raise ValueError(msg)

    try:
        result_df = context.execute_sql(ref.source_query, eager=True)
    except Exception as e:
        msg = f"SQL execution failed while reconstructing '{ref.name}': {e}. Query: {ref.source_query}"
        raise ValueError(msg) from e

    if not isinstance(result_df, pl.DataFrame):
        msg = f"execute_sql(eager=True) returned {type(result_df).__name__}, expected DataFrame"
        raise TypeError(msg)

    return result_df

"""Tests for the persistence module functions."""

from __future__ import annotations

import polars as pl
import pytest
from pytest_check import check

from chain_reaction.dataframe_toolkit.context import DataFrameContext
from chain_reaction.dataframe_toolkit.identifier import DataFrameId
from chain_reaction.dataframe_toolkit.models import (
    ColumnSummary,
    DataFrameReference,
    DataFrameToolkitState,
)
from chain_reaction.dataframe_toolkit.persistence import (
    _compare_column_summaries,
    _normalize_dataframe_mapping,
    _sort_references_by_dependency_order,
    _validate_dataframe_matches_reference,
    _values_nearly_equal,
    restore_from_state,
)

# ruff: noqa: PLR6301, S608


class TestValuesNearlyEqual:
    """Tests for _values_nearly_equal helper function."""

    def test_values_nearly_equal_both_none_returns_true(self) -> None:
        """Given both values are None, When called, Then returns True."""
        # Arrange
        actual = None
        expected = None

        # Act
        result = _values_nearly_equal(actual=actual, expected=expected)

        # Assert
        with check:
            assert result is True

    def test_values_nearly_equal_one_none_returns_false(self) -> None:
        """Given one value is None and other is not, When called, Then returns False."""
        # Arrange/Act/Assert
        with check:
            assert _values_nearly_equal(actual=None, expected=1.0) is False
        with check:
            assert _values_nearly_equal(actual=1.0, expected=None) is False
        with check:
            assert _values_nearly_equal(actual=None, expected="test") is False
        with check:
            assert _values_nearly_equal(actual="test", expected=None) is False

    def test_values_nearly_equal_equal_floats_returns_true(self) -> None:
        """Given two equal float values, When called, Then returns True."""
        # Arrange
        actual = 42.0
        expected = 42.0

        # Act
        result = _values_nearly_equal(actual=actual, expected=expected)

        # Assert
        with check:
            assert result is True

    def test_values_nearly_equal_nearly_equal_floats_within_tolerance_returns_true(
        self,
    ) -> None:
        """Given two floats within relative tolerance, When called, Then returns True."""
        # Arrange - values that differ by a tiny relative amount
        actual = 1.0
        expected = 1.0 + 1e-10  # Within default rel_tol of 1e-9

        # Act
        result = _values_nearly_equal(actual=actual, expected=expected, rel_tol=1e-9)

        # Assert
        with check:
            assert result is True

    def test_values_nearly_equal_different_floats_returns_false(self) -> None:
        """Given two different float values outside tolerance, When called, Then returns False."""
        # Arrange
        actual = 1.0
        expected = 2.0

        # Act
        result = _values_nearly_equal(actual=actual, expected=expected)

        # Assert
        with check:
            assert result is False

    def test_values_nearly_equal_equal_strings_returns_true(self) -> None:
        """Given two equal string values, When called, Then returns True."""
        # Arrange
        actual = "hello"
        expected = "hello"

        # Act
        result = _values_nearly_equal(actual=actual, expected=expected)

        # Assert
        with check:
            assert result is True

    def test_values_nearly_equal_different_strings_returns_false(self) -> None:
        """Given two different string values, When called, Then returns False."""
        # Arrange
        actual = "hello"
        expected = "world"

        # Act
        result = _values_nearly_equal(actual=actual, expected=expected)

        # Assert
        with check:
            assert result is False

    def test_values_nearly_equal_mixed_types_returns_false(self) -> None:
        """Given one string and one float, When called, Then returns False."""
        # Arrange/Act/Assert
        with check:
            assert _values_nearly_equal(actual="1.0", expected=1.0) is False
        with check:
            assert _values_nearly_equal(actual=1.0, expected="1.0") is False

    def test_values_nearly_equal_both_nan_returns_true(self) -> None:
        """Given both values are NaN, When called, Then returns True."""
        # Arrange
        actual = float("nan")
        expected = float("nan")

        # Act
        result = _values_nearly_equal(actual=actual, expected=expected)

        # Assert
        with check:
            assert result is True

    def test_values_nearly_equal_one_nan_returns_false(self) -> None:
        """Given one value is NaN and other is not, When called, Then returns False."""
        # Arrange/Act/Assert
        with check:
            assert _values_nearly_equal(actual=float("nan"), expected=1.0) is False
        with check:
            assert _values_nearly_equal(actual=1.0, expected=float("nan")) is False

    def test_values_nearly_equal_both_true_returns_true(self) -> None:
        """Given both values are True, When called, Then returns True."""
        # Act
        result = _values_nearly_equal(actual=True, expected=True)

        # Assert
        with check:
            assert result is True

    def test_values_nearly_equal_both_false_returns_true(self) -> None:
        """Given both values are False, When called, Then returns True."""
        # Act
        result = _values_nearly_equal(actual=False, expected=False)

        # Assert
        with check:
            assert result is True

    def test_values_nearly_equal_different_bools_returns_false(self) -> None:
        """Given one True and one False, When called, Then returns False."""
        # Arrange/Act/Assert
        with check:
            assert _values_nearly_equal(actual=True, expected=False) is False
        with check:
            assert _values_nearly_equal(actual=False, expected=True) is False

    def test_values_nearly_equal_bool_and_non_bool_returns_false(self) -> None:
        """Given one bool and one non-bool, When called, Then returns False."""
        # Arrange/Act/Assert
        with check:
            assert _values_nearly_equal(actual=True, expected=1.0) is False
        with check:
            assert _values_nearly_equal(actual=1.0, expected=True) is False
        with check:
            assert _values_nearly_equal(actual=False, expected=0.0) is False
        with check:
            assert _values_nearly_equal(actual=0.0, expected=False) is False
        with check:
            assert _values_nearly_equal(actual=True, expected="True") is False
        with check:
            assert _values_nearly_equal(actual="True", expected=True) is False


class TestCompareColumnSummaries:
    """Tests for _compare_column_summaries helper function."""

    def test_compare_column_summaries_identical_returns_empty_dict(self) -> None:
        """Given two identical column summaries, When compared, Then returns empty dict."""
        # Arrange
        series = pl.Series("test_col", [1, 2, 3, 4, 5])
        summary1 = ColumnSummary.from_series(series)
        summary2 = ColumnSummary.from_series(series)

        # Act
        result = _compare_column_summaries(summary1, summary2)

        # Assert
        with check:
            assert result == {}

    def test_compare_column_summaries_dtype_mismatch_returns_dtype_key(self) -> None:
        """Given summaries with different dtypes, When compared, Then returns dict with dtype key."""
        # Arrange
        series_int = pl.Series("col", [1, 2, 3])
        series_float = pl.Series("col", [1.0, 2.0, 3.0])
        summary_int = ColumnSummary.from_series(series_int)
        summary_float = ColumnSummary.from_series(series_float)

        # Act
        result = _compare_column_summaries(summary_int, summary_float)

        # Assert
        with check:
            assert "dtype" in result
        with check:
            assert result["dtype"][0] == "Int64"
        with check:
            assert result["dtype"][1] == "Float64"

    def test_compare_column_summaries_count_mismatch_returns_count_key(self) -> None:
        """Given summaries with different counts, When compared, Then returns dict with count key."""
        # Arrange
        series_short = pl.Series("col", [1, 2, 3])
        series_long = pl.Series("col", [1, 2, 3, 4, 5])
        summary_short = ColumnSummary.from_series(series_short)
        summary_long = ColumnSummary.from_series(series_long)

        # Act
        result = _compare_column_summaries(summary_short, summary_long)

        # Assert
        with check:
            assert "count" in result
        with check:
            assert result["count"] == (3, 5)

    def test_compare_column_summaries_statistical_mismatch_returns_appropriate_keys(
        self,
    ) -> None:
        """Given summaries with different statistics, When compared, Then returns dict with statistical keys."""
        # Arrange - same count but different values (different min/max/mean)
        series1 = pl.Series("col", [1, 2, 3])
        series2 = pl.Series("col", [10, 20, 30])
        summary1 = ColumnSummary.from_series(series1)
        summary2 = ColumnSummary.from_series(series2)

        # Act
        result = _compare_column_summaries(summary1, summary2)

        # Assert - should have min, max, mean differences
        with check:
            assert "min" in result
        with check:
            assert "max" in result
        with check:
            assert "mean" in result


class TestValidateDataframeMatchesReference:
    """Tests for _validate_dataframe_matches_reference function."""

    def test_validate_dataframe_matches_reference_valid_no_exception(self) -> None:
        """Given DataFrame matching reference, When validated, Then no exception raised."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
        reference = DataFrameReference.from_dataframe("test", df)

        # Act/Assert - should not raise
        _validate_dataframe_matches_reference(df, reference)

    def test_validate_dataframe_matches_reference_column_mismatch_raises(self) -> None:
        """Given DataFrame with different columns, When validated, Then raises ValueError."""
        # Arrange
        df_original = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        reference = DataFrameReference.from_dataframe("test", df_original)
        df_different = pl.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})

        # Act/Assert
        with pytest.raises(ValueError, match="column mismatch"):
            _validate_dataframe_matches_reference(df_different, reference)

    def test_validate_dataframe_matches_reference_shape_mismatch_raises(self) -> None:
        """Given DataFrame with different shape, When validated, Then raises ValueError."""
        # Arrange
        df_original = pl.DataFrame({"a": [1, 2, 3]})
        reference = DataFrameReference.from_dataframe("test", df_original)
        df_different = pl.DataFrame({"a": [1, 2, 3, 4, 5]})

        # Act/Assert
        with pytest.raises(ValueError, match="shape mismatch"):
            _validate_dataframe_matches_reference(df_different, reference)

    def test_validate_dataframe_matches_reference_statistics_mismatch_raises(
        self,
    ) -> None:
        """Given DataFrame with different statistics, When validated, Then raises ValueError."""
        # Arrange
        df_original = pl.DataFrame({"a": [1, 2, 3]})
        reference = DataFrameReference.from_dataframe("test", df_original)
        # Same shape and columns but different values
        df_different = pl.DataFrame({"a": [100, 200, 300]})

        # Act/Assert
        with pytest.raises(ValueError, match="statistics mismatch"):
            _validate_dataframe_matches_reference(df_different, reference)


class TestNormalizeDataframeMapping:
    """Tests for _normalize_dataframe_mapping function."""

    def test_normalize_dataframe_mapping_by_name(self) -> None:
        """Given dataframes keyed by name, When normalized, Then returns ID-keyed mapping."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})
        names_to_ids = {"users": "df_00000001", "orders": "df_00000002"}
        dataframes = {"users": df}

        # Act
        result = _normalize_dataframe_mapping(
            dataframes=dataframes,
            names_to_ids=names_to_ids,
        )

        # Assert
        with check:
            assert "df_00000001" in result
        with check:
            assert result["df_00000001"] is df

    def test_normalize_dataframe_mapping_by_id(self) -> None:
        """Given dataframes keyed by ID, When normalized, Then returns ID-keyed mapping."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})
        names_to_ids = {"users": "df_00000001", "orders": "df_00000002"}
        dataframes = {"df_00000001": df}

        # Act
        result = _normalize_dataframe_mapping(
            dataframes=dataframes,
            names_to_ids=names_to_ids,
        )

        # Assert
        with check:
            assert "df_00000001" in result
        with check:
            assert result["df_00000001"] is df

    def test_normalize_dataframe_mapping_unknown_name_raises(self) -> None:
        """Given unknown name key, When normalized, Then raises ValueError."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})
        names_to_ids = {"users": "df_00000001", "orders": "df_00000002"}
        dataframes = {"unknown_name": df}

        # Act/Assert
        with pytest.raises(ValueError, match="Name 'unknown_name' not in state's base references"):
            _normalize_dataframe_mapping(
                dataframes=dataframes,
                names_to_ids=names_to_ids,
            )

    def test_normalize_dataframe_mapping_duplicate_name_and_id_raises(self) -> None:
        """Given same base provided by both name and ID, When normalized, Then raises ValueError."""
        # Arrange - "users" resolves to "df_00000001", so both keys target the same ID
        names_to_ids = {"users": "df_00000001", "orders": "df_00000002"}
        df_a = pl.DataFrame({"a": [1, 2, 3]})
        df_b = pl.DataFrame({"a": [4, 5, 6]})
        dataframes = {"users": df_a, "df_00000001": df_b}

        # Act/Assert
        with pytest.raises(ValueError, match="Duplicate"):
            _normalize_dataframe_mapping(
                dataframes=dataframes,
                names_to_ids=names_to_ids,
            )

    def test_normalize_dataframe_mapping_unknown_id_raises(self) -> None:
        """Given unknown ID key, When normalized, Then raises ValueError."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})
        names_to_ids = {"users": "df_00000001", "orders": "df_00000002"}
        dataframes = {"df_99999999": df}

        # Act/Assert
        with pytest.raises(ValueError, match="ID 'df_99999999' not in state's base references"):
            _normalize_dataframe_mapping(
                dataframes=dataframes,
                names_to_ids=names_to_ids,
            )


class TestSortReferencesByDependencyOrder:
    """Tests for _sort_references_by_dependency_order function."""

    def test_sort_references_base_only(self) -> None:
        """Given only base references (no parents), When sorted, Then all refs returned."""
        # Arrange
        df1 = pl.DataFrame({"a": [1, 2, 3]})
        df2 = pl.DataFrame({"b": [4, 5, 6]})
        ref1 = DataFrameReference.from_dataframe("ref1", df1)
        ref2 = DataFrameReference.from_dataframe("ref2", df2)
        references = [ref1, ref2]

        # Act
        result = _sort_references_by_dependency_order(references)

        # Assert
        with check:
            assert len(result) == 2
        result_ids = {ref.id for ref in result}
        with check:
            assert result_ids == {ref1.id, ref2.id}

    def test_sort_references_chain_dependency(self) -> None:
        """Given chain A -> B -> C, When sorted, Then parents come before children."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})

        # Create A (base)
        ref_a = DataFrameReference.from_dataframe("A", df)

        # Create B (depends on A) - we need to manually set the ID since from_dataframe generates a new one
        ref_b = DataFrameReference(
            id="df_bbbbbbbb",
            name="B",
            description="",
            num_rows=3,
            num_columns=1,
            column_names=["a"],
            column_summaries={"a": ColumnSummary.from_series(df["a"])},
            parent_ids=[ref_a.id],
            source_query="SELECT * FROM A",
        )

        # Create C (depends on B)
        ref_c = DataFrameReference(
            id="df_cccccccc",
            name="C",
            description="",
            num_rows=3,
            num_columns=1,
            column_names=["a"],
            column_summaries={"a": ColumnSummary.from_series(df["a"])},
            parent_ids=[ref_b.id],
            source_query="SELECT * FROM B",
        )

        # Arrange in reverse order
        references = [ref_c, ref_b, ref_a]

        # Act
        result = _sort_references_by_dependency_order(references)

        # Assert - A should come before B, B before C
        result_ids = [ref.id for ref in result]
        a_index = result_ids.index(ref_a.id)
        b_index = result_ids.index(ref_b.id)
        c_index = result_ids.index(ref_c.id)

        with check:
            assert a_index < b_index, "A should come before B"
        with check:
            assert b_index < c_index, "B should come before C"

    def test_sort_references_diamond_dependency(self) -> None:
        """Given diamond A -> B, A -> C, B -> D, C -> D, When sorted, Then correct topological order."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})
        col_summary = {"a": ColumnSummary.from_series(df["a"])}

        # Create A (base)
        ref_a = DataFrameReference(
            id="df_aaaaaaaa",
            name="A",
            description="",
            num_rows=3,
            num_columns=1,
            column_names=["a"],
            column_summaries=col_summary,
            parent_ids=[],
        )

        # Create B (depends on A)
        ref_b = DataFrameReference(
            id="df_bbbbbbbb",
            name="B",
            description="",
            num_rows=3,
            num_columns=1,
            column_names=["a"],
            column_summaries=col_summary,
            parent_ids=[ref_a.id],
            source_query="SELECT * FROM A",
        )

        # Create C (depends on A)
        ref_c = DataFrameReference(
            id="df_cccccccc",
            name="C",
            description="",
            num_rows=3,
            num_columns=1,
            column_names=["a"],
            column_summaries=col_summary,
            parent_ids=[ref_a.id],
            source_query="SELECT * FROM A",
        )

        # Create D (depends on B and C)
        ref_d = DataFrameReference(
            id="df_dddddddd",
            name="D",
            description="",
            num_rows=3,
            num_columns=1,
            column_names=["a"],
            column_summaries=col_summary,
            parent_ids=[ref_b.id, ref_c.id],
            source_query="SELECT * FROM B JOIN C",
        )

        # Arrange in any order
        references = [ref_d, ref_b, ref_c, ref_a]

        # Act
        result = _sort_references_by_dependency_order(references)

        # Assert - A before B and C, B and C before D
        result_ids = [ref.id for ref in result]
        a_index = result_ids.index(ref_a.id)
        b_index = result_ids.index(ref_b.id)
        c_index = result_ids.index(ref_c.id)
        d_index = result_ids.index(ref_d.id)

        with check:
            assert a_index < b_index, "A should come before B"
        with check:
            assert a_index < c_index, "A should come before C"
        with check:
            assert b_index < d_index, "B should come before D"
        with check:
            assert c_index < d_index, "C should come before D"

    def test_sort_references_cyclic_dependency_raises_error(self) -> None:
        """Given cyclic dependency A -> B -> A, When sorted, Then raises ValueError."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})
        col_summary = {"a": ColumnSummary.from_series(df["a"])}

        # Create A (depends on B) - circular
        ref_a = DataFrameReference(
            id="df_aaaaaaaa",
            name="A",
            description="",
            num_rows=3,
            num_columns=1,
            column_names=["a"],
            column_summaries=col_summary,
            parent_ids=["df_bbbbbbbb"],
            source_query="SELECT * FROM B",
        )

        # Create B (depends on A) - circular
        ref_b = DataFrameReference(
            id="df_bbbbbbbb",
            name="B",
            description="",
            num_rows=3,
            num_columns=1,
            column_names=["a"],
            column_summaries=col_summary,
            parent_ids=["df_aaaaaaaa"],
            source_query="SELECT * FROM A",
        )

        references = [ref_a, ref_b]

        # Act/Assert
        with pytest.raises(ValueError, match="Cyclic dependency detected"):
            _sort_references_by_dependency_order(references)

    def test_sort_references_unknown_parent_id_raises_error(self) -> None:
        """Given reference with unknown parent_id, When sorted, Then raises ValueError."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})
        col_summary = {"a": ColumnSummary.from_series(df["a"])}

        # Create A (base)
        ref_a = DataFrameReference(
            id="df_aaaaaaaa",
            name="A",
            description="",
            num_rows=3,
            num_columns=1,
            column_names=["a"],
            column_summaries=col_summary,
            parent_ids=[],
        )

        # Create B (depends on non-existent reference - use valid ID format)
        ref_b = DataFrameReference(
            id="df_bbbbbbbb",
            name="B",
            description="",
            num_rows=3,
            num_columns=1,
            column_names=["a"],
            column_summaries=col_summary,
            parent_ids=["df_aaaaaaaa", "df_cccccccc"],  # 'df_cccccccc' does not exist
            source_query="SELECT * FROM A JOIN missing",
        )

        references = [ref_a, ref_b]

        # Act/Assert
        with pytest.raises(ValueError, match=r"unknown parent_ids.*df_cccccccc"):
            _sort_references_by_dependency_order(references)


class TestRestoreFromState:
    """Tests for restore_from_state function."""

    def test_restore_from_state_single_base(self) -> None:
        """Given state with single base DataFrame, When restored, Then context has DataFrame."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})
        ref = DataFrameReference.from_dataframe("test", df)
        state = DataFrameToolkitState(references=[ref])
        context = DataFrameContext()
        references: dict[DataFrameId, DataFrameReference] = {}

        # Act
        restore_from_state(state=state, base_dataframes={"test": df}, context=context, references=references)

        # Assert
        with check:
            assert len(references) == 1
        with check:
            assert ref.id in references
        with check:
            assert ref.id in context

    def test_restore_from_state_multiple_bases(self) -> None:
        """Given state with multiple base DataFrames, When restored, Then all in context."""
        # Arrange
        df1 = pl.DataFrame({"a": [1, 2, 3]})
        df2 = pl.DataFrame({"b": [4, 5, 6]})
        ref1 = DataFrameReference.from_dataframe("first", df1)
        ref2 = DataFrameReference.from_dataframe("second", df2)
        state = DataFrameToolkitState(references=[ref1, ref2])
        context = DataFrameContext()
        references: dict[DataFrameId, DataFrameReference] = {}

        # Act
        restore_from_state(
            state=state, base_dataframes={"first": df1, "second": df2}, context=context, references=references
        )

        # Assert
        with check:
            assert len(references) == 2
        with check:
            assert ref1.id in references
        with check:
            assert ref2.id in references
        with check:
            assert ref1.id in context
        with check:
            assert ref2.id in context

    def test_restore_from_state_with_derivative(self) -> None:
        """Given state with derivative, When restored, Then derivative reconstructed."""
        # Arrange
        base_df = pl.DataFrame({"a": [1, 2, 3, 4, 5]})
        base_ref = DataFrameReference.from_dataframe("base", base_df)

        # Create derivative reference that filters to a < 3
        derived_df = pl.DataFrame({"a": [1, 2]})
        derived_ref = DataFrameReference(
            id="df_de11ed11",  # Valid 8 hex chars format (0-9, a-f only)
            name="derived",
            description="Filtered data",
            num_rows=2,
            num_columns=1,
            column_names=["a"],
            column_summaries={"a": ColumnSummary.from_series(derived_df["a"])},
            parent_ids=[base_ref.id],
            source_query=f"SELECT * FROM {base_ref.id} WHERE a < 3",
        )

        state = DataFrameToolkitState(references=[base_ref, derived_ref])
        context = DataFrameContext()
        references: dict[DataFrameId, DataFrameReference] = {}

        # Act
        restore_from_state(state=state, base_dataframes={"base": base_df}, context=context, references=references)

        # Assert
        with check:
            assert len(references) == 2
        with check:
            assert base_ref.id in references
        with check:
            assert derived_ref.id in references
        with check:
            assert derived_ref.id in context

        # Verify reconstructed data
        reconstructed = context.get_dataframe(derived_ref.id)
        with check:
            assert reconstructed.shape == (2, 1)
        with check:
            assert set(reconstructed["a"].to_list()) == {1, 2}

    def test_restore_from_state_missing_base_raises(self) -> None:
        """Given state requiring base not provided, When restored, Then raises ValueError."""
        # Arrange
        df1 = pl.DataFrame({"a": [1, 2, 3]})
        df2 = pl.DataFrame({"b": [4, 5, 6]})
        ref1 = DataFrameReference.from_dataframe("first", df1)
        ref2 = DataFrameReference.from_dataframe("second", df2)
        state = DataFrameToolkitState(references=[ref1, ref2])
        context = DataFrameContext()
        references: dict[DataFrameId, DataFrameReference] = {}

        # Act/Assert - only provide one of two required bases
        with pytest.raises(ValueError, match="Missing base dataframes"):
            restore_from_state(state=state, base_dataframes={"first": df1}, context=context, references=references)

    def test_restore_from_state_empty_state(self) -> None:
        """Given empty state with no references, When restored, Then references remain empty."""
        # Arrange
        state = DataFrameToolkitState(references=[])
        context = DataFrameContext()
        references: dict[DataFrameId, DataFrameReference] = {}

        # Act
        restore_from_state(state=state, base_dataframes={}, context=context, references=references)

        # Assert
        with check:
            assert len(references) == 0

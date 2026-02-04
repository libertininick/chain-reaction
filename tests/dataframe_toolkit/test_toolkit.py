"""Tests for the DataFrameToolkit class."""

from __future__ import annotations

import polars as pl
import pytest
from pytest_check import check

from chain_reaction.dataframe_toolkit.models import (
    DataFrameReference,
    DataFrameToolkitState,
    ToolCallError,
)
from chain_reaction.dataframe_toolkit.toolkit import DataFrameToolkit

# ruff: noqa: PLR6301


class TestDataFrameToolkitInit:
    """Tests for DataFrameToolkit initialization."""

    def test_init_empty_references(self) -> None:
        """Given new toolkit, When checked, Then references is empty."""
        # Arrange/Act
        toolkit = DataFrameToolkit()

        # Assert - use public API (references property)
        with check:
            assert len(toolkit.references) == 0


class TestRegisterDataFrame:
    """Tests for DataFrameToolkit.register_dataframe method."""

    def test_register_success(self) -> None:
        """Given valid DataFrame, When registered, Then DataFrameReference returned with metadata."""
        # Arrange
        toolkit = DataFrameToolkit()
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

        # Act
        reference = toolkit.register_dataframe(
            "my_dataframe",
            df,
            description="Test DataFrame for unit tests",
            column_descriptions={"a": "First column", "b": "Second column"},
        )

        # Assert
        with check:
            assert isinstance(reference, DataFrameReference)
        with check:
            assert reference.name == "my_dataframe"
        with check:
            assert reference.description == "Test DataFrame for unit tests"
        with check:
            assert reference.num_rows == 3
        with check:
            assert reference.num_columns == 2
        with check:
            assert reference.column_names == ["a", "b"]

    def test_register_stores_in_context(self) -> None:
        """Given DataFrame, When registered, Then context has it."""
        # Arrange
        toolkit = DataFrameToolkit()
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

        # Act
        reference = toolkit.register_dataframe("stored_df", df)

        # Assert - use public API (references property)
        with check:
            assert reference in toolkit.references
        with check:
            assert any(ref.name == "stored_df" for ref in toolkit.references)

    def test_register_duplicate_name_error(self) -> None:
        """Given existing name, When registered, Then ValueError raised."""
        # Arrange
        toolkit = DataFrameToolkit()
        df1 = pl.DataFrame({"a": [1, 2, 3]})
        df2 = pl.DataFrame({"x": [10, 20, 30]})
        toolkit.register_dataframe("duplicate_name", df1)

        # Act/Assert
        with pytest.raises(ValueError, match="DataFrame 'duplicate_name' is already registered"):
            toolkit.register_dataframe("duplicate_name", df2)

    def test_register_name_matching_id_pattern_rejected(self) -> None:
        """Given name matching ID pattern, When registered, Then ValueError raised."""
        # Arrange
        toolkit = DataFrameToolkit()
        df = pl.DataFrame({"a": [1, 2, 3]})

        # Act/Assert
        with pytest.raises(ValueError, match="cannot match ID pattern"):
            toolkit.register_dataframe("df_1a2b3c4d", df)

    def test_register_name_similar_to_id_but_not_matching_allowed(self) -> None:
        """Given name similar to but not matching ID pattern, When registered, Then succeeds."""
        # Arrange
        toolkit = DataFrameToolkit()
        df = pl.DataFrame({"a": [1, 2, 3]})

        # Act - these should NOT match the pattern df_[0-9a-f]{8}
        ref1 = toolkit.register_dataframe("df_sales", df)  # Not 8 hex chars
        ref2 = toolkit.register_dataframe("df_12345678901", pl.DataFrame({"b": [1]}))  # Too long
        ref3 = toolkit.register_dataframe("dataframe_1a2b3c4d", pl.DataFrame({"c": [1]}))  # Wrong prefix

        # Assert
        with check:
            assert ref1.name == "df_sales"
        with check:
            assert ref2.name == "df_12345678901"
        with check:
            assert ref3.name == "dataframe_1a2b3c4d"


class TestRegisterDataFrames:
    """Tests for DataFrameToolkit.register_dataframes method."""

    def test_register_dataframes_success(self) -> None:
        """Given multiple DataFrames, When registered, Then all references created."""
        # Arrange
        toolkit = DataFrameToolkit()
        dfs = {
            "df1": pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}),
            "df2": pl.DataFrame({"x": ["foo", "bar"], "y": [1.0, 2.0]}),
        }

        # Act
        references = toolkit.register_dataframes(dfs)

        # Assert - use public API (references property) instead of _references
        registered_names = {ref.name for ref in toolkit.references}
        with check:
            assert len(references) == 2
        with check:
            assert "df1" in registered_names
        with check:
            assert "df2" in registered_names

    def test_register_dataframes_returns_all_refs(self) -> None:
        """Given multiple DataFrames, When registered, Then returns list of references."""
        # Arrange
        toolkit = DataFrameToolkit()
        dfs = {
            "users": pl.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]}),
            "orders": pl.DataFrame({"order_id": [100], "user_id": [1]}),
        }
        descriptions = {"users": "User accounts", "orders": "User orders"}

        # Act
        references = toolkit.register_dataframes(dfs, descriptions=descriptions)

        # Assert
        with check:
            assert isinstance(references, list)
        with check:
            assert all(isinstance(ref, DataFrameReference) for ref in references)
        with check:
            assert len(references) == 2

        # Verify each reference has correct metadata
        ref_by_name = {ref.name: ref for ref in references}
        with check:
            assert ref_by_name["users"].description == "User accounts"
        with check:
            assert ref_by_name["orders"].description == "User orders"

    def test_register_dataframes_existing_name_error(self) -> None:
        """Given name already in toolkit, When registered, Then ValueError before any registration."""
        # Arrange
        toolkit = DataFrameToolkit()
        existing_df = pl.DataFrame({"id": [1, 2, 3]})
        toolkit.register_dataframe("existing", existing_df)

        # Attempt to register batch with conflicting name
        new_dfs = {
            "existing": pl.DataFrame({"x": [10, 20]}),
            "brand_new": pl.DataFrame({"y": [30, 40]}),
        }

        # Act/Assert - should fail before registering any
        with pytest.raises(ValueError, match="DataFrame 'existing' is already registered"):
            toolkit.register_dataframes(new_dfs)

        # Verify atomicity: neither DataFrame should be registered
        registered_names = {ref.name for ref in toolkit.references}
        with check:
            assert "brand_new" not in registered_names
        with check:
            assert len(toolkit.references) == 1  # Only the original

    def test_register_dataframes_name_matching_id_pattern_rejected(self) -> None:
        """Given name matching ID pattern in batch, When registered, Then ValueError before any registration."""
        # Arrange
        toolkit = DataFrameToolkit()
        dfs = {
            "valid_name": pl.DataFrame({"a": [1, 2]}),
            "df_abcd1234": pl.DataFrame({"b": [3, 4]}),  # Matches ID pattern
        }

        # Act/Assert
        with pytest.raises(ValueError, match="cannot match ID pattern"):
            toolkit.register_dataframes(dfs)

        # Verify atomicity: no DataFrames registered
        with check:
            assert len(toolkit.references) == 0


class TestUnregisterDataFrame:
    """Tests for DataFrameToolkit.unregister_dataframe method."""

    def test_unregister_success(self) -> None:
        """Given registered name, When unregistered, Then removed."""
        # Arrange
        toolkit = DataFrameToolkit()
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        toolkit.register_dataframe("to_remove", df)

        # Act
        toolkit.unregister_dataframe("to_remove")

        # Assert - use public API (references property)
        registered_names = {ref.name for ref in toolkit.references}
        with check:
            assert "to_remove" not in registered_names
        with check:
            assert len(toolkit.references) == 0

    def test_unregister_not_found_error(self) -> None:
        """Given unknown name, When unregistered, Then KeyError raised."""
        # Arrange
        toolkit = DataFrameToolkit()

        # Act/Assert
        with pytest.raises(KeyError, match="DataFrame 'nonexistent' is not registered"):
            toolkit.unregister_dataframe("nonexistent")


class TestGetDataFrameId:
    """Tests for DataFrameToolkit.get_dataframe_id method."""

    def test_get_id_success(self) -> None:
        """Given registered name, When called, Then returns DataFrameId."""
        # Arrange
        toolkit = DataFrameToolkit()
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        reference = toolkit.register_dataframe("my_data", df)

        # Act
        result = toolkit.get_dataframe_id("my_data")

        # Assert
        with check:
            assert isinstance(result, str)
        with check:
            assert result.startswith("df_")
        with check:
            assert result == reference.id

    def test_get_id_not_found(self) -> None:
        """Given unknown name, When called, Then returns ToolCallError."""
        # Arrange
        toolkit = DataFrameToolkit()

        # Act
        result = toolkit.get_dataframe_id("nonexistent")

        # Assert
        with check:
            assert isinstance(result, ToolCallError)
        with check:
            assert result.error_type == "DataFrameNotFound"
        with check:
            assert "nonexistent" in result.message

    def test_get_id_error_has_available_names(self) -> None:
        """Given unknown name with other DataFrames registered, When called, Then error has available names."""
        # Arrange
        toolkit = DataFrameToolkit()
        toolkit.register_dataframe("users", pl.DataFrame({"id": [1, 2]}))
        toolkit.register_dataframe("orders", pl.DataFrame({"id": [10, 20]}))

        # Act
        result = toolkit.get_dataframe_id("unknown_table")

        # Assert
        with check:
            assert isinstance(result, ToolCallError)
        with check:
            assert "available_names" in result.details
        available_names = result.details["available_names"]
        assert isinstance(available_names, list)
        with check:
            assert set(available_names) == {"users", "orders"}

    def test_get_id_with_id_input_returns_invalid_argument_error(self) -> None:
        """Given ID instead of name, When called, Then returns InvalidArgument error with guidance."""
        # Arrange
        toolkit = DataFrameToolkit()
        toolkit.register_dataframe("sales", pl.DataFrame({"amount": [100, 200]}))

        # Act
        result = toolkit.get_dataframe_id("df_1a2b3c4d")  # This is an ID, not a name

        # Assert
        with check:
            assert isinstance(result, ToolCallError)
        with check:
            assert result.error_type == "InvalidArgument"
        with check:
            assert "already an ID" in result.message
        with check:
            assert "Use the name" in result.message
        with check:
            assert "available_names" in result.details

    def test_get_id_with_actual_registered_id_returns_invalid_argument_error(self) -> None:
        """Given actual registered ID, When called, Then returns InvalidArgument error (not the ID)."""
        # Arrange
        toolkit = DataFrameToolkit()
        ref = toolkit.register_dataframe("sales", pl.DataFrame({"amount": [100, 200]}))
        actual_id = ref.id  # e.g., "df_a1b2c3d4"

        # Act
        result = toolkit.get_dataframe_id(actual_id)

        # Assert - should return error, not the ID itself
        with check:
            assert isinstance(result, ToolCallError)
        with check:
            assert result.error_type == "InvalidArgument"
        with check:
            assert "already an ID" in result.message


class TestGetDataFrameReference:
    """Tests for DataFrameToolkit.get_dataframe_reference method."""

    def test_get_reference_by_name_returns_dataframe_reference(self) -> None:
        """Given registered name, When called, Then returns DataFrameReference."""
        # Arrange
        toolkit = DataFrameToolkit()
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        expected_reference = toolkit.register_dataframe(
            "my_data",
            df,
            description="Test data",
        )

        # Act
        result = toolkit.get_dataframe_reference("my_data")

        # Assert
        with check:
            assert isinstance(result, DataFrameReference)
        with check:
            assert result == expected_reference
        with check:
            assert result.name == "my_data"
        with check:
            assert result.description == "Test data"

    def test_get_reference_by_id_returns_dataframe_reference(self) -> None:
        """Given registered ID, When called, Then returns DataFrameReference."""
        # Arrange
        toolkit = DataFrameToolkit()
        df = pl.DataFrame({"x": [10, 20], "y": ["foo", "bar"]})
        expected_reference = toolkit.register_dataframe("lookup_by_id", df)
        dataframe_id = expected_reference.id

        # Act
        result = toolkit.get_dataframe_reference(dataframe_id)

        # Assert
        with check:
            assert isinstance(result, DataFrameReference)
        with check:
            assert result == expected_reference
        with check:
            assert result.id == dataframe_id
        with check:
            assert result.name == "lookup_by_id"

    def test_get_reference_not_found_returns_tool_call_error(self) -> None:
        """Given unknown identifier, When called, Then returns ToolCallError."""
        # Arrange
        toolkit = DataFrameToolkit()

        # Act
        result = toolkit.get_dataframe_reference("nonexistent")

        # Assert
        with check:
            assert isinstance(result, ToolCallError)
        with check:
            assert result.error_type == "DataFrameNotFound"
        with check:
            assert "nonexistent" in result.message
        with check:
            assert "not found by name or ID" in result.message

    def test_get_reference_error_has_both_names_and_ids(self) -> None:
        """Given unknown identifier with registered DataFrames, When called, Then error has available names AND IDs."""
        # Arrange
        toolkit = DataFrameToolkit()
        ref_users = toolkit.register_dataframe("users", pl.DataFrame({"id": [1, 2]}))
        ref_orders = toolkit.register_dataframe("orders", pl.DataFrame({"id": [10, 20]}))

        # Act
        result = toolkit.get_dataframe_reference("unknown_table")

        # Assert
        with check:
            assert isinstance(result, ToolCallError)
        with check:
            assert "available_names" in result.details
        with check:
            assert "available_ids" in result.details

        # Verify available_names contains expected values
        available_names = result.details["available_names"]
        assert isinstance(available_names, list)
        with check:
            assert set(available_names) == {"users", "orders"}

        # Verify available_ids contains expected values
        available_ids = result.details["available_ids"]
        assert isinstance(available_ids, list)
        with check:
            assert set(available_ids) == {ref_users.id, ref_orders.id}

    def test_get_reference_tool_invoke_returns_dataframe_reference(self) -> None:
        """Given toolkit with registered DataFrame, When tool invoked, Then returns DataFrameReference."""
        # Arrange
        toolkit = DataFrameToolkit()
        expected_reference = toolkit.register_dataframe(
            "sales",
            pl.DataFrame({"amount": [100, 200, 300]}),
        )

        # Act
        tools = toolkit.get_core_tools()
        tool_get_reference = next(t for t in tools if t.name == "get_dataframe_reference")
        result = tool_get_reference.invoke({"identifier": "sales"})

        # Assert
        with check:
            assert isinstance(result, DataFrameReference)
        with check:
            assert result == expected_reference
        with check:
            assert result.name == "sales"


class TestExportState:
    """Tests for DataFrameToolkit.export_state method."""

    def test_export_state_empty_toolkit(self) -> None:
        """Given empty toolkit, When exported, Then state has empty references."""
        # Arrange
        toolkit = DataFrameToolkit()

        # Act
        state = toolkit.export_state()

        # Assert
        with check:
            assert len(state.references) == 0

    def test_export_state_with_registered_dataframes(self) -> None:
        """Given toolkit with registered dataframes, When exported, Then all references included."""
        # Arrange
        toolkit = DataFrameToolkit()
        toolkit.register_dataframe("users", pl.DataFrame({"id": [1, 2]}))
        toolkit.register_dataframe("orders", pl.DataFrame({"order_id": [10, 20]}))

        # Act
        state = toolkit.export_state()

        # Assert
        with check:
            assert len(state.references) == 2
        names = {ref.name for ref in state.references}
        with check:
            assert names == {"users", "orders"}


class TestFromState:
    """Tests for DataFrameToolkit.from_state classmethod."""

    def test_from_state_by_name(self) -> None:
        """Given state and base dataframes by name, When from_state called, Then toolkit reconstructed."""
        # Arrange - create original toolkit and export state
        original = DataFrameToolkit()
        base_df = pl.DataFrame({"a": [1, 2, 3]})
        base_ref = original.register_dataframe("base", base_df)
        state = original.export_state()

        # Act - restore from state by name
        new_toolkit = DataFrameToolkit.from_state(state, {"base": base_df})

        # Assert
        with check:
            assert len(new_toolkit.references) == 1
        with check:
            assert new_toolkit.references[0].name == "base"
        with check:
            assert new_toolkit.references[0].id == base_ref.id

    def test_from_state_by_id(self) -> None:
        """Given state and base dataframes by ID, When from_state called, Then toolkit reconstructed."""
        # Arrange
        original = DataFrameToolkit()
        base_df = pl.DataFrame({"a": [1, 2, 3]})
        base_ref = original.register_dataframe("base", base_df)
        state = original.export_state()

        # Act - restore from state by ID
        new_toolkit = DataFrameToolkit.from_state(state, {base_ref.id: base_df})

        # Assert
        with check:
            assert len(new_toolkit.references) == 1
        with check:
            assert new_toolkit.references[0].id == base_ref.id

    def test_from_state_mixed_name_and_id(self) -> None:
        """Given state and base dataframes by mixed name/ID, When from_state called, Then toolkit reconstructed."""
        # Arrange
        original = DataFrameToolkit()
        df1 = pl.DataFrame({"a": [1, 2, 3]})
        df2 = pl.DataFrame({"b": [4, 5, 6]})
        ref1 = original.register_dataframe("first", df1)
        ref2 = original.register_dataframe("second", df2)
        state = original.export_state()

        # Act - restore with mixed keys
        new_toolkit = DataFrameToolkit.from_state(state, {"first": df1, ref2.id: df2})

        # Assert
        with check:
            assert len(new_toolkit.references) == 2
        ref_ids = {ref.id for ref in new_toolkit.references}
        with check:
            assert ref_ids == {ref1.id, ref2.id}

    def test_from_state_with_derivatives(self) -> None:
        """Given state with derivative, When from_state called, Then derivative reconstructed."""
        # Arrange - original toolkit with derivative
        original = DataFrameToolkit()
        base_df = pl.DataFrame({"a": [1, 2, 3]})
        base_ref = original.register_dataframe("base", base_df)

        # Create derivative reference with source_query
        derived_ref = DataFrameReference.from_dataframe(
            pl.DataFrame({"a": [1, 2]}),
            name="derived",
            source_query=f"SELECT * FROM {base_ref.id} WHERE a < 3",  # noqa: S608
            parent_ids=[base_ref.id],
        )
        state = DataFrameToolkitState(references=[base_ref, derived_ref])

        # Act
        new_toolkit = DataFrameToolkit.from_state(state, {"base": base_df})

        # Assert
        with check:
            assert len(new_toolkit.references) == 2
        names = {ref.name for ref in new_toolkit.references}
        with check:
            assert names == {"base", "derived"}

    def test_from_state_missing_base_raises_error(self) -> None:
        """Given state requiring base not provided, When from_state called, Then raises ValueError."""
        # Arrange
        original = DataFrameToolkit()
        df1 = pl.DataFrame({"a": [1, 2, 3]})
        df2 = pl.DataFrame({"b": [4, 5, 6]})
        original.register_dataframe("first", df1)
        original.register_dataframe("second", df2)
        state = original.export_state()

        # Act/Assert - only provide one of two required bases
        with pytest.raises(ValueError, match="Missing base dataframes"):
            DataFrameToolkit.from_state(state, {"first": df1})

    def test_from_state_unknown_name_raises_error(self) -> None:
        """Given name not in state, When from_state called, Then raises ValueError."""
        # Arrange
        original = DataFrameToolkit()
        base_df = pl.DataFrame({"a": [1, 2, 3]})
        original.register_dataframe("base", base_df)
        state = original.export_state()

        # Act/Assert
        with pytest.raises(ValueError, match="Name 'wrong_name' not found"):
            DataFrameToolkit.from_state(state, {"wrong_name": base_df})

    def test_from_state_unknown_id_raises_error(self) -> None:
        """Given ID not in state, When from_state called, Then raises ValueError."""
        # Arrange
        original = DataFrameToolkit()
        base_df = pl.DataFrame({"a": [1, 2, 3]})
        original.register_dataframe("base", base_df)
        state = original.export_state()

        # Act/Assert
        with pytest.raises(ValueError, match="ID 'df_00000000' not found"):
            DataFrameToolkit.from_state(state, {"df_00000000": base_df})

    def test_from_state_preserves_metadata(self) -> None:
        """Given state with metadata, When from_state called, Then metadata preserved."""
        # Arrange
        original = DataFrameToolkit()
        base_df = pl.DataFrame({"a": [1, 2, 3]})
        original.register_dataframe(
            "base",
            base_df,
            description="Test description",
            column_descriptions={"a": "Column A"},
        )
        state = original.export_state()

        # Act
        new_toolkit = DataFrameToolkit.from_state(state, {"base": base_df})

        # Assert
        restored_ref = new_toolkit.references[0]
        with check:
            assert restored_ref.description == "Test description"
        with check:
            assert restored_ref.column_summaries["a"].description == "Column A"


class TestFromStateErrorHandling:
    """Tests for error handling in DataFrameToolkit.from_state."""

    def test_from_state_column_name_mismatch_raises_error(self) -> None:
        """Given DataFrame with different columns, When from_state called, Then raises ValueError."""
        # Arrange
        original = DataFrameToolkit()
        original_df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        original.register_dataframe("data", original_df)
        state = original.export_state()

        # Different column names
        different_df = pl.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})

        # Act/Assert
        with pytest.raises(ValueError, match=r"column mismatch.*Expected.*a.*b.*got.*x.*y"):
            DataFrameToolkit.from_state(state, {"data": different_df})

    def test_from_state_row_count_mismatch_raises_error(self) -> None:
        """Given DataFrame with different row count, When from_state called, Then raises ValueError."""
        # Arrange
        original = DataFrameToolkit()
        original_df = pl.DataFrame({"a": [1, 2, 3]})
        original.register_dataframe("data", original_df)
        state = original.export_state()

        # Different row count
        different_df = pl.DataFrame({"a": [1, 2, 3, 4, 5]})

        # Act/Assert
        with pytest.raises(ValueError, match=r"shape mismatch.*Expected.*3.*got.*5"):
            DataFrameToolkit.from_state(state, {"data": different_df})

    def test_from_state_column_count_mismatch_raises_error(self) -> None:
        """Given DataFrame with different column count, When from_state called, Then raises ValueError."""
        # Arrange
        original = DataFrameToolkit()
        original_df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        original.register_dataframe("data", original_df)
        state = original.export_state()

        # Different column count (fewer columns)
        different_df = pl.DataFrame({"a": [1, 2, 3]})

        # Act/Assert - shape is checked first, so fails on shape mismatch
        with pytest.raises(ValueError, match="shape mismatch"):
            DataFrameToolkit.from_state(state, {"data": different_df})

    def test_from_state_sql_error_clear_message(self) -> None:
        """Given invalid SQL in source_query, When from_state called, Then clear error message."""
        # Arrange - create state with a derivative that has invalid SQL
        base_df = pl.DataFrame({"a": [1, 2, 3]})
        base_ref = DataFrameReference.from_dataframe(base_df, name="base")

        derived_ref = DataFrameReference.from_dataframe(
            pl.DataFrame({"a": [1]}),
            name="derived",
            source_query="SELECT * FROM nonexistent_table",  # Invalid SQL
            parent_ids=[base_ref.id],
        )

        state = DataFrameToolkitState(references=[base_ref, derived_ref])

        # Act/Assert
        with pytest.raises(ValueError, match=r"SQL execution failed.*derived"):
            DataFrameToolkit.from_state(state, {"base": base_df})

    def test_from_state_data_values_changed_raises_error(self) -> None:
        """Given DataFrame with different data values, When from_state called, Then raises ValueError."""
        # Arrange
        original = DataFrameToolkit()
        original_df = pl.DataFrame({"a": [1, 2, 3]})
        original.register_dataframe("data", original_df)
        state = original.export_state()

        # Same shape and columns, but different values
        different_df = pl.DataFrame({"a": [100, 200, 300]})

        # Act/Assert - should fail on column summary mismatch (min, max, mean differ)
        with pytest.raises(ValueError, match=r"statistics mismatch.*Differences"):
            DataFrameToolkit.from_state(state, {"data": different_df})

    def test_from_state_dtype_changed_raises_error(self) -> None:
        """Given DataFrame with different dtype, When from_state called, Then raises ValueError."""
        # Arrange
        original = DataFrameToolkit()
        original_df = pl.DataFrame({"a": [1, 2, 3]})  # Int64
        original.register_dataframe("data", original_df)
        state = original.export_state()

        # Same values but different dtype
        different_df = pl.DataFrame({"a": [1.0, 2.0, 3.0]})  # Float64

        # Act/Assert
        with pytest.raises(ValueError, match=r"statistics mismatch.*dtype"):
            DataFrameToolkit.from_state(state, {"data": different_df})

    def test_from_state_null_count_changed_raises_error(self) -> None:
        """Given DataFrame with different null count, When from_state called, Then raises ValueError."""
        # Arrange
        original = DataFrameToolkit()
        original_df = pl.DataFrame({"a": [1, None, 3]})
        original.register_dataframe("data", original_df)
        state = original.export_state()

        # Same shape but different null count
        different_df = pl.DataFrame({"a": [1, 2, 3]})  # No nulls

        # Act/Assert
        with pytest.raises(ValueError, match=r"statistics mismatch.*null_count"):
            DataFrameToolkit.from_state(state, {"data": different_df})

    def test_from_state_identical_data_passes(self) -> None:
        """Given identical DataFrame data, When from_state called, Then validation passes."""
        # Arrange
        original = DataFrameToolkit()
        original_df = pl.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
        original.register_dataframe("data", original_df)
        state = original.export_state()

        # Exact same data
        same_df = pl.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})

        # Act
        new_toolkit = DataFrameToolkit.from_state(state, {"data": same_df})

        # Assert - should succeed without error
        with check:
            assert len(new_toolkit.references) == 1


class TestGetTools:
    """Tests for DataFrameToolkit.get_tools and get_core_tools methods."""

    def test_get_tools_returns_list(self) -> None:
        """Given toolkit, When get_tools called, Then returns list of StructuredTool."""
        # Arrange
        toolkit = DataFrameToolkit()
        toolkit.register_dataframe("test", pl.DataFrame({"a": [1, 2, 3]}))

        # Act
        tools = toolkit.get_tools()

        # Assert
        with check:
            assert isinstance(tools, list)
        with check:
            assert len(tools) >= 1

    def test_get_core_tools_returns_list(self) -> None:
        """Given toolkit, When get_core_tools called, Then returns list of StructuredTool."""
        # Arrange
        toolkit = DataFrameToolkit()
        toolkit.register_dataframe("test", pl.DataFrame({"a": [1, 2, 3]}))

        # Act
        tools = toolkit.get_core_tools()

        # Assert
        with check:
            assert isinstance(tools, list)
        with check:
            assert len(tools) >= 1

    def test_get_tools_contains_core_tools(self) -> None:
        """Given toolkit, When get_tools called, Then contains all core tools."""
        # Arrange
        toolkit = DataFrameToolkit()
        toolkit.register_dataframe("test", pl.DataFrame({"a": [1, 2, 3]}))

        # Act
        all_tools = toolkit.get_tools()
        core_tools = toolkit.get_core_tools()

        # Assert - all core tools should be in get_tools()
        all_tool_names = {t.name for t in all_tools}
        core_tool_names = {t.name for t in core_tools}
        with check:
            assert core_tool_names.issubset(all_tool_names)

    def test_tool_schema_excludes_self(self) -> None:
        """Given toolkit, When tool created, Then schema does not include 'self' parameter."""
        # Arrange
        toolkit = DataFrameToolkit()
        toolkit.register_dataframe("test", pl.DataFrame({"a": [1, 2, 3]}))

        # Act
        tools = toolkit.get_core_tools()
        tool_get_dataframe_id = next(t for t in tools if t.name == "get_dataframe_id")
        tool_schema = tool_get_dataframe_id.args_schema.model_json_schema()

        # Assert - 'self' should not be in the properties
        with check:
            assert "self" not in tool_schema.get("properties", {})
        with check:
            assert "name" in tool_schema.get("properties", {})

    def test_tool_invoke_works(self) -> None:
        """Given toolkit with registered DataFrame, When get_dataframe_id tool invoked, Then returns correct ID."""
        # Arrange
        toolkit = DataFrameToolkit()
        reference = toolkit.register_dataframe("sales", pl.DataFrame({"a": [1, 2, 3]}))

        # Act
        tools = toolkit.get_core_tools()
        tool_get_dataframe_id = next(t for t in tools if t.name == "get_dataframe_id")
        result = tool_get_dataframe_id.invoke({"name": "sales"})

        # Assert
        with check:
            assert result == reference.id


class TestConversationResumptionScenarios:
    """End-to-end tests for conversation resumption workflow using from_state."""

    def test_conversation_resumption_scenario(self) -> None:
        """Full workflow: create toolkit, execute SQL, export, reconstruct with from_state."""
        # === Session 1: Original conversation ===
        original_toolkit = DataFrameToolkit()

        # Register base dataframe
        base_df = pl.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "score": [85, 92, 78, 95, 88],
        })
        base_ref = original_toolkit.register_dataframe("students", base_df)

        # Execute SQL to create derivative (simulating agent tool call)
        query = f"SELECT id, name, score FROM {base_ref.id} WHERE score >= 85"  # noqa: S608
        result = original_toolkit._context.execute_sql(query, eager=True)
        result_df = result if isinstance(result, pl.DataFrame) else result.collect()

        # Register derivative with source_query
        derived_ref = DataFrameReference.from_dataframe(
            result_df,
            name="high_scorers",
            description="Students with score >= 85",
            source_query=query,
            parent_ids=[base_ref.id],
        )
        original_toolkit._context.register(derived_ref.id, result_df)
        original_toolkit._references[derived_ref.id] = derived_ref

        # Export state (would be persisted to conversation thread)
        state = original_toolkit.export_state()
        state_json = state.model_dump_json()

        # === Session 2: Resume conversation using from_state ===
        restored_state = DataFrameToolkitState.model_validate_json(state_json)
        new_toolkit = DataFrameToolkit.from_state(restored_state, {"students": base_df})

        # === Verify reconstruction ===
        with check:
            assert len(new_toolkit.references) == 2

        ref_names = {ref.name for ref in new_toolkit.references}
        with check:
            assert ref_names == {"students", "high_scorers"}

        # Verify reconstructed data matches
        reconstructed_df = new_toolkit._context.get_dataframe(derived_ref.id)
        with check:
            assert reconstructed_df.shape == (4, 3)  # 4 students with score >= 85
        with check:
            assert set(reconstructed_df["name"].to_list()) == {"Alice", "Bob", "Diana", "Eve"}

    def test_multi_level_derivation_reconstruction(self) -> None:
        """Test A -> B -> C chain reconstruction using from_state."""
        # Setup base data
        original_toolkit = DataFrameToolkit()
        a_df = pl.DataFrame({
            "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "y": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"],
        })
        a_ref = original_toolkit.register_dataframe("A", a_df)

        # Create B from A
        b_query = f"SELECT x, y FROM {a_ref.id} WHERE x <= 5"  # noqa: S608
        b_result = original_toolkit._context.execute_sql(b_query, eager=True)
        b_df = b_result if isinstance(b_result, pl.DataFrame) else b_result.collect()
        b_ref = DataFrameReference.from_dataframe(b_df, name="B", source_query=b_query, parent_ids=[a_ref.id])
        original_toolkit._context.register(b_ref.id, b_df)
        original_toolkit._references[b_ref.id] = b_ref

        # Create C from B
        c_query = f"SELECT x, y FROM {b_ref.id} WHERE x <= 2"  # noqa: S608
        c_result = original_toolkit._context.execute_sql(c_query, eager=True)
        c_df = c_result if isinstance(c_result, pl.DataFrame) else c_result.collect()
        c_ref = DataFrameReference.from_dataframe(c_df, name="C", source_query=c_query, parent_ids=[b_ref.id])
        original_toolkit._context.register(c_ref.id, c_df)
        original_toolkit._references[c_ref.id] = c_ref

        # Export and restore using from_state
        state = original_toolkit.export_state()
        new_toolkit = DataFrameToolkit.from_state(state, {"A": a_df})

        # Verify
        with check:
            assert len(new_toolkit.references) == 3

        ref_names = {ref.name for ref in new_toolkit.references}
        with check:
            assert ref_names == {"A", "B", "C"}

        # Verify data
        c_reconstructed = new_toolkit._context.get_dataframe(c_ref.id)
        with check:
            assert c_reconstructed.shape == (2, 2)
        with check:
            assert set(c_reconstructed["x"].to_list()) == {1, 2}

    def test_join_reconstruction(self) -> None:
        """Test reconstruction of derivatives from JOINs using from_state."""
        # Setup two base tables
        original_toolkit = DataFrameToolkit()

        users_df = pl.DataFrame({
            "user_id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
        })
        users_ref = original_toolkit.register_dataframe("users", users_df)

        orders_df = pl.DataFrame({
            "order_id": [101, 102, 103, 104],
            "user_id": [1, 1, 2, 3],
            "amount": [50, 75, 100, 25],
        })
        orders_ref = original_toolkit.register_dataframe("orders", orders_df)

        # Create derived table from JOIN
        join_query = f"""
            SELECT u.name, o.order_id, o.amount
            FROM {users_ref.id} u
            JOIN {orders_ref.id} o ON u.user_id = o.user_id
        """  # noqa: S608
        join_result = original_toolkit._context.execute_sql(join_query, eager=True)
        joined_df = join_result if isinstance(join_result, pl.DataFrame) else join_result.collect()
        joined_ref = DataFrameReference.from_dataframe(
            joined_df,
            name="user_orders",
            source_query=join_query,
            parent_ids=[users_ref.id, orders_ref.id],
        )
        original_toolkit._context.register(joined_ref.id, joined_df)
        original_toolkit._references[joined_ref.id] = joined_ref

        # Export and restore using from_state
        state = original_toolkit.export_state()
        new_toolkit = DataFrameToolkit.from_state(
            state,
            {"users": users_df, "orders": orders_df},
        )

        # Verify
        with check:
            assert len(new_toolkit.references) == 3

        ref_names = {ref.name for ref in new_toolkit.references}
        with check:
            assert ref_names == {"users", "orders", "user_orders"}

        # Verify data
        reconstructed_df = new_toolkit._context.get_dataframe(joined_ref.id)
        with check:
            assert reconstructed_df.shape == (4, 3)
        with check:
            assert "Alice" in reconstructed_df["name"].to_list()
        with check:
            assert reconstructed_df["name"].to_list().count("Alice") == 2  # Alice has 2 orders

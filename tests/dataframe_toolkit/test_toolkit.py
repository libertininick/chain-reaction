"""Tests for the DataFrameToolkit class and ToolCallError model."""

from __future__ import annotations

import polars as pl
import pytest
from pydantic import ValidationError
from pytest_check import check

from chain_reaction.dataframe_toolkit.models import DataFrameReference, ToolCallError
from chain_reaction.dataframe_toolkit.toolkit import DataFrameToolkit

# ruff: noqa: PLR6301


class TestToolCallError:
    """Tests for the ToolCallError model."""

    def test_tool_call_error_all_fields(self) -> None:
        """Given all fields, When instantiated, Then model is valid."""
        error = ToolCallError(
            error_type="DataFrameNotFound",
            message="DataFrame 'sales' is not registered",
            details={"available_names": ["orders", "customers"]},
        )

        with check:
            assert error.error_type == "DataFrameNotFound"
        with check:
            assert error.message == "DataFrame 'sales' is not registered"
        with check:
            assert error.details == {"available_names": ["orders", "customers"]}

    def test_tool_call_error_minimal(self) -> None:
        """Given only required fields, When instantiated, Then details is empty dict."""
        error = ToolCallError(
            error_type="SQLSyntaxError",
            message="Invalid SQL syntax near 'SELEC'",
        )

        with check:
            assert error.error_type == "SQLSyntaxError"
        with check:
            assert error.message == "Invalid SQL syntax near 'SELEC'"
        with check:
            assert error.details == {}

    def test_tool_call_error_serialization(self) -> None:
        """Given model instance, When converted to dict, Then all fields present."""
        error = ToolCallError(
            error_type="SQLTableError",
            message="Table 'unknown_table' does not exist",
            details={"invalid_tables": ["unknown_table"], "available_tables": ["df_abc123"]},
        )

        error_dict = error.model_dump()

        with check:
            assert "error_type" in error_dict
        with check:
            assert "message" in error_dict
        with check:
            assert "details" in error_dict
        with check:
            assert error_dict["error_type"] == "SQLTableError"
        with check:
            assert error_dict["message"] == "Table 'unknown_table' does not exist"
        with check:
            assert error_dict["details"]["invalid_tables"] == ["unknown_table"]

    def test_tool_call_error_serialization_minimal(self) -> None:
        """Given minimal model instance, When converted to dict, Then details is empty dict."""
        error = ToolCallError(
            error_type="ExecutionError",
            message="Query execution failed",
        )

        error_dict = error.model_dump()

        with check:
            assert error_dict["details"] == {}

    def test_tool_call_error_required_fields(self) -> None:
        """Given missing required fields, When instantiated, Then raises ValidationError."""
        with pytest.raises(ValidationError):
            ToolCallError(error_type="SomeError")  # type: ignore[call-arg]

        with pytest.raises(ValidationError):
            ToolCallError(message="Some message")  # type: ignore[call-arg]

    def test_tool_call_error_has_field_descriptions(self) -> None:
        """Given ToolCallError model, When schema inspected, Then fields have descriptions."""
        schema = ToolCallError.model_json_schema()
        properties = schema["properties"]

        with check:
            assert "description" in properties["error_type"]
        with check:
            assert "description" in properties["message"]
        with check:
            assert "description" in properties["details"]

    def test_tool_call_error_json_serialization(self) -> None:
        """Given ToolCallError with nested details, When serialized to JSON, Then valid JSON string."""
        error = ToolCallError(
            error_type="SQLColumnError",
            message="Invalid columns in query",
            details={
                "invalid_columns": ["unknown_col"],
                "table_columns": {"df_abc123": ["id", "name", "value"]},
                "count": 1,
                "is_recoverable": True,
            },
        )

        json_str = error.model_dump_json()

        with check:
            assert isinstance(json_str, str)
        with check:
            assert "SQLColumnError" in json_str
        with check:
            assert "invalid_columns" in json_str
        with check:
            assert "unknown_col" in json_str


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

"""Tests for the dataframe_toolkit models."""

from __future__ import annotations

import json
import re

import polars as pl
import pytest
from pydantic import ValidationError
from pytest_check import check

from chain_reaction.dataframe_toolkit.models import (
    DataFrameReference,
    DataFrameToolkitState,
    ToolCallError,
)

# ruff: noqa: PLR6301, PLR0904


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


class TestDataFrameReference:
    """Tests for the DataFrameReference model."""

    # -------------------------------------------------------------------------
    # from_dataframe factory method tests
    # -------------------------------------------------------------------------

    def test_from_dataframe_minimal_arguments_creates_valid_reference(self) -> None:
        """Given DataFrame and name only, When from_dataframe called, Then creates reference with defaults."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})

        # Act
        ref = DataFrameReference.from_dataframe(df, name="test_df")

        # Assert
        with check:
            assert ref.name == "test_df"
        with check:
            assert not ref.description
        with check:
            assert ref.num_rows == 3
        with check:
            assert ref.num_columns == 2
        with check:
            assert ref.column_names == ["a", "b"]
        with check:
            assert ref.parent_ids == []
        with check:
            assert ref.source_query is None

    def test_from_dataframe_all_arguments_creates_reference_with_all_values(self) -> None:
        """Given all arguments, When from_dataframe called, Then creates reference with all values."""
        # Arrange
        df = pl.DataFrame({"col1": [10, 20], "col2": [1.5, 2.5]})
        parent_ids = ["df_00000001", "df_00000002"]

        # Act
        ref = DataFrameReference.from_dataframe(
            df,
            name="derived_df",
            description="A derived DataFrame",
            column_descriptions={"col1": "Integer column", "col2": "Float column"},
            parent_ids=parent_ids,
            source_query="SELECT col1, col2 FROM base",
        )

        # Assert
        with check:
            assert ref.name == "derived_df"
        with check:
            assert ref.description == "A derived DataFrame"
        with check:
            assert ref.parent_ids == parent_ids
        with check:
            assert ref.source_query == "SELECT col1, col2 FROM base"
        with check:
            assert ref.column_summaries["col1"].description == "Integer column"
        with check:
            assert ref.column_summaries["col2"].description == "Float column"

    def test_from_dataframe_generates_unique_id(self) -> None:
        """Given same DataFrame, When from_dataframe called twice, Then generates different ids."""
        # Arrange
        df = pl.DataFrame({"a": [1]})

        # Act
        ref1 = DataFrameReference.from_dataframe(df, name="test")
        ref2 = DataFrameReference.from_dataframe(df, name="test")

        # Assert
        with check:
            assert ref1.id != ref2.id
        with check:
            assert ref1.id.startswith("df_")
        with check:
            assert len(ref1.id) == 11  # "df_" + 8 hex chars

    def test_from_dataframe_empty_dataframe_raises_key_error(self) -> None:
        """Given empty DataFrame, When from_dataframe called, Then raises KeyError for min/max.

        Note: This tests the current limitation where ColumnSummary.from_series
        cannot handle empty columns because min/max values are not available.
        """
        # Arrange
        df = pl.DataFrame({"a": pl.Series([], dtype=pl.Int64), "b": pl.Series([], dtype=pl.Utf8)})

        # Act/Assert
        with pytest.raises(KeyError, match="min"):
            DataFrameReference.from_dataframe(df, name="empty_df")

    def test_from_dataframe_with_null_values_creates_valid_reference(self) -> None:
        """Given DataFrame with nulls, When from_dataframe called, Then creates reference with null counts."""
        # Arrange
        df = pl.DataFrame({"a": [1, None, 3], "b": [None, None, "z"]})

        # Act
        ref = DataFrameReference.from_dataframe(df, name="null_df")

        # Assert
        with check:
            assert ref.num_rows == 3
        with check:
            assert ref.column_summaries["a"].null_count == 1
        with check:
            assert ref.column_summaries["b"].null_count == 2

    def test_from_dataframe_single_column_single_row(self) -> None:
        """Given DataFrame with single column and row, When from_dataframe called, Then creates valid reference."""
        # Arrange
        df = pl.DataFrame({"only_col": [42]})

        # Act
        ref = DataFrameReference.from_dataframe(df, name="single")

        # Assert
        with check:
            assert ref.num_rows == 1
        with check:
            assert ref.num_columns == 1
        with check:
            assert ref.column_names == ["only_col"]

    def test_from_dataframe_partial_column_descriptions(self) -> None:
        """Given column descriptions for some columns only, When from_dataframe called, Then others empty."""
        # Arrange
        df = pl.DataFrame({"a": [1], "b": [2], "c": [3]})

        # Act
        ref = DataFrameReference.from_dataframe(
            df,
            name="partial_desc",
            column_descriptions={"a": "Column A description"},
        )

        # Assert
        with check:
            assert ref.column_summaries["a"].description == "Column A description"
        with check:
            assert not ref.column_summaries["b"].description
        with check:
            assert not ref.column_summaries["c"].description

    # -------------------------------------------------------------------------
    # Field tests
    # -------------------------------------------------------------------------

    def test_id_field_follows_dataframe_id_pattern(self) -> None:
        """Given DataFrameReference, When id accessed, Then follows df_<8 hex chars> pattern."""
        # Arrange
        df = pl.DataFrame({"a": [1]})

        # Act
        ref = DataFrameReference.from_dataframe(df, name="test")

        # Assert
        pattern = re.compile(r"^df_[0-9a-f]{8}$")
        with check:
            assert pattern.match(ref.id) is not None

    def test_name_field_preserves_value(self) -> None:
        """Given name with special characters, When from_dataframe called, Then name preserved exactly."""
        # Arrange
        df = pl.DataFrame({"a": [1]})
        name = "my-test_df.2024"

        # Act
        ref = DataFrameReference.from_dataframe(df, name=name)

        # Assert
        with check:
            assert ref.name == name

    def test_description_field_empty_string_when_none(self) -> None:
        """Given no description, When from_dataframe called, Then description is empty string."""
        # Arrange
        df = pl.DataFrame({"a": [1]})

        # Act
        ref = DataFrameReference.from_dataframe(df, name="test")

        # Assert
        with check:
            assert not ref.description

    def test_description_field_preserves_value(self) -> None:
        """Given description, When from_dataframe called, Then description preserved."""
        # Arrange
        df = pl.DataFrame({"a": [1]})
        desc = "This DataFrame contains sales data for Q4 2024."

        # Act
        ref = DataFrameReference.from_dataframe(df, name="test", description=desc)

        # Assert
        with check:
            assert ref.description == desc

    def test_num_rows_matches_dataframe_height(self) -> None:
        """Given DataFrame with specific height, When from_dataframe called, Then num_rows matches."""
        # Arrange
        df = pl.DataFrame({"a": list(range(100))})

        # Act
        ref = DataFrameReference.from_dataframe(df, name="test")

        # Assert
        with check:
            assert ref.num_rows == 100

    def test_num_columns_matches_dataframe_width(self) -> None:
        """Given DataFrame with specific width, When from_dataframe called, Then num_columns matches."""
        # Arrange
        df = pl.DataFrame({f"col_{i}": [1] for i in range(5)})

        # Act
        ref = DataFrameReference.from_dataframe(df, name="test")

        # Assert
        with check:
            assert ref.num_columns == 5

    def test_column_names_matches_dataframe_columns(self) -> None:
        """Given DataFrame with columns, When from_dataframe called, Then column_names matches order."""
        # Arrange
        df = pl.DataFrame({"z": [1], "a": [2], "m": [3]})

        # Act
        ref = DataFrameReference.from_dataframe(df, name="test")

        # Assert
        with check:
            assert ref.column_names == ["z", "a", "m"]

    def test_column_summaries_contains_all_columns(self) -> None:
        """Given DataFrame with multiple columns, When from_dataframe called, Then column_summaries has all."""
        # Arrange
        df = pl.DataFrame({"int_col": [1, 2, 3], "str_col": ["a", "b", "c"], "float_col": [1.1, 2.2, 3.3]})

        # Act
        ref = DataFrameReference.from_dataframe(df, name="test")

        # Assert
        with check:
            assert set(ref.column_summaries.keys()) == {"int_col", "str_col", "float_col"}

    def test_parent_ids_default_empty_list(self) -> None:
        """Given no parent_ids, When from_dataframe called, Then parent_ids is empty list."""
        # Arrange
        df = pl.DataFrame({"a": [1]})

        # Act
        ref = DataFrameReference.from_dataframe(df, name="test")

        # Assert
        with check:
            assert ref.parent_ids == []

    def test_parent_ids_preserves_values(self) -> None:
        """Given parent_ids, When from_dataframe called, Then parent_ids preserved."""
        # Arrange
        df = pl.DataFrame({"a": [1]})
        parent_ids = ["df_11111111", "df_22222222", "df_33333333"]

        # Act
        ref = DataFrameReference.from_dataframe(df, name="test", parent_ids=parent_ids)

        # Assert
        with check:
            assert ref.parent_ids == parent_ids

    # -------------------------------------------------------------------------
    # source_query field tests (existing tests)
    # -------------------------------------------------------------------------

    def test_source_query_default_none(self) -> None:
        """Given DataFrameReference without source_query, When checked, Then source_query is None."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})

        # Act
        ref = DataFrameReference.from_dataframe(df, name="test")

        # Assert
        with check:
            assert ref.source_query is None

    def test_source_query_with_value(self) -> None:
        """Given DataFrameReference with source_query, When checked, Then source_query contains SQL string."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})
        sql = "SELECT * FROM base_table WHERE value > 0"

        # Act
        ref = DataFrameReference.from_dataframe(df, name="derived", source_query=sql)

        # Assert
        with check:
            assert ref.source_query == sql

    def test_source_query_serialization(self) -> None:
        """Given DataFrameReference with source_query, When serialized, Then source_query is included."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})
        sql = "SELECT a FROM parent"

        # Act
        ref = DataFrameReference.from_dataframe(df, name="derived", source_query=sql)
        ref_dict = ref.model_dump()

        # Assert
        with check:
            assert "source_query" in ref_dict
        with check:
            assert ref_dict["source_query"] == sql

    def test_source_query_json_serialization(self) -> None:
        """Given DataFrameReference with source_query, When serialized to JSON, Then source_query is included."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})
        sql = "SELECT * FROM base"

        # Act
        ref = DataFrameReference.from_dataframe(df, name="derived", source_query=sql)
        json_str = ref.model_dump_json()

        # Assert
        with check:
            assert "source_query" in json_str
        with check:
            assert sql in json_str

    def test_source_query_none_serialization(self) -> None:
        """Given DataFrameReference without source_query, When serialized, Then source_query is None in dict."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})

        # Act
        ref = DataFrameReference.from_dataframe(df, name="base")
        ref_dict = ref.model_dump()

        # Assert
        with check:
            assert "source_query" in ref_dict
        with check:
            assert ref_dict["source_query"] is None

    # -------------------------------------------------------------------------
    # Serialization tests
    # -------------------------------------------------------------------------

    def test_model_dump_contains_all_fields(self) -> None:
        """Given DataFrameReference, When model_dump called, Then all fields present."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})
        ref = DataFrameReference.from_dataframe(df, name="test")

        # Act
        ref_dict = ref.model_dump()

        # Assert
        expected_fields = [
            "id",
            "name",
            "description",
            "num_rows",
            "num_columns",
            "column_names",
            "column_summaries",
            "parent_ids",
            "source_query",
        ]
        for field in expected_fields:
            with check:
                assert field in ref_dict, f"Field '{field}' missing from model_dump"

    def test_model_dump_json_produces_valid_json(self) -> None:
        """Given DataFrameReference, When model_dump_json called, Then produces valid JSON string."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        ref = DataFrameReference.from_dataframe(df, name="test", description="Test DataFrame")

        # Act
        json_str = ref.model_dump_json()

        # Assert
        with check:
            assert isinstance(json_str, str)
        # Should be parseable JSON
        parsed = json.loads(json_str)
        with check:
            assert parsed["name"] == "test"
        with check:
            assert parsed["description"] == "Test DataFrame"
        with check:
            assert parsed["num_rows"] == 3

    def test_model_dump_json_with_indent_produces_formatted_output(self) -> None:
        """Given DataFrameReference, When model_dump_json with indent, Then output is formatted."""
        # Arrange
        df = pl.DataFrame({"a": [1]})
        ref = DataFrameReference.from_dataframe(df, name="test")

        # Act
        compact = ref.model_dump_json()
        formatted = ref.model_dump_json(indent=2)

        # Assert
        with check:
            assert "\n" not in compact
        with check:
            assert "\n" in formatted

    def test_json_round_trip_preserves_all_fields(self) -> None:
        """Given DataFrameReference, When serialized and deserialized, Then all fields preserved."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3], "b": [1.1, 2.2, 3.3]})
        original = DataFrameReference.from_dataframe(
            df,
            name="test_df",
            description="A test DataFrame",
            parent_ids=["df_aaaaaaaa", "df_bbbbbbbb"],
            source_query="SELECT * FROM parent",
        )

        # Act
        json_str = original.model_dump_json()
        restored = DataFrameReference.model_validate_json(json_str)

        # Assert
        with check:
            assert restored.id == original.id
        with check:
            assert restored.name == original.name
        with check:
            assert restored.description == original.description
        with check:
            assert restored.num_rows == original.num_rows
        with check:
            assert restored.num_columns == original.num_columns
        with check:
            assert restored.column_names == original.column_names
        with check:
            assert restored.parent_ids == original.parent_ids
        with check:
            assert restored.source_query == original.source_query

    def test_model_dump_column_summaries_structure(self) -> None:
        """Given DataFrameReference, When model_dump called, Then column_summaries has correct structure."""
        # Arrange
        df = pl.DataFrame({"int_col": [1, 2, 3]})
        ref = DataFrameReference.from_dataframe(df, name="test", column_descriptions={"int_col": "Integer values"})

        # Act
        ref_dict = ref.model_dump()

        # Assert
        summary = ref_dict["column_summaries"]["int_col"]
        expected_summary_fields = [
            "description",
            "dtype",
            "count",
            "null_count",
            "unique_count",
            "min",
            "max",
            "mean",
            "std",
            "p25",
            "p50",
            "p75",
        ]
        for field in expected_summary_fields:
            with check:
                assert field in summary, f"ColumnSummary field '{field}' missing"
        with check:
            assert summary["description"] == "Integer values"

    # -------------------------------------------------------------------------
    # Schema and field descriptions tests
    # -------------------------------------------------------------------------

    def test_all_fields_have_descriptions_in_schema(self) -> None:
        """Given DataFrameReference model, When schema inspected, Then all fields have descriptions."""
        # Arrange/Act
        schema = DataFrameReference.model_json_schema()
        properties = schema["properties"]

        # Assert
        expected_fields = [
            "id",
            "name",
            "description",
            "num_rows",
            "num_columns",
            "column_names",
            "column_summaries",
            "parent_ids",
            "source_query",
        ]
        for field in expected_fields:
            with check:
                assert field in properties, f"Field '{field}' not in schema properties"
            with check:
                assert "description" in properties.get(field, {}), f"Field '{field}' does not have description"

    def test_source_query_has_description_in_schema(self) -> None:
        """Given DataFrameReference model, When schema inspected, Then source_query has description."""
        # Arrange/Act
        schema = DataFrameReference.model_json_schema()
        properties = schema["properties"]

        # Assert
        with check:
            assert "source_query" in properties
        with check:
            assert "description" in properties["source_query"]

    # -------------------------------------------------------------------------
    # Edge case tests
    # -------------------------------------------------------------------------

    def test_dataframe_with_special_column_names(self) -> None:
        """Given DataFrame with special column names, When from_dataframe called, Then names preserved."""
        # Arrange
        df = pl.DataFrame({"column with spaces": [1], "column-with-dashes": [2], "123_numeric_start": [3]})

        # Act
        ref = DataFrameReference.from_dataframe(df, name="special")

        # Assert
        with check:
            assert "column with spaces" in ref.column_names
        with check:
            assert "column-with-dashes" in ref.column_names
        with check:
            assert "123_numeric_start" in ref.column_names
        with check:
            assert "column with spaces" in ref.column_summaries
        with check:
            assert "column-with-dashes" in ref.column_summaries

    def test_dataframe_with_various_dtypes(self) -> None:
        """Given DataFrame with various dtypes, When from_dataframe called, Then column_summaries created."""
        # Arrange
        df = pl.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.1, 2.2, 3.3],
            "str_col": ["a", "b", "c"],
            "bool_col": [True, False, True],
        })

        # Act
        ref = DataFrameReference.from_dataframe(df, name="multi_dtype")

        # Assert
        with check:
            assert len(ref.column_summaries) == 4
        with check:
            assert "Int64" in ref.column_summaries["int_col"].dtype
        with check:
            assert "Float64" in ref.column_summaries["float_col"].dtype
        with check:
            assert "String" in ref.column_summaries["str_col"].dtype
        with check:
            assert "Boolean" in ref.column_summaries["bool_col"].dtype

    def test_dataframe_with_all_null_column_raises_key_error(self) -> None:
        """Given DataFrame with all-null column, When from_dataframe called, Then raises KeyError.

        Note: This tests the current limitation where ColumnSummary.from_series
        cannot handle all-null columns because min/max values are not available.
        """
        # Arrange
        df = pl.DataFrame({"all_null": [None, None, None], "has_values": [1, 2, 3]})

        # Act/Assert
        with pytest.raises(KeyError, match="min"):
            DataFrameReference.from_dataframe(df, name="with_nulls")

    def test_dataframe_with_partial_null_column_creates_valid_reference(self) -> None:
        """Given DataFrame with some nulls in column, When from_dataframe called, Then creates reference."""
        # Arrange
        df = pl.DataFrame({"some_null": [1, None, 3], "no_null": [1, 2, 3]})

        # Act
        ref = DataFrameReference.from_dataframe(df, name="with_some_nulls")

        # Assert
        with check:
            assert ref.column_summaries["some_null"].null_count == 1
        with check:
            assert ref.column_summaries["some_null"].count == 2
        with check:
            assert ref.column_summaries["no_null"].null_count == 0
        with check:
            assert ref.column_summaries["no_null"].count == 3


class TestDataFrameToolkitState:
    """Tests for the DataFrameToolkitState model."""

    def test_toolkit_state_empty(self) -> None:
        """Given empty references, When instantiated, Then state has empty references list."""
        # Act
        state = DataFrameToolkitState(references=[])

        # Assert
        with check:
            assert state.references == []

    def test_toolkit_state_with_references(self) -> None:
        """Given references list, When instantiated, Then state contains all references."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})
        ref = DataFrameReference.from_dataframe(df, name="test")

        # Act
        state = DataFrameToolkitState(references=[ref])

        # Assert
        with check:
            assert len(state.references) == 1
        with check:
            assert state.references[0].name == "test"

    def test_toolkit_state_json_round_trip(self) -> None:
        """Given state with references, When serialized and deserialized, Then data preserved."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})
        ref = DataFrameReference.from_dataframe(df, name="test", source_query="SELECT * FROM base")
        state = DataFrameToolkitState(references=[ref])

        # Act
        json_str = state.model_dump_json()
        restored = DataFrameToolkitState.model_validate_json(json_str)

        # Assert
        with check:
            assert len(restored.references) == 1
        with check:
            assert restored.references[0].name == "test"
        with check:
            assert restored.references[0].source_query == "SELECT * FROM base"

    def test_toolkit_state_to_json_produces_valid_json(self) -> None:
        """Given state with references, When model_dump_json called, Then produces valid JSON string."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3]})
        ref = DataFrameReference.from_dataframe(df, name="test")
        state = DataFrameToolkitState(references=[ref])

        # Act
        json_str = state.model_dump_json()

        # Assert
        with check:
            assert isinstance(json_str, str)
        # Should be parseable JSON
        parsed = json.loads(json_str)
        with check:
            assert "references" in parsed
        with check:
            assert len(parsed["references"]) == 1

    def test_toolkit_state_to_json_with_indent(self) -> None:
        """Given state, When model_dump_json called with indent, Then output is formatted."""
        # Arrange
        state = DataFrameToolkitState(references=[])

        # Act
        compact = state.model_dump_json()
        formatted = state.model_dump_json(indent=2)

        # Assert
        with check:
            assert "\n" not in compact
        with check:
            assert "\n" in formatted

    def test_toolkit_state_from_json_invalid_raises_error(self) -> None:
        """Given invalid JSON, When model_validate_json called, Then raises ValidationError."""
        # Act/Assert
        with pytest.raises(ValidationError):
            DataFrameToolkitState.model_validate_json("invalid json")

    def test_toolkit_state_serialization_preserves_all_fields(self) -> None:
        """Given reference with all fields, When round-tripped, Then all fields preserved."""
        # Arrange
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        ref = DataFrameReference.from_dataframe(
            df,
            name="test_df",
            description="A test DataFrame",
            source_query="SELECT * FROM parent WHERE x > 0",
            parent_ids=["df_00000001", "df_00000002"],
        )
        state = DataFrameToolkitState(references=[ref])

        # Act
        json_str = state.model_dump_json()
        restored = DataFrameToolkitState.model_validate_json(json_str)

        # Assert
        restored_ref = restored.references[0]
        with check:
            assert restored_ref.name == "test_df"
        with check:
            assert restored_ref.description == "A test DataFrame"
        with check:
            assert restored_ref.source_query == "SELECT * FROM parent WHERE x > 0"
        with check:
            assert restored_ref.parent_ids == ["df_00000001", "df_00000002"]
        with check:
            assert restored_ref.num_rows == 3
        with check:
            assert restored_ref.num_columns == 2
        with check:
            assert restored_ref.column_names == ["a", "b"]

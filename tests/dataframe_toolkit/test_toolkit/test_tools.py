"""Tests for DataFrameToolkit LangChain tool interface (get_tools, get_core_tools, schema, invocation)."""

from __future__ import annotations

import polars as pl
from pytest_check import check

from chain_reaction.dataframe_toolkit.models import DataFrameReference
from chain_reaction.dataframe_toolkit.toolkit import DataFrameToolkit


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

    def test_tool_invoke_get_dataframe_id(self) -> None:
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

    def test_tool_invoke_get_dataframe_reference(self) -> None:
        """Given toolkit with registered DataFrame, When get_dataframe_reference invoked, Returns DataFrameReference."""
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

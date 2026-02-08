"""Tests for DataFrameToolkit state export, reconstruction, and conversation resumption."""

from __future__ import annotations

from datetime import date

import polars as pl
import pytest
from pytest_check import check

from chain_reaction.dataframe_toolkit.models import (
    DataFrameReference,
    DataFrameToolkitState,
)
from chain_reaction.dataframe_toolkit.toolkit import DataFrameToolkit


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
            "derived",
            pl.DataFrame({"a": [1, 2]}),
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
        with pytest.raises(ValueError, match="Name 'wrong_name' not in state's base references"):
            DataFrameToolkit.from_state(state, {"wrong_name": base_df})

    def test_from_state_unknown_id_raises_error(self) -> None:
        """Given ID not in state, When from_state called, Then raises ValueError."""
        # Arrange
        original = DataFrameToolkit()
        base_df = pl.DataFrame({"a": [1, 2, 3]})
        original.register_dataframe("base", base_df)
        state = original.export_state()

        # Act/Assert
        with pytest.raises(ValueError, match="ID 'df_00000000' not in state's base references"):
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
        base_ref = DataFrameReference.from_dataframe("base", base_df)

        derived_ref = DataFrameReference.from_dataframe(
            "derived",
            pl.DataFrame({"a": [1]}),
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


class TestConversationResumptionScenarios:
    """End-to-end tests for conversation resumption workflow using from_state.

    TODO(testability): These tests directly access `toolkit._registry.context` and
    `toolkit._registry.references` to simulate derivative creation. Once `execute_sql`
    is implemented (Phase 6), refactor these tests to use the public API instead.
    See: .claude/agent-outputs/reviews/2026-02-04T033041Z-main-HEAD-review.md
    """

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
        result = original_toolkit._registry.context.execute_sql(query, eager=True)
        result_df = result if isinstance(result, pl.DataFrame) else result.collect()

        # Register derivative with source_query
        derived_ref = DataFrameReference.from_dataframe(
            "high_scorers",
            result_df,
            description="Students with score >= 85",
            source_query=query,
            parent_ids=[base_ref.id],
        )
        original_toolkit._registry.register(derived_ref, result_df)

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
        reconstructed_df = new_toolkit._registry.context.get_dataframe(derived_ref.id)
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
        b_result = original_toolkit._registry.context.execute_sql(b_query, eager=True)
        b_df = b_result if isinstance(b_result, pl.DataFrame) else b_result.collect()
        b_ref = DataFrameReference.from_dataframe("B", b_df, source_query=b_query, parent_ids=[a_ref.id])
        original_toolkit._registry.register(b_ref, b_df)

        # Create C from B
        c_query = f"SELECT x, y FROM {b_ref.id} WHERE x <= 2"  # noqa: S608
        c_result = original_toolkit._registry.context.execute_sql(c_query, eager=True)
        c_df = c_result if isinstance(c_result, pl.DataFrame) else c_result.collect()
        c_ref = DataFrameReference.from_dataframe("C", c_df, source_query=c_query, parent_ids=[b_ref.id])
        original_toolkit._registry.register(c_ref, c_df)

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
        c_reconstructed = new_toolkit._registry.context.get_dataframe(c_ref.id)
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
        join_result = original_toolkit._registry.context.execute_sql(join_query, eager=True)
        joined_df = join_result if isinstance(join_result, pl.DataFrame) else join_result.collect()
        joined_ref = DataFrameReference.from_dataframe(
            "user_orders",
            joined_df,
            source_query=join_query,
            parent_ids=[users_ref.id, orders_ref.id],
        )
        original_toolkit._registry.register(joined_ref, joined_df)

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
        reconstructed_df = new_toolkit._registry.context.get_dataframe(joined_ref.id)
        with check:
            assert reconstructed_df.shape == (4, 3)
        with check:
            assert "Alice" in reconstructed_df["name"].to_list()
        with check:
            assert reconstructed_df["name"].to_list().count("Alice") == 2  # Alice has 2 orders

    def test_null_heavy_dataframe_reconstruction(self) -> None:
        """Test reconstruction with null-heavy DataFrames and date columns."""
        original_toolkit = DataFrameToolkit()

        # Base dataframe with nulls across multiple columns and date data
        events_df = pl.DataFrame({
            "event_id": [1, 2, 3, 4, 5, 6],
            "event_date": [
                date(2025, 1, 15),
                date(2025, 3, 22),
                None,
                date(2025, 6, 1),
                None,
                date(2025, 12, 31),
            ],
            "category": ["sales", None, "support", None, None, "sales"],
            "revenue": [100.5, None, None, 250.0, None, 75.25],
        })
        events_ref = original_toolkit.register_dataframe("events", events_df)

        # Derive: filter to rows with non-null revenue
        query = f"SELECT event_id, event_date, category, revenue FROM {events_ref.id} WHERE revenue IS NOT NULL"  # noqa: S608
        result = original_toolkit._registry.context.execute_sql(query, eager=True)
        result_df = result if isinstance(result, pl.DataFrame) else result.collect()

        derived_ref = DataFrameReference.from_dataframe(
            "revenue_events",
            result_df,
            source_query=query,
            parent_ids=[events_ref.id],
        )
        original_toolkit._registry.register(derived_ref, result_df)

        # Export and restore
        state = original_toolkit.export_state()
        new_toolkit = DataFrameToolkit.from_state(state, {"events": events_df})

        # Verify
        with check:
            assert len(new_toolkit.references) == 2

        reconstructed_df = new_toolkit._registry.context.get_dataframe(derived_ref.id)
        with check:
            assert reconstructed_df.shape == (3, 4)  # 3 rows with non-null revenue
        with check:
            assert set(reconstructed_df["event_id"].to_list()) == {1, 4, 6}
        # Verify nulls survived round-trip in the derived data
        with check:
            assert reconstructed_df["category"].null_count() == 1  # event_id=4 has null category

"""Reducer functions for agent state fields."""

from typing import Any


def reduce_dict(left: dict[Any, Any] | None, right: dict[Any, Any] | None) -> dict[Any, Any]:
    """Merge two dictionaries."""
    left = left or {}
    right = right or {}
    return {**left, **right}


def reduce_list(left: list[Any] | None, right: list[Any] | None) -> list[Any]:
    """Combine two lists."""
    left = left or []
    right = right or []
    return [*left, *right]

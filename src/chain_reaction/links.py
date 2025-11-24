"""Utility functions for creating links between components in a chain."""

from functools import partial
from typing import Any, Literal

from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel


def init_model_dump_link(
    *,
    mode: str | Literal["json", "python"] = "python",
    include: set[str] | None = None,
    exclude: set[str] | None = None,
    field_remapping: dict[str, str] | None = None,
) -> RunnableLambda:
    """Initialize a LangChain link for dumping a Pydantic model to a dictionary.

    Args:
        mode (str | Literal['json', 'python']): The serialization mode.
            'json' for JSON-compatible dict, 'python' for Python-native types.
            Defaults to 'python'.
        include (set[str] | None): Fields to include in the dump. Defaults to None.
        exclude (set[str] | None): Fields to exclude from the dump. Defaults to None.
        field_remapping (dict[str, str] | None): Mapping of field names to new keys in the output dictionary.
            Defaults to None.

    Returns:
        RunnableLambda: A LangChain link that performs the model dump.
    """
    return RunnableLambda(
        partial(_dump_pydantic_model, mode=mode, include=include, exclude=exclude, field_remapping=field_remapping)
    )


# Helpers
def _dump_pydantic_model(
    model: BaseModel,
    *,
    mode: str | Literal["json", "python"] = "python",
    include: set[str] | None = None,
    exclude: set[str] | None = None,
    field_remapping: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Get a dictionary representation of a pydantic model, optionally specifying which fields to include or exclude.

    Args:
        model (BaseModel): The Pydantic model instance.
        mode (str | Literal['json', 'python']): The serialization mode.
            'json' for JSON-compatible dict, 'python' for Python-native types.
            Defaults to 'python'.
        include (set[str] | None): Fields to include in the dump. Defaults to None.
        exclude (set[str] | None): Fields to exclude from the dump. Defaults to None.
        field_remapping (dict[str, str] | None): Mapping of field names to new keys in the output dictionary.
            Defaults to None.

    Returns:
        dict[str, Any]: The dictionary representation of the model.
    """
    if field_remapping is None:
        field_remapping = {}
    return {
        field_remapping.get(k, k): v for k, v in model.model_dump(mode=mode, include=include, exclude=exclude).items()
    }

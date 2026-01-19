"""Module for generating and validating unique DataFrame identifiers."""

from __future__ import annotations

import re
from typing import Annotated
from uuid import uuid4

from pydantic import AfterValidator, Field

DATAFRAME_ID_PATTERN = re.compile(r"^df_[0-9a-f]{8}$")


def generate_dataframe_id() -> str:
    """Generate a unique identifier for a DataFrame that can be used in a dataframe registry."""
    return f"df_{uuid4().hex[:8]}"


def validate_dataframe_id(value: str) -> str:
    """Validate that a DataFrame ID follows the pattern df_<8 hex chars>."""
    if not DATAFRAME_ID_PATTERN.match(value):
        msg = f"DataFrame ID must match pattern 'df_<8 hex chars>', got: {value}"
        raise ValueError(msg)
    return value


DataFrameId = Annotated[
    str,
    AfterValidator(validate_dataframe_id),
    Field(
        description="Unique DataFrame identifier in the format df_<8 hex chars>.",
        examples=["df_1a2b3c4d", "df_abcd1234"],
    ),
]

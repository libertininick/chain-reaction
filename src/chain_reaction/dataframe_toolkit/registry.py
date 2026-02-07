"""DataFrame registry grouping context and references."""

from __future__ import annotations

import dataclasses

from chain_reaction.dataframe_toolkit.context import DataFrameContext
from chain_reaction.dataframe_toolkit.identifier import DataFrameId
from chain_reaction.dataframe_toolkit.models import DataFrameReference


@dataclasses.dataclass
class DataFrameRegistry:
    """Groups a DataFrameContext and its associated references.

    This container holds the two data structures that are always
    modified together during DataFrame registration and state restoration.

    Attributes:
        context (DataFrameContext): The SQL-capable DataFrame registry.
        references (dict[DataFrameId, DataFrameReference]): Mapping of
            DataFrameId to reference metadata.
    """

    context: DataFrameContext = dataclasses.field(default_factory=DataFrameContext)
    references: dict[DataFrameId, DataFrameReference] = dataclasses.field(default_factory=dict)

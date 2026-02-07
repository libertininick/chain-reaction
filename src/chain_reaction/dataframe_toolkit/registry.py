"""DataFrame registry grouping context and references."""

from __future__ import annotations

import dataclasses

import polars as pl

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

    def register(self, reference: DataFrameReference, dataframe: pl.DataFrame | pl.LazyFrame) -> None:
        """Register a dataframe with its reference metadata.

        Updates both the SQL context and references dict together,
        keeping them in sync.

        Args:
            reference (DataFrameReference): The reference metadata for the dataframe.
            dataframe (pl.DataFrame | pl.LazyFrame): The dataframe to register.
        """
        self.context.register(reference.id, dataframe)
        self.references[reference.id] = reference

    def unregister(self, dataframe_id: DataFrameId) -> None:
        """Unregister a dataframe from both context and references.

        Args:
            dataframe_id (DataFrameId): The ID of the dataframe to unregister.
        """
        self.context.unregister(dataframe_id)
        del self.references[dataframe_id]

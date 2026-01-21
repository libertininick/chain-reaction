"""Models for DataFrame manipulation and analysis using LangChain tools."""

from __future__ import annotations

import polars as pl
from pydantic import BaseModel, Field

from chain_reaction.dataframe_toolkit.identifier import DataFrameId, generate_dataframe_id
from chain_reaction.dataframe_toolkit.polars_utils import get_series_description


class ColumnSummary(BaseModel):
    """A summary of a single column in a DataFrame."""

    description: str = Field(description="A textual description of the column for analysis context.")
    dtype: str = Field(description="The data type of the column.")
    count: int = Field(description="The number of non-null entries in the column.")
    null_count: int = Field(description="The number of null entries in the column.")
    unique_count: int = Field(description="The number of unique entries in the column.")
    min: float | str = Field(description="The minimum value in the column.")
    max: float | str = Field(description="The maximum value in the column.")
    mean: float | str | None = Field(description="The mean value in the column.")
    std: float | str | None = Field(description="The standard deviation of the values in the column.")
    p25: float | str | None = Field(description="The 25th percentile of the values in the column.")
    p50: float | str | None = Field(description="The 50th percentile (median) of the values in the column.")
    p75: float | str | None = Field(description="The 75th percentile of the values in the column.")

    @classmethod
    def from_series(cls, series: pl.Series, description: str | None = None) -> ColumnSummary:
        """Create a ColumnSummary from a Polars Series.

        Args:
            series (pl.Series): The Polars Series to summarize.
            description (str | None, optional): An optional textual description of the column. Defaults to None.

        Returns:
            ColumnSummary: The generated ColumnSummary.
        """
        # Get descriptive statistics for the series
        des_dict = get_series_description(series)

        return cls(
            description=description or "",
            dtype=str(series.dtype),
            count=int(des_dict["count"]),
            null_count=int(des_dict["null_count"]),
            unique_count=series.n_unique(),
            min=des_dict["min"],
            max=des_dict["max"],
            mean=des_dict.get("mean"),
            std=des_dict.get("std"),
            p25=des_dict.get("25%"),
            p50=des_dict.get("50%"),
            p75=des_dict.get("75%"),
        )


class DataFrameReference(BaseModel):
    """A reference to a Polars DataFrame in a dataframe registry."""

    id: DataFrameId = Field(
        description="Unique identifier to reference the DataFrame in the dataframe registry and SQL queries.",
        default_factory=generate_dataframe_id,
    )
    name: str = Field(description="The name of the DataFrame.")
    description: str = Field(description="A textual description of the the DataFrame for analysis context.")
    num_rows: int = Field(description="The number of rows in the DataFrame.")
    num_columns: int = Field(description="The number of columns in the DataFrame.")
    column_names: list[str] = Field(description="The names of the columns in the DataFrame.")
    column_summaries: dict[str, ColumnSummary] = Field(description="A summary of each column in the DataFrame.")
    parent_ids: list[DataFrameId] = Field(
        description="The identifiers of the immediate parent DataFrames of this DataFrame, if any.",
        default_factory=list,
    )

    @classmethod
    def from_dataframe(
        cls,
        dataframe: pl.DataFrame,
        name: str,
        description: str | None = None,
        column_descriptions: dict[str, str] | None = None,
        parent_ids: list[DataFrameId] | None = None,
    ) -> DataFrameReference:
        """Create a DataFrameReference from a Polars DataFrame.

        Args:
            dataframe (pl.DataFrame): Polars DataFrame.
            name (str): The name of the DataFrame.
            description (str | None): An optional textual description of the DataFrame. Defaults to None.
            column_descriptions (dict[str, str] | None): Optional textual descriptions of the columns. Defaults to None.
            parent_ids (list[DataFrameId] | None): Identifiers of the parent DataFrames, if any. Defaults to None.

        Returns:
            DataFrameReference: The generated DataFrameReference.
        """
        if column_descriptions is None:
            column_descriptions = {}

        return cls(
            id=generate_dataframe_id(),
            name=name,
            num_rows=dataframe.height,
            num_columns=dataframe.width,
            column_names=dataframe.columns,
            column_summaries={
                col: ColumnSummary.from_series(dataframe[col], description=column_descriptions.get(col))
                for col in dataframe.columns
            },
            description=description or "",
            parent_ids=parent_ids or [],
        )

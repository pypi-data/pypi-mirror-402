from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypeAliasType

from olmoearth_shared.models.olmoearth_config.prediction_requests.projections import Projection


class PartitionerName(StrEnum):
    NOOP = "noop"
    GRID = "grid"


class NoopPartitioner(BaseModel):
    """Partitioner that does nothing."""
    name: Literal[PartitionerName.NOOP]


class GridPartitioner(BaseModel):
    """Partitioner that uses a grid to partition the input data."""
    name: Literal[PartitionerName.GRID]
    grid_size: float = Field(gt=0, description="The size of the grid cells in units of the output projection.")
    overlap_size: float = Field(default=0, ge=0, description="The size of the overlap between adjacent grid cells in units of the output projection.")
    projection: Projection | None = Field(default=None, description="Projection strategy to use for output geometries. If not provided, no re-projection will take place.")
    clip: bool = Field(default=False, description="If True, the partitioner will clip the output geometries to the input geometry. Otherwise, the produced grids might include areas outside the input geometry.")


Partitioner = TypeAliasType(
    "Partitioner",
    Annotated[
        GridPartitioner,
        Field(discriminator="name")
    ]
)


class Partitioners(BaseModel):
    request_to_partitions: Partitioner = Field(description="Controls the partitioning of the initial request into smaller units for machine-level parallelism.")
    partition_to_windows: Partitioner = Field(description="Controls the subdivision of a request partition into smaller units for process-level parallelism.")

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator
from typing_extensions import TypeAliasType


class DataSplitterName(StrEnum):
    RANDOM = "random"
    SPATIAL = "spatial"


class SplitProportions(BaseModel):
    train_prop: float = Field(ge=0, le=1, description="The proportion of data to assign to the training split.")
    val_prop: float = Field(ge=0, le=1, description="The proportion of data to assign to the validation split.")
    test_prop: float = Field(ge=0, le=1, description="The proportion of data to assign to the test split.")

    @model_validator(mode='after')
    def validate_proportions_sum_to_one(self) -> 'SplitProportions':
        """Ensure that train_prop + val_prop + test_prop == 1"""
        total = self.train_prop + self.val_prop + self.test_prop
        if abs(total - 1.0) > 1e-9:
            raise ValueError("Proportions must sum to 1.0")
        return self


class RandomDataSplitter(SplitProportions):
    """Data splitter that assigns splits based on random sampling."""
    name: Literal[DataSplitterName.RANDOM]
    seed: int | None = Field(default=42, description="The seed for the random number generator.")


class SpatialDataSplitter(SplitProportions):
    """Data splitter that assigns splits based on spatial grid cell location."""
    name: Literal[DataSplitterName.SPATIAL]
    grid_size: int = Field(ge=1, description="The size of the grid cells in pixels.")


DataSplitter = TypeAliasType(
    "DataSplitter",
    Annotated[
        RandomDataSplitter | SpatialDataSplitter,
        Field(discriminator="name")
    ]
)

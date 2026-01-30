"""
Used (optionally) to winnow down items from training data splits at training time.
"""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypeAliasType


class RandomSamplerName(StrEnum):
    RANDOM = "random"


class RandomSampler(BaseModel):
    name: Literal[RandomSamplerName.RANDOM]
    num_samples: int = Field(ge=0, description="The number of samples to take")
    replace: bool = Field(default=False, description="Whether sampled items can be sampled again")


TrainingSampler = TypeAliasType(
    "TrainingSampler",
    Annotated[
        RandomSampler,
        Field(discriminator="name")
    ]
)

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypeAliasType


class AnnotationSamplerName(StrEnum):
    NOOP = "noop"
    CHOOSE_N = "choose_n"


class NoopSampler(BaseModel):
    """No-op sampler that returns the full dataset."""
    name: Literal[AnnotationSamplerName.NOOP]


class ChooseNSampler(BaseModel):
    """Sampler that chooses a random subset of annotation tasks."""
    name: Literal[AnnotationSamplerName.CHOOSE_N]
    n: int = Field(ge=0, description="The number of samples to take")


AnnotationSampler = TypeAliasType(
    "AnnotationSampler",
    Annotated[
        NoopSampler | ChooseNSampler,
        Field(discriminator="name")
    ]
)

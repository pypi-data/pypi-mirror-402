"""
Named data transformers that manipulate input tensors before they are provided to the model.
These can provide normalizations ahead of specific encoders, augmentations during training, or other processing.

Meant to be chained.
"""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypeAliasType


class TransformName(StrEnum):
    OLMOEARTH_NORMALIZE = "olmoearth_normalize"
    RANDOM_FLIP = "random_flip"


class OlmoEarthNormalize(BaseModel):
    name: Literal[TransformName.OLMOEARTH_NORMALIZE]


class RandomFlip(BaseModel):
    name: Literal[TransformName.RANDOM_FLIP]
    x: bool = Field(default=True, description="Flip the image horizontally")
    y: bool = Field(default=True, description="Flip the image vertically")


Transform = TypeAliasType(
    "Transform",
    Annotated[
        OlmoEarthNormalize | RandomFlip,
        Field(discriminator="name")
    ]
)

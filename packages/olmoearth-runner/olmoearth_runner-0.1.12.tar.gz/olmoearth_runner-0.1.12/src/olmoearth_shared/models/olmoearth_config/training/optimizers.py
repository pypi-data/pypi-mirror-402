from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypeAliasType


class OptimizerName(StrEnum):
    ADAMW = "adamw"


class AdamW(BaseModel):
    name: Literal[OptimizerName.ADAMW]
    lr: float = Field(ge=0, description="The learning rate to use for the optimizer.")


Optimizer = TypeAliasType(
    "Optimizer",
    Annotated[
        AdamW,
        Field(discriminator="name")
    ]
)

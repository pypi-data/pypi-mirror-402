from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypeAliasType


class SchedulerName(StrEnum):
    PLATEAU = "plateau"


class Plateau(BaseModel):
    """Lowers learning rate via an exponential decay strategy when model performance plateaus. """
    name: Literal[SchedulerName.PLATEAU]
    factor: float = Field(ge=0, le=1, description="Multiplicative factor of learning rate decay. LR = LR * factor.")
    patience: int = Field(ge=0, description="Number of epochs with no improvement after which learning rate will be reduced.")
    min_lr: float = Field(ge=0, description="A lower bound on the learning rate.")
    cooldown: int = Field(ge=0, description="Number of epochs to wait before resuming normal operation after lr has been reduced.")


Scheduler = TypeAliasType(
    "Scheduler",
    Annotated[
        Plateau,
        Field(discriminator="name")
    ]
)

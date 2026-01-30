from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypeAliasType

MAX_TIMESTEPS = 12  # OlmoEarth's max number of timesteps


class TemporalityName(StrEnum):
    SAMPLED = "sampled"
    REPEATING_INTERVAL = "repeating_interval"


class Month(StrEnum):
    JANUARY = "January"
    FEBRUARY = "February"
    MARCH = "March"
    APRIL = "April"
    MAY = "May"
    JUNE = "June"
    JULY = "July"
    AUGUST = "August"
    SEPTEMBER = "September"
    OCTOBER = "October"
    NOVEMBER = "November"
    DECEMBER = "December"


class SampledTemporality(BaseModel):
    """
    Represents a temporal configuration that samples data from a given duration.
    """
    name: Literal[TemporalityName.SAMPLED]
    duration_days: int = Field(ge=0, description="The length of time in which to sample data.")
    num_samples: int = Field(ge=1, le=MAX_TIMESTEPS, description="The number of samples to take or construct within the duration.")


class RepeatingIntervalTemporality(BaseModel):
    """
    Represents a temporal configuration to sample/generate a single image for each of a fixed number
    of periods of equal duration.
    """
    name: Literal[TemporalityName.REPEATING_INTERVAL]
    period_duration_days: int = Field(ge=0, description="The length of time a single period lasts for.")
    num_periods: int = Field(ge=1, le=MAX_TIMESTEPS, description="The number of periods total, each `period_duration_days` long.")
    allowed_start_month_constraints: set[Month] | None = Field(default=None, description="The months that are valid for starting the repeating interval in.")


# TODO: pre_post_sampled, pre_post_interval


Temporality = TypeAliasType(
    "Temporality",
    Annotated[
        SampledTemporality | RepeatingIntervalTemporality,
        Field(discriminator="name")
    ]
)

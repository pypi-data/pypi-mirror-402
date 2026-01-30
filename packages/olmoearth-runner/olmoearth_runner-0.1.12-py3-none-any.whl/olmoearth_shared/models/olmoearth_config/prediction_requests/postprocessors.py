from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypeAliasType


class PostprocessorName(StrEnum):
    NOOP = "noop"
    COMBINE_GEOTIFF = "combine_geotiff"


class NoopPostprocessor(BaseModel):
    """Postprocessor that does nothing."""
    name: Literal[PostprocessorName.NOOP]


class CombineGeotiff(BaseModel):
    """Postprocessor that combines the geotiffs into a single geotiff."""
    name: Literal[PostprocessorName.COMBINE_GEOTIFF]


Postprocessor = TypeAliasType(
    "Postprocessor",
    Annotated[
        NoopPostprocessor | CombineGeotiff,
        Field(discriminator="name")
    ]
)


class Postprocessors(BaseModel):
    window: Postprocessor = Field(description="Controls the postprocessing of the prediction results for a single window.")
    partition: Postprocessor = Field(description="Controls the postprocessing of all the window results for a single partition.")
    request: Postprocessor = Field(description="Controls the postprocessing of all the partition results for the entire request.")

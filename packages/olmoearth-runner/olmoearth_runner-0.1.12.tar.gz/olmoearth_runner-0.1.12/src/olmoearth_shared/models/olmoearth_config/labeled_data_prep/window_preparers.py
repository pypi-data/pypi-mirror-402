from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypeAliasType


class WindowPreparerName(StrEnum):
    POINT_TO_RASTER = "point_to_raster"
    POLYGON_TO_RASTER = "polygon_to_raster"


class PointToRasterWindowPreparer(BaseModel):
    """Preparer that converts point annotations into raster windows centered on the point."""
    name: Literal[WindowPreparerName.POINT_TO_RASTER]
    window_buffer: int = Field(ge=0, description="The buffer around the point in pixels.")


class PolygonToRasterWindowPreparer(BaseModel):
    """Preparer that converts polygon annotations into raster windows enclosing the task geometry."""
    name: Literal[WindowPreparerName.POLYGON_TO_RASTER]


WindowPreparer = TypeAliasType(
    "WindowPreparer",
    Annotated[
        PointToRasterWindowPreparer | PolygonToRasterWindowPreparer,
        Field(discriminator="name")
    ]
)

from enum import StrEnum

from pydantic import BaseModel, Field


class SpaceMode(StrEnum):
    """How to build up or sample imagery."""

    MOSAIC = "mosaic"
    CONTAINS = "contains"


class Sentinel2L2ASortBy(StrEnum):
    CLOUD_COVER = "cloud_cover"


class Sentinel2L2A(BaseModel):
    sort_by: Sentinel2L2ASortBy = Field(default=Sentinel2L2ASortBy.CLOUD_COVER, description="The field to sort the data by.")
    space_mode: SpaceMode


# TODO: sentinel-1-rtc, landsat8/9


class Modalities(BaseModel):
    sentinel2_l2a: Sentinel2L2A | None = None

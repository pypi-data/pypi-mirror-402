from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypeAliasType

from olmoearth_shared.models.olmoearth_config.model.decoders import SegmentationDecoder


class TaskName(StrEnum):
    SEGMENTATION = "segmentation"


class SegmentationTask(BaseModel):
    name: Literal[TaskName.SEGMENTATION]
    decoder: SegmentationDecoder


# TODO: classification, per-pixel regression, regression, and detection tasks


ModelTask = TypeAliasType(
    "ModelTask",
    Annotated[
        SegmentationTask,
        Field(discriminator="name")
    ]
)

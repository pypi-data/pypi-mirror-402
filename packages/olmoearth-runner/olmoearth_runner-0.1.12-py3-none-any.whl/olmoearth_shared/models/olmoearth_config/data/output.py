from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypeAliasType

from olmoearth_shared.models.olmoearth_config.data_type import DataType


class FieldType(StrEnum):
    """Field type discriminator values"""
    CLASSIFICATION = "classification"
    SEGMENTATION = "segmentation"
    REGRESSION = "regression"


ColorChannel = Annotated[int, Field(ge=0, le=255)]
RGB = tuple[ColorChannel, ColorChannel, ColorChannel]
RGBA = tuple[ColorChannel, ColorChannel, ColorChannel, ColorChannel]


class ClassificationValue(BaseModel):
    """A single value allowed for vector- or per-pixel classification (segmentation)."""
    value: int = Field(ge=0, description="The computer-friendly value stored in the raster or geojson")
    label: str = Field(description="The human-readable label for this value")
    color: RGB | RGBA = Field(description="The RGB(A) color for this value")


class ClassificationField(BaseModel):
    """A field that represents vector-level classification"""
    field_type: Literal[FieldType.CLASSIFICATION]
    allowed_values: list[ClassificationValue]


class SegmentationField(BaseModel):
    """A field that represents per-pixel classification"""
    field_type: Literal[FieldType.SEGMENTATION]
    allowed_values: list[ClassificationValue]
    nodata_value: int | None = Field(default=None, description="The value to use for nodata pixels.")


class RegressionField(BaseModel):
    field_type: Literal[FieldType.REGRESSION]
    min_value: float = Field(description="Minimum possible value for this field")
    max_value: float = Field(description="Maximum possible value for this field")
    colormap_name: str = Field(
        default="viridis",
        description="Name of the rio_tiler colormap to use, "
                    "see https://cogeotiff.github.io/rio-tiler/colormap/#default-rio-tilers-colormaps"
    )
    nodata_value: float | None = Field(default=None, description="The value to use for nodata pixels. Respected for labeled training data and in inference outputs.")


RasterField = TypeAliasType(
    "RasterField",
    Annotated[
        SegmentationField | RegressionField,
        Field(discriminator="field_type")
    ]
)


VectorField = TypeAliasType(
    "VectorField",
    Annotated[
        ClassificationField | RegressionField, # TODO: DetectionField
        Field(discriminator="field_type")
    ]
)


class RasterOutput(BaseModel):
    data_type: Literal[DataType.RASTER]
    fields: dict[str, RasterField]


class VectorOutput(BaseModel):
    data_type: Literal[DataType.VECTOR]
    fields: dict[str, VectorField]


Output = TypeAliasType(
    "Output",
    Annotated[
        RasterOutput | VectorOutput,
        Field(discriminator="data_type")
    ]
)

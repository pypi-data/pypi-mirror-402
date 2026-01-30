#TODO(chrisw): this is going away at some point
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class InferenceResultsDataType(StrEnum):
    RASTER = "RASTER"
    VECTOR = "VECTOR"


class PredictionValue(BaseModel):
    """this is a single class value that the model can choose from on a given ClassificationField"""
    value: int | str = Field(description="The computer-friendly value stored in the raster or geojson")
    label: str = Field(description="The human-readable label for this value")
    color: tuple[int, int, int] | tuple[int, int, int, int] = Field(description="The RGB(A) color for this value")

    @field_validator("color", mode="after")
    @classmethod
    def validate_color_values(cls, v: tuple[int, int, int]) -> tuple[int, int, int]:
        """Validate that each RGB value is between 0 and 255."""
        for _, val in enumerate(v):
            if not 0 <= val <= 255:
                raise ValueError(f"Color value must be between 0 and 255, got {val}")
        return v


class ClassificationField(BaseModel):
    """A field the model will try to classify"""
    property_name: str = Field(
        description="The property field name in the geojson feature, or just the name of this band in a raster file"
    )
    confidence_property_name: str | None = Field(
        default=None,
        description="For vector results, if this field has a corresponding confidence field, the name of that field"
    )
    allowed_values: list[PredictionValue]
    band_index: int | None = Field(
        default=None,
        description="For raster results, the index of this field's band in the raster (1-based)"
    )
    confidence_band_index: int | None = Field(
        default=None,
        description="For raster results, if this field has a corresponding confidence value, the band of that field"
    )

    def build_colormap(self) -> dict[int, tuple[int, int, int, int]]:
        """Generates a rio_tiler compliant colormap and adds in alpha if missing"""
        return {
            int(av.value): av.color if len(av.color) == 4 else av.color + (255,)
            for av in self.allowed_values
        }


class RegressionField(BaseModel):
    """A field that the model tries to predict a continuous value of"""
    property_name: str = Field(
        description="The property field name in the geojson feature, or just the name of this band in a raster file")
    band_index: int | None = Field(
        default=None,
        description="For raster results, the index of this field's band in the raster (1-based)")
    min_value: float = Field(description="Minimum possible value for this field")
    max_value: float = Field(description="Maximum possible value for this field")
    colormap_name: str = Field(
        default="viridis",
        description="Name of the rio_tiler colormap to use, "
                    "see https://cogeotiff.github.io/rio-tiler/colormap/#default-rio-tilers-colormaps"
    )


class DetectionObject(BaseModel):
    """For detection models; this is an object the model is trying to detect"""
    detected_object_name: str = Field(description="The name of the object the model is trying to detect (e.g., 'car')")
    confidence_property_name: str | None = Field(
        default=None,
        description="For vector results, if there is a corresponding confidence field, this is the name of that field")
    confidence_band_index: int | None = Field(
        default=None,
        description="For raster results, if there is a corresponding confidence value, this the band of that field"
    )


class InferenceResultsConfig(BaseModel):
    """Configuration for inference results."""
    data_type: InferenceResultsDataType = Field(
        description="The type of predictions that this model returns. Options: RASTER, VECTOR"
    )
    classification_fields: list[ClassificationField] | None = Field(
        default=None,
        description="Classification legend mapping pixel values to labels and colors for raster outputs"
    )
    regression_fields: list[RegressionField] | None = Field(
        default=None,
        description='Fields that the model will predict a continous value on'
    )
    detection_objects: list[DetectionObject] | None = Field(
        default=None,
        description='For a detection model, this is the object(s) that the model is trying to find'
    )

    @field_validator("data_type", mode="before")
    @classmethod
    def uppercase_data_type(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.upper()
        return v

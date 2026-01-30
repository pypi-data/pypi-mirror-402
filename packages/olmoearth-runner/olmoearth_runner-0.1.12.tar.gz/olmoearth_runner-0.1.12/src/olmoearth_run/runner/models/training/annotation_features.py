from datetime import datetime
import uuid

from geojson_pydantic import Feature, FeatureCollection
from geojson_pydantic.geometries import Geometry, MultiPolygon, Polygon
from pydantic import BaseModel, Field, field_validator, model_validator


def _validate_time_range(start_time: datetime | None, end_time: datetime | None) -> None:
    if start_time is None or end_time is None:
        return

    if start_time > end_time:
        raise ValueError("Start time must be before end time")

    return


class AnnotationTaskFeatureProperties(BaseModel):
    """
    Properties for an Earth System Studio Annotation Task that contains a group of annotations.
    """
    oe_annotations_task_id: uuid.UUID = Field(description="The ID of the task that created the feature")
    oe_start_time: datetime = Field(description="The beginning of the temporal component")
    oe_end_time: datetime = Field(description="The end of the temporal component")

    @model_validator(mode='after')
    def validate_time_range(self) -> 'AnnotationTaskFeatureProperties':
        _validate_time_range(self.oe_start_time, self.oe_end_time)
        return self


class AnnotationFeatureProperties(BaseModel):
    oe_labels: dict[str, int | float | None]= Field(description="The labels of the feature (can have multiple fields for multi-task models)")
    oe_start_time: datetime | None = Field(default=None, description="The beginning of the temporal component")
    oe_end_time: datetime | None = Field(default=None, description="The end of the temporal component")
    oe_annotations_task_id: uuid.UUID = Field(description="The ID of the task that created the feature")

    @model_validator(mode='after')
    def validate_time_range(self) -> 'AnnotationFeatureProperties':
        _validate_time_range(self.oe_start_time, self.oe_end_time)
        return self

    @field_validator('oe_labels')
    @classmethod
    def validate_labels(cls, v: dict[str, int | float | None]) -> dict[str, int | float | None]:
        for value in v.values():
            if value is not None:
                return v

        raise ValueError("At least one label must be non-null")


class AnnotationTaskFeature(Feature[Polygon | MultiPolygon, AnnotationTaskFeatureProperties]):
    """A GeoJSON Feature for annotation tasks with guaranteed non-null geometry and properties."""

    # Override type annotations to be non-nullable
    geometry: Polygon | MultiPolygon
    properties: AnnotationTaskFeatureProperties

    def get_time_range(self) -> tuple[datetime, datetime]:
        """
        Extract temporal information from task properties.

        Returns:
            Tuple of (start_time, end_time)
        """
        return (self.properties.oe_start_time, self.properties.oe_end_time)


class AnnotationFeature(Feature[Geometry, AnnotationFeatureProperties]):
    """A GeoJSON Feature for annotations with guaranteed non-null geometry and properties."""

    # Override type annotations to be non-nullable
    geometry: Geometry
    properties: AnnotationFeatureProperties


class AnnotationTaskFeatureCollection(FeatureCollection[AnnotationTaskFeature]):
    """A GeoJSON FeatureCollection containing AnnotationTaskFeatures."""
    pass


class AnnotationFeatureCollection(FeatureCollection[AnnotationFeature]):
    """A GeoJSON FeatureCollection containing AnnotationFeatures."""
    pass

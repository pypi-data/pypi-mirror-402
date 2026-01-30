import uuid
from datetime import datetime
from typing import Generic, TypeVar, cast

from numpy import ndarray
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from rslearn.utils import Projection, STGeometry
from shapely.geometry.base import BaseGeometry

from olmoearth_run.shared.models.data_split_type import DataSplitType


class LabeledSTGeometry(BaseModel):
    """
    A spatio-temporal geometry with an associated label.
    Can be used to represent unprocessed annotations,
    or processed features for inclusion in training windows.
    """
    model_config = {"arbitrary_types_allowed": True}

    st_geometry: STGeometry = Field(description="Spatial-temporal geometry with explicit projection")
    labels: dict[str, int | float | None] = Field(description="The label value(s) (can have multiple fields for multi-task models)")

    @field_validator('labels')
    @classmethod
    def validate_labels(cls, v: dict[str, int | float | None]) -> dict[str, int | float | None]:
        for value in v.values():
            if value is not None:
                return v

        raise ValueError("At least one label must be non-null")


class RasterLabel(BaseModel):
    """
    A raster label with a key and a value.
    """
    model_config = {"arbitrary_types_allowed": True}

    key: str = Field(description="The key of the label")
    value: ndarray = Field(description="The value of the label")


class AnnotationTask(BaseModel):
    """
    Annotations belonging to a single Earth System Studio Annotation Task.
    Encapsulates the full task boundary and the set of all
    annotated spatio-temporal geometries collected for that task.
    """
    model_config = {"arbitrary_types_allowed": True}

    task_id: uuid.UUID = Field(description="The ID of the annotation task")
    task_st_geometry: STGeometry = Field(description="The spatio-temporal boundary of the annotation task as STGeometry")
    annotations: list[LabeledSTGeometry] = Field(description="The labeled ST geometries for the annotations in the task")

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """
        Get the bounds of the annotation task.

        Returns:
            Tuple of (minx, miny, maxx, maxy) in the task geometry's projection coordinates
        """
        return cast(BaseGeometry, self.task_st_geometry.shp).bounds


# Type alias for constraint - can be either list of geojson features or list of ndarray maps with their label keys
TrainingWindowLabelsTypes = list[LabeledSTGeometry] | list[RasterLabel]
TrainingWindowLabels = TypeVar('TrainingWindowLabels', bound=TrainingWindowLabelsTypes)


class WindowOptions(BaseModel):
    """
    Options/metadata for a window that will be passed to the RSLearn window.options attribute.

    This class encapsulates all the metadata that the framework manages for windows,
    including data splits and provenance tracking.
    """
    data_split: DataSplitType = Field(description="The assigned data split (train/val/test)")
    source_task_id: uuid.UUID = Field(description="The source task ID for provenance tracking")


class LabeledWindow(BaseModel, Generic[TrainingWindowLabels]):
    """Base class with shared validation logic for window + features compatibility."""
    name: str = Field(description="Window identifier")
    st_geometry: STGeometry = Field(description="Spatial-temporal geometry defining the window extent, projection, and time range")
    labels: TrainingWindowLabels = Field(description="Training labels as list of GeoJSON features or 2D uint8 raster array")

    model_config = ConfigDict(arbitrary_types_allowed=True)  # Allow numpy arrays

    @property
    def projection(self) -> Projection:
        """Get the projection from the underlying geometry."""
        return self.st_geometry.projection

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        """Get the bounds from the underlying geometry, converted to integers."""
        float_bounds = cast(BaseGeometry, self.st_geometry.shp).bounds
        return (int(float_bounds[0]), int(float_bounds[1]), int(float_bounds[2]), int(float_bounds[3]))

    @property
    def time_range(self) -> tuple[datetime, datetime] | None:
        """Get the time range from the underlying geometry."""
        return self.st_geometry.time_range

    @model_validator(mode='after')
    def validate_labels(self) -> 'LabeledWindow[TrainingWindowLabels]':
        """Validate labels based on their content type."""
        if not self.labels:
            raise ValueError("Window must have at least one label")

        # Check the type of the first element to determine validation strategy
        first_label = self.labels[0]
        if isinstance(first_label, LabeledSTGeometry):
            # Validate each vector label
            for label in self.labels:
                if not isinstance(label, LabeledSTGeometry):
                    raise ValueError(f"Mixed label types not supported. Expected all LabeledSTGeometry, got {type(label)}")
                self._validate_vector_label(label)
        elif isinstance(first_label, RasterLabel):
            # Validate each raster label
            for label in self.labels:
                if not isinstance(label, RasterLabel):
                    raise ValueError(f"Mixed label types not supported. Expected all RasterLabel, got {type(label)}")
                self._validate_raster_label(label)
        else:
            raise ValueError(f"Unsupported label type: {type(first_label)}. Expected LabeledSTGeometry or RasterLabel")
        return self

    def _validate_vector_label(self, label: LabeledSTGeometry) -> None:
        """Validate a single vector label: spatial containment within window bounds."""
        if not hasattr(label, 'st_geometry') or label.st_geometry is None:
            return

        try:
            feature_geom = cast(BaseGeometry, label.st_geometry.shp)

            if label.st_geometry.projection != self.projection:
                raise ValueError(
                    f"Feature projection {label.st_geometry.projection} does not match "
                    f"window projection {self.projection}"
                )

            # Skip validation for empty geometries (they have NaN bounds)
            if feature_geom.is_empty:
                return

            win_minx, win_miny, win_maxx, win_maxy = self.bounds
            feat_minx, feat_miny, feat_maxx, feat_maxy = feature_geom.bounds

            if not (win_minx <= feat_minx and feat_maxx <= win_maxx and
                    win_miny <= feat_miny and feat_maxy <= win_maxy):
                raise ValueError(
                    f"Feature geometry is not contained within window bounds. "
                    f"Feature bounds: {feature_geom.bounds}, Window bounds: {self.bounds}"
                )
        except Exception as e:
            raise ValueError(f"Error validating geometry for feature: {e}") from e

    def _validate_raster_label(self, label: RasterLabel) -> None:
        """Validate a single raster label: shape, dtype, and spatial dimensions."""
        # Validate shape and dtype
        if label.value.ndim != 2:
            raise ValueError(f"Raster label array must be 2D, got {label.value.ndim}D")

        # TODO: dtype check -- need to figure out what's supportable in RSLearn

        # Validate spatial dimensions match bounds
        minx, miny, maxx, maxy = self.bounds
        expected_width = maxx - minx
        expected_height = maxy - miny

        actual_height, actual_width = label.value.shape

        if actual_width != expected_width:
            raise ValueError(
                f"Raster label width ({actual_width}) does not match expected width ({expected_width}) "
                f"for bounds range {maxx - minx}"
            )

        if actual_height != expected_height:
            raise ValueError(
                f"Raster label height ({actual_height}) does not match expected height ({expected_height}) "
                f"for bounds range {maxy - miny}"
            )


class ProcessedWindow(BaseModel):
    """
    A labeled window with its associated options/metadata.

    This encapsulates both the window data and the metadata that the framework
    manages (data splits, provenance, etc.).
    """
    window: LabeledWindow[TrainingWindowLabelsTypes] = Field(description="The labeled window")
    options: WindowOptions = Field(description="Window options/metadata managed by the framework")

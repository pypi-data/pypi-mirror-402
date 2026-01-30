"""
Polygon to Raster Window Preparer.

This module provides a window preparer that converts polygon/multipolygon annotations
to raster labels. It creates one window per annotation task, using the task geometry
as the window boundary and rasterizing the polygon annotations into uint8 labels.
"""

from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry
from typing import cast

from olmoearth_run.runner.models.training.labeled_data import (
    AnnotationTask,
    LabeledWindow,
    RasterLabel,
)
from olmoearth_run.runner.tools.labeled_window_preparers.labeled_window_preparer import (
    RasterLabelsWindowPreparer,
)
from olmoearth_run.runner.tools.labeled_window_preparers.geometry_utils import (
    compute_window_bounds,
    create_raster_labels_from_annotations,
    project_geometry_to_crs,
)
from olmoearth_run.runner.tools.labeled_window_preparers.rasterization_utils import (
    DEFAULT_NODATA_VALUE,
)
from rslearn.utils import STGeometry, get_utm_ups_crs


class PolygonToRasterWindowPreparer(RasterLabelsWindowPreparer):
    """
    Window preparer that converts polygon/multipolygon annotations to raster labels.

    This preparer creates one window per annotation task, using the task geometry
    as the window boundary. It rasterizes polygon annotations into uint8 raster
    labels where each pixel contains the class index of the polygon that covers it.

    Key characteristics:
    - One window per task (not per annotation)
    - Window boundary is the task geometry
    - Labels are uint8 raster arrays
    - Uses UTM projection for consistent resolution
    """

    def __init__(self, window_resolution: float = 10.0, nodata_value: int = DEFAULT_NODATA_VALUE):
        """
        Initialize the PolygonToRasterWindowPreparer.

        Args:
            window_resolution: Resolution in meters per pixel (default: 10.0)
        """
        self.window_resolution = window_resolution
        self.nodata_value = nodata_value

    def prepare_labeled_windows(
        self, annotation_task: AnnotationTask
    ) -> list[LabeledWindow[list[RasterLabel]]]:
        """
        Prepare labeled windows from polygon annotation tasks.

        This method creates one window per annotation task, using the task geometry
        as the window boundary. It rasterizes all polygon annotations within the task
        into a single uint8 raster label.

        Args:
            annotation_task: Single AnnotationTask object containing task context and annotations

        Returns:
            List containing one LabeledWindow object with raster labels, or empty list if no annotations
        """
        if not annotation_task.annotations:
            return []

        # Validate that all annotations have polygon geometries
        for annotation in annotation_task.annotations:
            geom = annotation.st_geometry.shp
            if not isinstance(geom, (Polygon, MultiPolygon)):
                raise ValueError(
                    f"Expected Polygon or MultiPolygon annotation geometry, "
                    f"got {type(geom).__name__} with geom_type {getattr(geom, 'geom_type', 'unknown')}"
                )

        # Calculate CRS based on task centroid
        task_centroid = cast(
            BaseGeometry, annotation_task.task_st_geometry.shp
        ).centroid
        utm_crs = get_utm_ups_crs(task_centroid.x, task_centroid.y)

        # Extract the task geometry
        task_geom = annotation_task.task_st_geometry.shp
        if not isinstance(
            task_geom, (Polygon, BaseGeometry)
        ) or task_geom.geom_type not in ["Polygon", "MultiPolygon"]:
            raise ValueError(
                f"Expected Polygon or MultiPolygon for task, got {type(task_geom)} with geom_type {getattr(task_geom, 'geom_type', 'unknown')}"
            )

        # Convert to appropriate projection if needed
        projected_geometry = project_geometry_to_crs(
            task_geom, self.window_resolution, utm_crs
        )

        # Create the window geometry
        window_st_geometry = STGeometry(
            projected_geometry.projection,
            projected_geometry.shp,
            annotation_task.task_st_geometry.time_range,
        )

        # Create the raster label by rasterizing polygon annotations
        # Use the exact bounds that the window will have
        window_bounds = compute_window_bounds(projected_geometry)
        raster_labels = create_raster_labels_from_annotations(
            annotations=annotation_task.annotations,
            window_bounds=window_bounds,
            window_resolution=self.window_resolution,
            crs=utm_crs,
            nodata_value=self.nodata_value,
        )

        labeled_window = LabeledWindow(
            name=f"task_{annotation_task.task_id}_polygon_window",
            st_geometry=window_st_geometry,
            labels=raster_labels,
        )

        return [labeled_window]

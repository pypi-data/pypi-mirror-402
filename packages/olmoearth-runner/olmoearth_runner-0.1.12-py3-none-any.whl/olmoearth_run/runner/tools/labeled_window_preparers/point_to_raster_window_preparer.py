"""Window preparer for creating windows with raster labels from point annotations."""

from typing import cast

import numpy as np
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
    create_window_geometry_from_point,
    project_geometry_to_crs,
)
from rslearn.config import DType
from rslearn.utils import get_utm_ups_crs
from shapely.geometry import Point


class PointToRasterWindowPreparer(RasterLabelsWindowPreparer):
    """Point to raster window preparer.

    Creates windows of specified size centered on each point annotation.
    """

    def __init__(
        self,
        window_buffer: int,
        window_resolution: float,
        dtype: str,
        nodata_value: int,
    ):
        """Initialize point to raster window preparer.

        This function allows for extracting patches where the labeled pixel can be at any
        position within the patch. The window_buffer parameter is related to the patch size
        around each point annotation. For example, using window_buffer of 31 creates 63x63
        windows, and with a patch size of 32, a point at the center will always be in the patch.

        Args:
            window_buffer: Buffer around the point in pixels (e.g., 31 creates 63x63 pixel windows)
            window_resolution: Resolution in meters per pixel (e.g., 10.0 for 10m/pixel)
            dtype: Data type for the raster labels (e.g., "float32", "uint8", "int16")
            nodata_value: Nodata value for the raster labels
        """
        self.window_buffer = window_buffer
        self.window_resolution = window_resolution
        self.dtype = DType(dtype.lower())
        self.nodata_value = nodata_value

    def prepare_labeled_windows(
        self, annotation_task: AnnotationTask
    ) -> list[LabeledWindow[list[RasterLabel]]]:
        """Prepare labeled windows from point annotation tasks.

        Creates one window per point annotation, with the point at the center
        of a window with window_buffer pixels around the point on each side.

        Args:
            annotation_task: Single AnnotationTask object containing point annotations

        Returns:
            List of LabeledWindow objects, one per point annotation
        """
        if not annotation_task.annotations:
            return []

        labeled_windows = []

        for i, annotation in enumerate(annotation_task.annotations):
            # Get the point geometry
            point_geom = annotation.st_geometry.shp
            if not isinstance(point_geom, Point):
                raise ValueError(
                    f"Expected Point geometry, got {type(point_geom)} with geom_type {getattr(point_geom, 'geom_type', 'unknown')}"
                )

            # Calculate CRS based on point location (not task centroid)
            # Since each point creates an independent window, use the point's coordinates
            # for proper UTM/UPS zone selection - this handles large tasks spanning multiple zones
            utm_crs = get_utm_ups_crs(point_geom.x, point_geom.y)

            projected_point = project_geometry_to_crs(
                point_geom, self.window_resolution, utm_crs
            )

            # Create window geometry centered on the point
            window_geometry = create_window_geometry_from_point(
                projected_point,
                self.window_buffer,
                annotation_task.task_st_geometry.time_range,
            )

            # Create raster labels for this window
            window_bounds = compute_window_bounds(window_geometry)
            raster_labels = create_raster_labels_from_annotations(
                annotations=[annotation],
                window_bounds=window_bounds,
                window_resolution=self.window_resolution,
                crs=utm_crs,
                dtype=cast(type[np.generic], self.dtype.get_numpy_dtype()),
                nodata_value=self.nodata_value,
            )

            labeled_window = LabeledWindow(
                name=f"task_{annotation_task.task_id}_point_{i}",
                st_geometry=window_geometry,
                labels=raster_labels,
            )

            labeled_windows.append(labeled_window)

        return labeled_windows

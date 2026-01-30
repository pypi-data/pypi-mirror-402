"""
Point-to-pixel window preparer implementation.

This module provides a concrete implementation of VectorFeaturesWindowPreparer
that creates single-pixel windows from point annotations. Each point annotation
becomes a 1x1 pixel window centered on the point location fit for training a classifier.
"""

from rslearn.utils import STGeometry, get_utm_ups_crs
from shapely.geometry import Point, box

from olmoearth_run.runner.models.training.labeled_data import (
    AnnotationTask,
    LabeledSTGeometry,
    LabeledWindow,
)
from olmoearth_run.runner.tools.labeled_window_preparers.labeled_window_preparer import (
    VectorLabelsWindowPreparer,
)
from olmoearth_run.runner.tools.labeled_window_preparers.geometry_utils import (
    project_geometry_to_crs,
)


class PointToPixelWindowPreparer(VectorLabelsWindowPreparer):
    """
    Window preparer that creates single-pixel windows from point annotations.

    Each point annotation becomes a 1x1 pixel window centered on the point location.
    This is useful for point-based classification tasks where each annotation
    represents a single pixel to be classified.
    """

    def __init__(self, window_resolution: float = 10.0):
        """
        Initialize the point-to-pixel window preparer.

        Args:
            window_resolution: Resolution in meters per pixel (default: 10.0 for Helios)
        """
        self.window_resolution = window_resolution

    def prepare_labeled_windows(
        self,
        annotation_task: AnnotationTask,
    ) -> list[LabeledWindow[list[LabeledSTGeometry]]]:
        """
        Prepare labeled windows with vector labels from point annotations.

        For each point annotation, creates a single-pixel window centered on the point.
        The window is sized to be exactly 1x1 pixels at the specified resolution.

        Args:
            annotation_task: Single AnnotationTask object containing task context and annotations

        Returns:
            List of LabeledWindow objects with single-pixel windows and point labels
        """
        # Skip tasks with no annotations - can't create meaningful training windows
        if not annotation_task.annotations:
            return []

        labeled_windows = []

        # Process each annotation in the task
        for annotation_idx, annotation in enumerate(annotation_task.annotations):
            # Create a single-pixel window for this point annotation
            labeled_window = self._create_single_pixel_window(
                annotation, annotation_task, annotation_idx
            )
            labeled_windows.append(labeled_window)

        return labeled_windows

    def _create_single_pixel_window(
        self, annotation: LabeledSTGeometry, task: AnnotationTask, annotation_idx: int
    ) -> LabeledWindow[list[LabeledSTGeometry]]:
        """
        Create a single-pixel window from a point annotation.

        Args:
            annotation: The point annotation to create a window for
            task: The parent annotation task
            annotation_idx: The index of this annotation within the task

        Returns:
            LabeledWindow with a single-pixel window and the point label
        """
        # Extract the point geometry
        point_geom = annotation.st_geometry.shp
        if not isinstance(point_geom, Point):
            raise ValueError(f"Expected Point geometry, got {type(point_geom)}")

        # Calculate CRS based on point location (not task centroid)
        # Since each point creates an independent window, use the point's coordinates
        # for proper UTM/UPS zone selection - this handles large tasks spanning multiple zones
        utm_crs = get_utm_ups_crs(point_geom.x, point_geom.y)

        # Convert to appropriate projection if needed
        projected_geometry = project_geometry_to_crs(
            point_geom, self.window_resolution, utm_crs
        )

        # Create a 1x1 pixel window centered on the point
        window_bounds = self._compute_single_pixel_bounds(projected_geometry)

        # Create a window geometry that matches the computed bounds
        window_geometry = box(*window_bounds)

        # Create the labeled window with the projected point annotation as the label
        # We need to project the annotation to the same coordinate system as the window
        # and use integer pixel coordinates to match the window bounds
        projected_point = projected_geometry.shp
        if not isinstance(projected_point, Point):
            raise ValueError(f"Expected Point geometry, got {type(projected_point)}")
        pixel_point = Point(int(projected_point.x), int(projected_point.y))
        pixel_projected_geometry = STGeometry(
            projected_geometry.projection, pixel_point, projected_geometry.time_range
        )

        projected_annotation = LabeledSTGeometry(
            st_geometry=pixel_projected_geometry, labels=annotation.labels
        )

        return LabeledWindow(
            name=f"task_{task.task_id}_annotation_{annotation_idx}_point_{point_geom.x}_{point_geom.y}",
            st_geometry=STGeometry(
                projected_geometry.projection,
                window_geometry,
                task.task_st_geometry.time_range,
            ),
            labels=[projected_annotation],  # Projected point annotation as the label
        )

    def _compute_single_pixel_bounds(
        self, projected_geometry: STGeometry
    ) -> tuple[int, int, int, int]:
        """
        Compute bounds for a single-pixel window centered on the point.

        This matches the reference implementation's approach:
        - Convert coordinates to integers (pixel coordinates)
        - Create a 1x1 pixel window with no padding
        - Upper bounds are exclusive, so add 1 to maxx and maxy

        Args:
            projected_geometry: The projected point geometry

        Returns:
            Tuple of (minx, miny, maxx, maxy) in pixel coordinates
        """
        point = projected_geometry.shp
        if not isinstance(point, Point):
            raise ValueError(f"Expected Point geometry, got {type(point)}")

        # Convert to integer pixel coordinates
        x, y = int(point.x), int(point.y)

        # Create a 1x1 pixel window with no padding
        minx = x
        miny = y
        maxx = x + 1
        maxy = y + 1

        return (minx, miny, maxx, maxy)

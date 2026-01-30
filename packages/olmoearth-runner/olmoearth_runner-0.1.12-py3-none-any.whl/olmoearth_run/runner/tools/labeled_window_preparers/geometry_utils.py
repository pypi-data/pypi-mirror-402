"""Utility functions for geometry operations."""

from collections import defaultdict
from datetime import datetime
from typing import cast

import numpy as np
from rslearn.utils import STGeometry, Projection
from rslearn.utils.geometry import WGS84_PROJECTION
from shapely.geometry import Point, box
from shapely.geometry.base import BaseGeometry

from olmoearth_run.runner.models.training.labeled_data import (
    LabeledSTGeometry,
    RasterLabel,
)
from olmoearth_run.runner.tools.labeled_window_preparers.rasterization_utils import (
    DEFAULT_NODATA_VALUE,
    rasterize_shapes_to_mask,
    transform_geometries_to_pixel_coordinates,
)


def create_window_geometry_from_point(
    projected_point: STGeometry,
    window_buffer: int,
    time_range: tuple[datetime, datetime] | None,
) -> STGeometry:
    """Create a square window geometry centered on the projected point.

    Args:
        projected_point: The projected point geometry
        window_buffer: Buffer around the point in pixels
        time_range: Time range for the window

    Returns:
        STGeometry representing the window bounds
    """
    point = cast(Point, projected_point.shp)

    # Create square polygon centered on the point using box
    minx = point.x - window_buffer
    miny = point.y - window_buffer
    maxx = point.x + window_buffer + 1
    maxy = point.y + window_buffer + 1

    window_polygon = box(minx, miny, maxx, maxy)

    return STGeometry(projected_point.projection, window_polygon, time_range)


def compute_window_bounds(window_geometry: STGeometry) -> tuple[int, int, int, int]:
    """Compute integer bounds for the window from the window geometry.

    Args:
        window_geometry: The window geometry

    Returns:
        Tuple of (minx, miny, maxx, maxy) in world coordinates
    """
    bounds = cast(BaseGeometry, window_geometry.shp).bounds

    minx = int(bounds[0])
    miny = int(bounds[1])
    maxx = int(bounds[2])
    maxy = int(bounds[3])

    return (minx, miny, maxx, maxy)


def create_raster_labels_from_annotations(
    annotations: list[LabeledSTGeometry],
    window_bounds: tuple[int, int, int, int],
    window_resolution: float,
    crs: str,
    dtype: type[np.generic] = np.uint8,
    nodata_value: int = DEFAULT_NODATA_VALUE,
) -> list[RasterLabel]:
    """Create raster labels by rasterizing annotations.

    Args:
        annotations: List of labeled annotations to rasterize
        window_bounds: Window bounds in world coordinates (minx, miny, maxx, maxy)
        window_resolution: Resolution in meters per pixel
        crs: The target coordinate reference system
        nodata_value: Value to use for nodata pixels
        dtype: Data type of the output array

    Returns:
        List of RasterLabel objects with rasterized labels
    """
    if not annotations:
        return []

    # Collect labeled shapes for rasterization
    keys = sorted(annotations[0].labels.keys())
    shape_labels: dict[str, list[tuple[BaseGeometry, int | float]]] = defaultdict(list)

    for annotation in annotations:
        # Project the annotation geometry to the specified CRS
        projected_annotation = project_geometry_to_crs(
            cast(BaseGeometry, annotation.st_geometry.shp), window_resolution, crs
        )

        # Add to shape labels with the label values
        for key in keys:
            label_value = annotation.labels[key]
            if label_value is not None:
                shape_labels[key].append(
                    (cast(BaseGeometry, projected_annotation.shp), label_value)
                )

    # Calculate the expected raster dimensions from the window bounds
    height = window_bounds[3] - window_bounds[1]  # maxy - miny
    width = window_bounds[2] - window_bounds[0]  # maxx - minx

    raster_labels: list[RasterLabel] = []
    for key in keys:
        # Transform geometries to pixel coordinates and rasterize
        pixel_shapes = transform_geometries_to_pixel_coordinates(
            shape_labels[key], window_bounds
        )

        label_mask = rasterize_shapes_to_mask(
            width, height, pixel_shapes, nodata_value, dtype
        )
        raster_labels.append(RasterLabel(key=key, value=label_mask))

    return raster_labels


def project_geometry_to_crs(
    geometry: BaseGeometry, window_resolution: float, crs: str
) -> STGeometry:
    """Project a geometry to a specified coordinate system.

    Args:
        geometry: The geometry to project
        window_resolution: Resolution in meters per pixel
        crs: The target coordinate reference system

    Returns:
        STGeometry projected to the specified CRS
    """
    # Create source geometry in WGS84
    src_geometry = STGeometry(WGS84_PROJECTION, geometry, None)

    # Create projection with specified resolution
    destination_projection = Projection(
        crs,
        window_resolution,
        -window_resolution,
    )

    # Project the geometry
    return src_geometry.to_projection(destination_projection)

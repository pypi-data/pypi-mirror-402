"""
Rasterization utilities for converting polygon annotations to raster labels.

This module provides utility functions for rasterizing labeled geometries into
uint8 raster arrays, with support for testing using pixel-space geometries.
"""

from typing import Sequence

import numpy as np
import rasterio.features  # type: ignore[import-untyped]
from shapely.affinity import translate
from shapely.geometry.base import BaseGeometry


DEFAULT_NODATA_VALUE = 255


def rasterize_shapes_to_mask(
    width: int,
    height: int,
    shape_labels: Sequence[tuple[BaseGeometry, int | float]],
    nodata_value: int = DEFAULT_NODATA_VALUE,
    dtype: type[np.generic] = np.uint8,
) -> np.ndarray:
    """
    Rasterize labeled shapes into a uint8 array.

    This function takes shapes that are already in pixel coordinates and
    rasterizes them into a label mask. Each pixel contains the label ID
    of the shape that covers it, with 0 for background pixels.

    Args:
        width: Width of the output raster in pixels
        height: Height of the output raster in pixels
        shape_labels: Sequence of (geometry, label) tuples where geometries are in pixel coordinates
        nodata_value: Value to use for nodata pixels
        dtype: Data type of the output array

    Returns:
        uint8 numpy array with rasterized labels

    Note:
        - Geometries should already be in pixel coordinates (not WGS84)
        - Background pixels get NODATA_VALUE (255)
        - For overlapping shapes, the last one processed wins
    """
    if not shape_labels:
        # Return nodata raster if no annotations
        return np.full((height, width), nodata_value, dtype=np.uint8)

    # Generate the raster mask using rasterio
    # rasterio.features.rasterize expects shapes in pixel coordinates
    label_mask = rasterio.features.rasterize(
        shape_labels, out_shape=(height, width), fill=nodata_value, dtype=dtype
    )

    return label_mask


def transform_geometries_to_pixel_coordinates(
    geometries: Sequence[tuple[BaseGeometry, int | float]],
    window_bounds: tuple[int, int, int, int],
) -> list[tuple[BaseGeometry, int | float]]:
    """
    Transform geometries from world coordinates to pixel coordinates.

    This function translates geometries so they can be used with
    rasterize_shapes_to_mask. It's useful for converting from
    projected coordinate systems (like UTM) to pixel space.

    Args:
        geometries: Sequence of (geometry, label) tuples in world coordinates
        window_bounds: Window bounds as (minx, miny, maxx, maxy) in world coordinates

    Returns:
        List of (geometry, label) tuples in pixel coordinates

    Note:
        - This performs a simple translation: subtract minx, miny from all coordinates
        - The result is suitable for rasterize_shapes_to_mask
    """
    pixel_shapes = []
    for geometry, label_id in geometries:
        # Simple translation to pixel coordinates
        transformed_shape = translate(geometry, -window_bounds[0], -window_bounds[1])
        pixel_shapes.append((transformed_shape, label_id))

    return pixel_shapes

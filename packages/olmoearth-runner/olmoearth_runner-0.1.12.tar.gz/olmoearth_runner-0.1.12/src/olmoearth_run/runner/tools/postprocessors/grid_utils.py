from typing import Callable, TypeVar
from shapely.geometry import Polygon  #type: ignore[import-untyped]


T = TypeVar('T')


def group_polygons_by_grid(
    items: list[T],
    max_size: float,
    get_geometry: Callable[[T], Polygon]
) -> dict[tuple[int, int], list[T]]:
    """
    Group items with geometries into grid cells of maximum size.

    Each item is assigned to a grid cell based on its geometry's centroid.
    Grid cells are max_size x max_size in the coordinate system.

    Args:
        items: List of items (each must have a geometry accessible via get_geometry)
        max_size: Maximum width/height of each grid cell in coordinate units
        get_geometry: Function to extract Polygon from each item

    Returns:
        Dictionary mapping (grid_x, grid_y) to list of items in that cell
    """
    if not items:
        return {}

    # Find overall bounds to establish grid origin
    all_bounds = [get_geometry(item).bounds for item in items]
    min_x = min(b[0] for b in all_bounds)
    min_y = min(b[1] for b in all_bounds)

    # Group items by grid cell (based on centroid)
    from collections import defaultdict
    groups: dict[tuple[int, int], list[T]] = defaultdict(list)
    for item in items:
        geom = get_geometry(item)
        centroid = geom.centroid
        grid_x = int((centroid.x - min_x) // max_size)
        grid_y = int((centroid.y - min_y) // max_size)

        key = (grid_x, grid_y)
        groups[key].append(item)

    return groups

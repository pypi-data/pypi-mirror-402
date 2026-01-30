from typing import cast

from shapely.geometry import shape, MultiPolygon as ShapelyMultiPolygon, Polygon as ShapelyPolygon
from shapely.ops import unary_union

# Pydantic v2
from geojson_pydantic import FeatureCollection
from geojson_pydantic.geometries import Polygon, MultiPolygon

def fc_to_multipolygon(fc: FeatureCollection) -> ShapelyMultiPolygon:
    """
    Convert a geojson-pydantic FeatureCollection of Polygon/MultiPolygon
    features into a single Shapely MultiPolygon.
    """
    polys: list[ShapelyPolygon] = []

    for f in fc.features:
        if f.geometry is None:
            continue

        # Accept Polygon or MultiPolygon (skip anything else)
        if not isinstance(f.geometry, (Polygon, MultiPolygon)):
            continue

        # shapely.shape expects a GeoJSON-like dict
        geom = shape(f.geometry.model_dump())

        # Normalize to polygons
        if geom.geom_type == "Polygon":
            polys.append(geom)  # type: ignore[arg-type]
        elif geom.geom_type == "MultiPolygon":
            assert isinstance(geom, ShapelyMultiPolygon)
            polys.extend(list(geom.geoms))  # type: ignore[assignment]

    if not polys:
        return ShapelyMultiPolygon([])

    # We want to dissolve touching/overlapping polygons into pieces so we use unary_union and
    # normalize the result back to MultiPolygon.
    dissolved = unary_union(polys)
    if dissolved.geom_type == "Polygon":
        assert isinstance(dissolved, ShapelyPolygon)
        return ShapelyMultiPolygon([dissolved])
    elif dissolved.geom_type == "MultiPolygon":
        assert isinstance(dissolved, ShapelyMultiPolygon)
        return cast(ShapelyMultiPolygon, dissolved)
    else:
        # (e.g., GeometryCollection containing polygons)
        return ShapelyMultiPolygon([g for g in getattr(dissolved, "geoms", []) if g.geom_type == "Polygon"])

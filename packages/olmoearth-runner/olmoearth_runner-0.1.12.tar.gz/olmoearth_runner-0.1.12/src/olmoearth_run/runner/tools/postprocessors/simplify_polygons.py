from geojson_pydantic import Feature, FeatureCollection, Polygon
from shapely.geometry import mapping, shape

from olmoearth_shared.api.run.prediction_geometry import PredictionResultCollection, PredictionResultFeature
from olmoearth_run.runner.tools.postprocessors.postprocess_interface import PostprocessInterfaceVector


class SimplifyPolygons(PostprocessInterfaceVector):
    def __init__(self, tolerance: float = 0.01, preserve_topology: bool = True):
        """
        Initialize the SimplifyPolygons postprocessor.

        :param tolerance: The simplification tolerance. Higher values result in more simplification.
        :param preserve_topology: If True, ensures that the simplified geometry remains valid.
        """
        self.tolerance = tolerance
        self.preserve_topology = preserve_topology

    def process_partition(self, all_window_results: list[PredictionResultCollection]) -> PredictionResultCollection:
        simplified_features: list[PredictionResultFeature] = []

        for collection in all_window_results:
            for feature in collection.features:
                if feature.geometry is not None and feature.geometry.type in ["Polygon", "MultiPolygon"]:
                    # Convert GeoJSON to Shapely geometry
                    geom = shape(feature.geometry)

                    # Apply simplification
                    simplified_geom = geom.simplify(self.tolerance, preserve_topology=self.preserve_topology)

                    # Skip if geometry becomes invalid or empty
                    if simplified_geom.is_empty or not simplified_geom.is_valid:
                        continue

                    # Create new feature with simplified geometry
                    simplified_feature: PredictionResultFeature = Feature(
                        type="Feature",
                        geometry=Polygon.model_validate(mapping(simplified_geom)),
                        properties=feature.properties
                    )

                    simplified_features.append(simplified_feature)
                else:
                    # Pass through non-polygon features unchanged
                    simplified_features.append(feature)

        return FeatureCollection(type="FeatureCollection", features=simplified_features)

from typing import Literal

from geojson_pydantic import Feature, FeatureCollection

from olmoearth_shared.api.run.prediction_geometry import (
    PredictionRequestFeature,
    PredictionResultCollection,
    PredictionResultFeature,
    PredictionResultProperties,
)
from olmoearth_run.runner.tools.postprocessors.postprocess_interface import PostprocessInterfaceVector


class CombineGeojson(PostprocessInterfaceVector):
    """
    Postprocessor that combines request and result features with configurable geometry and properties sources.

    Args:
        geometry_source: Which geometry to use in the result. Options:
            - "request": Use the geometry from the request window (default)
            - "result": Use the geometry from the result feature
        include_request_properties: If True, merge properties from both request and result,
            with result properties taking precedence. If False, use only result properties (default: True).
    """

    def __init__(
        self,
        geometry_source: Literal["request", "result"] = "request",
        include_request_properties: bool = True,
    ):
        self.geometry_source = geometry_source
        self.include_request_properties = include_request_properties

    def process_window(self, window_request: PredictionRequestFeature, window_result: PredictionResultCollection) -> PredictionResultCollection:
        combined_features: list[PredictionResultFeature] = []

        for result_feature in window_result.features:
            if self.geometry_source == "request":
                geometry = window_request.geometry
            elif self.geometry_source == "result":
                geometry = result_feature.geometry
            else:
                raise ValueError(f"Invalid geometry_source: {self.geometry_source}. Must be 'request' or 'result'.")

            properties: PredictionResultProperties | None
            if self.include_request_properties:
                properties_dict = window_request.properties.model_dump() if window_request.properties else {}
                result_properties_dict = result_feature.properties.model_dump() if result_feature.properties else {}
                # On conflict, the result properties take precedence.
                properties_dict.update({k: v for k, v in result_properties_dict.items() if v is not None})
                properties = PredictionResultProperties(**properties_dict)
            else:
                properties = result_feature.properties

            combined_features.append(Feature(type="Feature", properties=properties, geometry=geometry))

        return FeatureCollection(
            type="FeatureCollection",
            features=combined_features
        )

    def process_partition(self, partition_window_results: list[PredictionResultCollection]) -> PredictionResultCollection:
        return self._combine_features(partition_window_results)

    def process_dataset(self, all_partitions_results: list[PredictionResultCollection]) -> PredictionResultCollection:
        return self._combine_features(all_partitions_results)

    def _combine_features(self, features: list[PredictionResultCollection]) -> PredictionResultCollection:
        combined_features: list[PredictionResultFeature] = []
        for partition_results in features:
            combined_features.extend(partition_results.features)
        return FeatureCollection(type="FeatureCollection", features=combined_features)

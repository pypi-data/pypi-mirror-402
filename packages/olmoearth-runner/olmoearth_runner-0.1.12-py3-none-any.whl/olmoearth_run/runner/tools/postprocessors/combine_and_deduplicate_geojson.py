from geojson_pydantic import FeatureCollection
from shapely.geometry import shape

from olmoearth_shared.api.run.prediction_geometry import PredictionResultCollection
from olmoearth_run.runner.tools.postprocessors.postprocess_interface import PostprocessInterfaceVector


class CombineAndDeduplicateGeojson(PostprocessInterfaceVector):
    def __init__(self, min_iou: float = 0.9, point_nearness: float = 0.001) -> None:
        """
        :param min_iou: Minimum Intersection over Union (IoU) threshold for deduplication.
        :param point_nearness: Distance threshold for considering points as duplicates.
        """
        self.min_iou = min_iou
        self.point_nearness = point_nearness

    def process_partition(self, all_window_results: list[PredictionResultCollection]) -> PredictionResultCollection:
        # Combine all features
        all_features = []
        for collection in all_window_results:
            all_features.extend(collection.features)

        unique_features = []
        processed_indices = set()

        for i, feature in enumerate(all_features):
            if i in processed_indices:
                continue
            if not feature.geometry:
                continue

            geom = shape(feature.geometry.model_dump())
            geom_type = feature.geometry.type

            # Find duplicates for this feature
            duplicates = [i]

            for j, other_feature in enumerate(all_features[i + 1 :], i + 1):
                if j in processed_indices:
                    continue
                if not other_feature.geometry:
                    continue

                other_geom = shape(other_feature.geometry.model_dump())
                other_type = other_feature.geometry.type

                is_duplicate = False

                # Check polygon duplicates using IoU
                if geom_type in ["Polygon", "MultiPolygon"] and other_type in ["Polygon", "MultiPolygon"]:
                    if geom.is_valid and other_geom.is_valid:
                        intersection_area = geom.intersection(other_geom).area
                        union_area = geom.union(other_geom).area

                        if union_area > 0:
                            iou = intersection_area / union_area
                            if iou >= self.min_iou:
                                is_duplicate = True

                # Check point duplicates using distance
                elif geom_type == "Point" and other_type == "Point":
                    distance = geom.distance(other_geom)
                    if distance <= self.point_nearness:
                        is_duplicate = True

                # Check other geometry types for exact matches
                elif geom_type == other_type:
                    if geom.equals(other_geom):
                        is_duplicate = True

                if is_duplicate:
                    duplicates.append(j)

            # Keep the first occurrence, mark others as processed
            unique_features.append(feature)
            processed_indices.update(duplicates)

        return FeatureCollection(type="FeatureCollection", features=unique_features)

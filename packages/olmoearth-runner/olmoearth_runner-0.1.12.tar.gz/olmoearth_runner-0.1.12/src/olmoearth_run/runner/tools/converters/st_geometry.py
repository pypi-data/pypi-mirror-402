import logging

from rslearn.utils import STGeometry
from rslearn.utils.geometry import WGS84_PROJECTION
from shapely.geometry import shape

from olmoearth_shared.api.run.prediction_geometry import PredictionRequestCollection, PredictionRequestFeature

logger = logging.getLogger(__name__)


class STGeometryConverter:
    @staticmethod
    def from_prediction_request_geometry(feature_collection: PredictionRequestCollection) -> list[STGeometry]:
        return [
            STGeometryConverter.from_prediction_request_feature(feature)
            for feature in feature_collection.features
        ]

    @staticmethod
    def from_prediction_request_feature(feature: PredictionRequestFeature) -> STGeometry:
        if feature.geometry is None or feature.properties is None:
            raise ValueError(f"cannot convert invalid feature to STGeometry: {feature.model_dump(mode='json')}")
        if feature.properties.oe_start_time and feature.properties.oe_end_time:
            time_range = (feature.properties.oe_start_time, feature.properties.oe_end_time)
        else:
            time_range = None

        return STGeometry(projection=WGS84_PROJECTION, shp=shape(feature.geometry), time_range=time_range)

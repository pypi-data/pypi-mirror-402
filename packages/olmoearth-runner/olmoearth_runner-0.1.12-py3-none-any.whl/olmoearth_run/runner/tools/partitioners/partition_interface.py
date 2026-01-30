import logging
from typing import cast

from rslearn.utils import Projection, STGeometry, get_utm_ups_crs
from rslearn.utils.geometry import WGS84_PROJECTION
from shapely.geometry.base import BaseGeometry

from olmoearth_shared.api.run.prediction_geometry import PredictionRequestCollection, PredictionRequestFeature

logger = logging.getLogger(__name__)


class PartitionInterface:
    """
    A Partitioner is responsible for taking one or more input Geometries and splitting them up into another set of
    (typically smaller) partitions.   This is used in two places during inference:
    1. First to take the user-provided input geometries and split them into partitions that we can hand out to
       different compute nodes for processing.  The number of partitions created determines the maximum concurrency
       of inference.
    2. Second on each compute node; we will take the input partitions and further split them down into
       (typically smaller) windows that we will actually run inference on.  This second step can be optimized
       for whatever the model works best on.
    """

    def __init__(self, output_projection: Projection | None = None, use_utm: bool = False):
        self.output_projection = output_projection if output_projection else WGS84_PROJECTION
        self.use_utm = use_utm

    def partition_request_geometry(self, request_extents: PredictionRequestCollection) -> list[PredictionRequestCollection]:
        """
        Implement this method to describe the specific methodology to partition the input Feature Collection into groups for processing.
        """
        raise NotImplementedError

    def prepare_window_geometries(self, request_extents: PredictionRequestCollection) -> list[tuple[PredictionRequestFeature, STGeometry]]:
        """
        Implement this method to describe the specific methodology to partition input geometries.
        """
        raise NotImplementedError

    def _convert_to_utm(self, geometry: STGeometry) -> STGeometry:
        logger.debug(f"Converting {geometry} to UTM.")
        wgs84_geom = geometry.to_projection(WGS84_PROJECTION)
        wgs84_point = cast(BaseGeometry, wgs84_geom.shp).centroid
        utm_crs = get_utm_ups_crs(wgs84_point.x, wgs84_point.y)
        utm_projection = Projection(utm_crs, self.output_projection.x_resolution, self.output_projection.y_resolution)
        return geometry.to_projection(utm_projection)

    def _update_projection(self, geometry: STGeometry) -> STGeometry:
        if self.use_utm:
            return self._convert_to_utm(geometry)
        else:
            return geometry.to_projection(self.output_projection)

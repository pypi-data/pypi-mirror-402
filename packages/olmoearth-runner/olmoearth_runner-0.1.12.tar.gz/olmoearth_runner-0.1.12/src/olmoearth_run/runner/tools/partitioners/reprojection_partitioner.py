"""
Partitioner that just re-projects request geometries from WGS84 (lat/lng) into pixel coordinates.
"""
from rslearn.utils import Projection, STGeometry

from olmoearth_run.runner.tools.converters.st_geometry import STGeometryConverter
from olmoearth_run.runner.tools.partitioners.partition_interface import PartitionInterface
from olmoearth_shared.api.run.prediction_geometry import PredictionRequestCollection, PredictionRequestFeature


class ReprojectionPartitioner(PartitionInterface):
    def __init__(self, output_projection: Projection | None = None, use_utm: bool = False):
        super().__init__(output_projection, use_utm)

    def partition_request_geometry(self, request_extents: PredictionRequestCollection) -> list[PredictionRequestCollection]:
        """Request Partitions need to stay in WGS84, so it doesn't make sense to reproject them"""
        raise NotImplementedError("ReprojectionPartitioner does not support partitioning request_geometries")

    def prepare_window_geometries(self, request_extents: PredictionRequestCollection) -> list[tuple[PredictionRequestFeature, STGeometry]]:
        """For each input geometry, re-project it into the output projection."""
        partitions: list[tuple[PredictionRequestFeature, STGeometry]] = []

        for feature in request_extents.features:
            geometry = STGeometryConverter.from_prediction_request_feature(feature)
            # Update projection
            reproj_geom = self._update_projection(geometry)
            partitions.append((feature, reproj_geom))

        return partitions

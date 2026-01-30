from typing import cast

from rslearn.utils import Projection, STGeometry
from shapely.geometry import box as shapely_box
from shapely.geometry.base import BaseGeometry

from olmoearth_shared.api.run.prediction_geometry import PredictionRequestCollection, PredictionRequestFeature
from olmoearth_run.runner.tools.converters.st_geometry import STGeometryConverter
from olmoearth_run.runner.tools.partitioners.partition_interface import PartitionInterface


class FixedWindowPartitioner(PartitionInterface):
    def __init__(self, window_size: float, output_projection: Projection | None = None, use_utm: bool = False):
        super().__init__(output_projection, use_utm)
        self.window_size = window_size

    def partition_request_geometry(self, request_extents: PredictionRequestCollection) -> list[PredictionRequestCollection]:
        raise NotImplementedError("FixedWindowPartitioner does not support partitioning request_geometries")

    def prepare_window_geometries(self, request_extents: PredictionRequestCollection) -> list[tuple[PredictionRequestFeature, STGeometry]]:
        """Given the input geometries, create fixed-size windows centered at each geometry's centroid.
           Each feature is assigned to a single window, which finds the centroid of the geometry."""
        partitions: list[tuple[PredictionRequestFeature, STGeometry]] = []

        for feature in request_extents.features:
            geometry = STGeometryConverter.from_prediction_request_feature(feature)
            # Update projection if needed
            working_geometry = self._update_projection(geometry)

            # Get the centroid of the geometry
            shp = cast(BaseGeometry, working_geometry.shp)
            centroid = shp.centroid

            # Create a fixed-size box centered at the centroid
            half_size = self.window_size / 2
            chunk_shp = shapely_box(centroid.x - half_size, centroid.y - half_size, centroid.x + half_size, centroid.y + half_size)

            st_geometry = STGeometry(working_geometry.projection, chunk_shp, working_geometry.time_range)
            partitions.append((feature, st_geometry))

        return partitions

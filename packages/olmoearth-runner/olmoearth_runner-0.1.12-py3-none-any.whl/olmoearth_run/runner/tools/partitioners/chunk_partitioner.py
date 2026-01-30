import logging

from rslearn.utils import Projection, STGeometry

from olmoearth_shared.api.run.prediction_geometry import PredictionRequestCollection, PredictionRequestFeature
from olmoearth_run.runner.tools.converters.st_geometry import STGeometryConverter
from olmoearth_run.runner.tools.partitioners.partition_interface import PartitionInterface

logger = logging.getLogger(__name__)


class ChunkPartitioner(PartitionInterface):
    """ChunkPartitioner chunks the request geometries into partitions.

    It assigns up to a configured number of geometries to each partition; the last
    partition may have fewer geometries. The request geometries are not modified when
    chunked into the partitions.
    """

    def __init__(self, num_geometries_per_partition: int, output_projection: Projection | None = None, use_utm: bool = False):
        super().__init__(output_projection, use_utm)
        self.num_geometries_per_partition = num_geometries_per_partition

    def partition_request_geometry(self, request_extents: PredictionRequestCollection) -> list[PredictionRequestCollection]:
        """Chunk the request geometries into partitions.

        One partition is created for each chunk of num_geometries_per_partition
        features in request_extents.
        """

        # Filter out None geometries.
        valid_features = [f for f in request_extents.features if f.geometry is not None]
        if not valid_features:
            return []
        logger.info(f"Creating partitions for {len(valid_features)} input features.")

        partitions: list[PredictionRequestCollection] = []
        for batch_start_idx in range(0, len(valid_features), self.num_geometries_per_partition):
            batch = valid_features[batch_start_idx:batch_start_idx+self.num_geometries_per_partition]
            partitions.append(
                PredictionRequestCollection(
                    type="FeatureCollection",
                    features=batch,
                )
            )

        return partitions

    def prepare_window_geometries(self, request_extents: PredictionRequestCollection) -> list[tuple[PredictionRequestFeature, STGeometry]]:
        """For each geometry, create a window corresponding to the geometry's bounds."""
        partitions: list[tuple[PredictionRequestFeature, STGeometry]] = []

        for feature in request_extents.features:
            geometry = STGeometryConverter.from_prediction_request_feature(feature)
            working_geometry = self._update_projection(geometry)
            partitions.append((feature, working_geometry))

        return partitions

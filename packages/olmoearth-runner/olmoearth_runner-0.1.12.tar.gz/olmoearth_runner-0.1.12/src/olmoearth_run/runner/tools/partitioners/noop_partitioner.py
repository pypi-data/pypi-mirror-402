from rslearn.utils import STGeometry

from olmoearth_shared.api.run.prediction_geometry import PredictionRequestCollection, PredictionRequestFeature
from olmoearth_run.runner.tools.partitioners.partition_interface import PartitionInterface


class NoopPartitioner(PartitionInterface):
    def partition_request_geometry(self, request_extents: PredictionRequestCollection) -> list[PredictionRequestCollection]:
        """Returns the input extent as a single partition without any modifications."""
        return [request_extents] if request_extents.features else []

    def prepare_window_geometries(self, request_extents: PredictionRequestCollection) -> list[tuple[PredictionRequestFeature, STGeometry]]:
        """
        When going from a partition -> windows you must re-project the data, so it doesn't make sense to use the NoopPartitioner here.
        """
        raise NotImplementedError("Noop Partitioner cannot prepare window geometries")

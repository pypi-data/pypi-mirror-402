from upath import UPath

from olmoearth_shared.api.run.prediction_geometry import PredictionRequestFeature
from olmoearth_run.runner.tools.postprocessors.postprocess_interface import PostprocessInterfaceRaster


class NoopRaster(PostprocessInterfaceRaster):
    def process_window(self, window_request: PredictionRequestFeature, window_result_path: UPath) -> None:
        pass

    def process_partition(self, partition_window_results: list[UPath], output_dir: UPath) -> list[UPath]:
        return []

    def process_dataset(self, all_partitions_result_paths: list[UPath], output_dir: UPath) -> list[UPath]:
        return []

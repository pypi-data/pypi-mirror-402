import logging
from typing import cast

from upath import UPath

from olmoearth_run.shared.models.olmoearth_run_config import OlmoEarthRunConfig
from olmoearth_run.shared.models.model_stage_paths import ModelStagePaths
from olmoearth_shared.api.run.prediction_geometry import PredictionResultCollection
from olmoearth_run.shared.models.prediction_scratch_space import PredictionScratchSpace
from olmoearth_run.shared.models.api.task_args import CombinePartitionsTaskArgs
from olmoearth_run.shared.models.api.task_results import CombinePartitionsTaskResults, InferenceResultsDataType
from olmoearth_run.runner.steps.base_step_definition import BaseStepDefinition
from olmoearth_run.runner.tools.olmoearth_run_config_loader import OlmoEarthRunConfigLoader
from olmoearth_run.runner.tools.postprocessors.postprocess_interface import PostprocessInterfaceRaster, PostprocessInterfaceVector

logger = logging.getLogger(__name__)


class CombinePartitionsStepDefinition(BaseStepDefinition[CombinePartitionsTaskArgs, CombinePartitionsTaskResults]):
    scratch: PredictionScratchSpace
    olmoearth_run_config: OlmoEarthRunConfig

    def run(self, task_args: CombinePartitionsTaskArgs) -> CombinePartitionsTaskResults:
        self.scratch = PredictionScratchSpace(root_path=task_args.scratch_path)
        model_stage_paths = ModelStagePaths(root_path=task_args.model_stage_root_path)
        UPath(model_stage_paths.root_path).mkdir(parents=True, exist_ok=True)
        self.olmoearth_run_config = OlmoEarthRunConfigLoader.load_olmoearth_run_config(model_stage_paths.olmoearth_run_config_path)

        if self.olmoearth_run_config.inference_results_config.data_type == InferenceResultsDataType.VECTOR:
            return self._combine_vector(task_args)
        return self._combine_raster(task_args)

    def _combine_raster(self, task_args: CombinePartitionsTaskArgs) -> CombinePartitionsTaskResults:
        logger.debug(f"Combining raster partitions: {task_args.partition_ids} args: {task_args}")
        postprocessor = cast(PostprocessInterfaceRaster, OlmoEarthRunConfigLoader.get_dataset_postprocessor(self.olmoearth_run_config))

        # The scratch space keeps track of partition directories.
        # But partition processors can write one or multiple GeoTIFFs under that directory.
        # So we have to scan the contents across the directories.
        partition_result_paths: list[UPath] = []
        for partition_id in task_args.partition_ids:
            partition_result_dir = self.scratch.get_partition_result_raster_dir(partition_id)
            if not partition_result_dir.exists():
                continue
            partition_result_paths.extend(partition_result_dir.iterdir())

        prediction_result_raster_dir = UPath(self.scratch.prediction_result_raster_dir)
        prediction_result_raster_dir.mkdir(parents=True, exist_ok=True)
        saved_raster_paths = postprocessor.process_dataset(partition_result_paths, prediction_result_raster_dir)

        return CombinePartitionsTaskResults(generated_file_paths=[str(raster_path) for raster_path in saved_raster_paths])

    def _combine_vector(self, task_args: CombinePartitionsTaskArgs) -> CombinePartitionsTaskResults:
        logger.debug(f"Combining vector partitions: {task_args.partition_ids} args: {task_args}")
        postprocessor = cast(PostprocessInterfaceVector, OlmoEarthRunConfigLoader.get_dataset_postprocessor(self.olmoearth_run_config))

        partition_results: list[PredictionResultCollection] = []
        partition_result_paths = [self.scratch.get_partition_result_vector_path(partition_id) for partition_id in task_args.partition_ids]
        for partition_result_path in partition_result_paths:
            partition_result_json = UPath(partition_result_path).read_text()
            partition_result = PredictionResultCollection.model_validate_json(partition_result_json)
            partition_results.append(partition_result)

        combined_result = postprocessor.process_dataset(partition_results)
        self.scratch.write_prediction_result_vector(combined_result)
        return CombinePartitionsTaskResults(generated_file_paths=[self.scratch.prediction_result_vector_path])

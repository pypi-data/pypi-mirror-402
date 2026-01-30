import logging
from multiprocessing import Pool
from typing import cast

from rslearn.dataset import Dataset, Window
from upath import UPath

from olmoearth_run.config import OlmoEarthSettings
from olmoearth_run.shared.models.olmoearth_run_config import OlmoEarthRunConfig
from olmoearth_run.shared.models.model_stage_paths import ModelStagePaths
from olmoearth_shared.api.run.prediction_geometry import PredictionResultCollection
from olmoearth_run.shared.models.prediction_scratch_space import PredictionScratchSpace, WINDOW_OUTPUT_LAYER_NAME
from olmoearth_run.shared.models.api.task_args import PostprocessPartitionTaskArgs
from olmoearth_run.shared.models.api.task_results import InferenceResultsDataType, PostprocessPartitionTaskResults
from olmoearth_run.runner.steps.base_step_definition import BaseStepDefinition
from olmoearth_run.runner.tools.olmoearth_run_config_loader import OlmoEarthRunConfigLoader
from olmoearth_run.runner.tools.postprocessors.postprocess_interface import PostprocessInterfaceRaster, PostprocessInterfaceVector

logger = logging.getLogger(__name__)


class PostprocessPartitionStepDefinition(BaseStepDefinition[PostprocessPartitionTaskArgs, PostprocessPartitionTaskResults]):
    scratch: PredictionScratchSpace
    olmoearth_run_config: OlmoEarthRunConfig

    def run(self, task_args: PostprocessPartitionTaskArgs) -> PostprocessPartitionTaskResults:
        self.scratch = PredictionScratchSpace(root_path=task_args.scratch_path)
        model_stage_paths = ModelStagePaths(root_path=task_args.model_stage_root_path)

        dataset = Dataset(UPath(task_args.dataset_path))

        self.olmoearth_run_config = OlmoEarthRunConfigLoader.load_olmoearth_run_config(model_stage_paths.olmoearth_run_config_path)
        result_data_type = self.olmoearth_run_config.inference_results_config.data_type

        output_files: list[UPath] = []
        for partition_id in task_args.partition_ids:
            rslearn_groups = [self.scratch.get_group(partition_id)]
            logger.debug(f"Loading windows for partition {partition_id} with groups {rslearn_groups}")
            windows = dataset.storage.get_windows(groups=rslearn_groups)
            if result_data_type == InferenceResultsDataType.VECTOR:
                output_files.extend(self._postprocess_vector(partition_id, windows))
            else:
                output_files.extend(self._postprocess_raster(partition_id, windows))

        return PostprocessPartitionTaskResults(
            partition_ids=task_args.partition_ids,
            output_files=[str(f) for f in output_files],
            inference_results_data_type=result_data_type,
        )

    def _postprocess_raster(self, partition_id: str, windows: list[Window]) -> list[UPath]:
        window_postprocessor = cast(PostprocessInterfaceRaster, OlmoEarthRunConfigLoader.get_window_postprocessor(self.olmoearth_run_config))

        partition_result_raster_dir = self.scratch.get_partition_result_raster_dir(partition_id)
        window_group = self.scratch.get_group(partition_id)
        window_output_paths: list[UPath] = []
        for window in windows:
            window_output_path = self.scratch.get_window_prediction_result_geotiff_path(window.get_layer_dir(WINDOW_OUTPUT_LAYER_NAME))
            window_root = window.storage.get_window_root(window_group, window.name)
            request_feature = self.scratch.get_window_request_feature(window_root)
            window_postprocessor.process_window(request_feature, window_output_path)
            window_output_paths.append(window_output_path)

        # Prepare arguments for parallel processing
        process_args = [
            (window, self.scratch.root_path, window_postprocessor, partition_id)
            for window in windows
        ]

        logger.debug(f"Postprocessing raster partition {partition_id} with {len(windows)} windows using {window_postprocessor}")
        # Use multiprocessing to process windows in parallel
        with Pool(processes=OlmoEarthSettings.NUM_WORKERS) as pool:
            window_output_paths = pool.starmap(_process_raster_window, process_args)

        partition_postprocessor = cast(PostprocessInterfaceRaster, OlmoEarthRunConfigLoader.get_partition_postprocessor(self.olmoearth_run_config))
        logger.debug(f"Postprocessing raster partition {partition_id} using {partition_postprocessor}")
        partition_result_raster_dir.mkdir(parents=True, exist_ok=True)
        saved_raster_paths = partition_postprocessor.process_partition(window_output_paths, partition_result_raster_dir)

        return saved_raster_paths

    def _postprocess_vector(self, partition_id: str, windows: list[Window]) -> list[UPath]:
        window_postprocessor = cast(PostprocessInterfaceVector, OlmoEarthRunConfigLoader.get_window_postprocessor(self.olmoearth_run_config))

        # Prepare arguments for parallel processing
        process_args = [
            (window, self.scratch.root_path, window_postprocessor, partition_id)
            for window in windows
        ]

        logger.debug(f"Postprocessing vector partition {partition_id} with {len(windows)} windows using {window_postprocessor}")
        # Use multiprocessing to process windows in parallel
        with Pool(processes=OlmoEarthSettings.NUM_WORKERS) as pool:
            window_results = pool.starmap(_process_vector_window, process_args)

        # Filter out None results (windows with no output)
        all_window_results = [result for result in window_results if result is not None]

        # Combine all window results to produce a single result for the partition
        partition_postprocessor = cast(PostprocessInterfaceVector, OlmoEarthRunConfigLoader.get_partition_postprocessor(self.olmoearth_run_config))
        logger.debug(f"Postprocessing vector partition {partition_id} using {partition_postprocessor}")
        partition_result = partition_postprocessor.process_partition(all_window_results)
        self.scratch.write_partition_result_vector(partition_id, partition_result)

        return [self.scratch.get_partition_result_vector_path(partition_id)]


def _process_raster_window(window: Window, scratch_path: str, window_postprocessor: PostprocessInterfaceRaster, partition_id: str) -> UPath:
    scratch = PredictionScratchSpace(root_path=scratch_path)

    # this path is dictated by the RslearnWriter configuration in RunInferenceStepDefinition
    window_output_path = scratch.get_window_prediction_result_geotiff_path(window.get_layer_dir(WINDOW_OUTPUT_LAYER_NAME))

    # retrieve the GeoJSON Feature from which the window was derived
    window_group = scratch.get_group(partition_id)
    window_root = window.storage.get_window_root(window_group, window.name)
    request_feature = scratch.get_window_request_feature(window_root)

    logger.debug(f"Postprocessing raster window {window.name} with output path {window_output_path}")
    # the postprocessor updates the geotiff in place
    window_postprocessor.process_window(request_feature, window_output_path)
    return window_output_path


def _process_vector_window(window: Window, scratch_path: str, window_postprocessor: PostprocessInterfaceVector, partition_id: str) -> PredictionResultCollection | None:
    scratch = PredictionScratchSpace(root_path=scratch_path)

    # retrieve the inference result GeoJSON FeatureCollection
    output = scratch.get_window_prediction_result_collection(window.get_layer_dir('output'))
    if output is None:
        logger.warning(f"no output generated for window {window.name}")
        return None

    # retrieve the GeoJSON Feature from which the window was derived
    window_group = scratch.get_group(partition_id)
    window_root = window.storage.get_window_root(window_group, window.name)
    request_feature = scratch.get_window_request_feature(window_root)

    # generate a complete result for the window, derived from combining the request feature and the output
    window_result = window_postprocessor.process_window(request_feature, output)

    # writing each result to the Window isn't necessary, but it's a helpful artifact
    scratch.write_window_result_vector(window_root, window_result)

    return window_result

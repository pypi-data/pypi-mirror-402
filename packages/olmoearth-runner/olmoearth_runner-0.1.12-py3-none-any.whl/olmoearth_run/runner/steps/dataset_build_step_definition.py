import logging
import multiprocessing
import os
from concurrent.futures import ThreadPoolExecutor

from rslearn.dataset import Dataset, Window
from rslearn.dataset.storage.file import FileWindowStorage, load_window
from upath import UPath

from olmoearth_run.config import OlmoEarthSettings
from olmoearth_run.runner.steps.base_step_definition import BaseStepDefinition
from olmoearth_run.runner.tools.dataset_builder import DatasetBuilder
from olmoearth_run.shared.models.prediction_scratch_space import PredictionScratchSpace
from olmoearth_run.shared.models.api.step_type import StepType
from olmoearth_run.shared.models.api.task_args import DatasetBuildTaskArgs
from olmoearth_run.shared.models.api.task_results import DatasetBuildTaskResults

logger = logging.getLogger(__name__)

multiprocessing.set_start_method("forkserver", force=True)


class DatasetBuildStepDefinition(BaseStepDefinition[DatasetBuildTaskArgs, DatasetBuildTaskResults]):
    def run(self, task_args: DatasetBuildTaskArgs) -> DatasetBuildTaskResults:
        logger.info(f"Running dataset build step for {len(task_args.partition_ids)} partitions")
        scratch = PredictionScratchSpace(root_path=task_args.scratch_path)

        # Get windows for partition
        dataset = Dataset(UPath(task_args.dataset_path))
        # Dataset building is a very IO intensive task, so we can have more workers than CPU cores
        builder = DatasetBuilder(
            dataset=dataset,
            num_workers=(os.cpu_count() or 1) * OlmoEarthSettings.DATASET_BUILD_WORKERS_PER_CPU,
            min_window_success_rate=task_args.min_window_success_rate
        )
        total_size_mb = 0.0

        for partition_id in task_args.partition_ids:
            logger.info(f"Building dataset for partition {partition_id}")
            partition_dir = UPath(task_args.dataset_path) / 'windows' / scratch.get_group(partition_id)
            window_paths = [window_dir for window_dir in partition_dir.iterdir() if window_dir.is_dir()]

            # Load windows in parallel using ThreadPoolExecutor for IO-bound operations
            with ThreadPoolExecutor() as executor:
                storage = FileWindowStorage(dataset.path)
                windows: list[Window] = list(executor.map(lambda wd: load_window(storage, wd), window_paths))

            builder.build_dataset(windows)
            total_size_mb += builder.get_partition_size_mb(str(partition_dir))

        return DatasetBuildTaskResults(
            step_type=StepType.DATASET_BUILD,
            dataset_build_path=task_args.dataset_path,
            dataset_size_mb=total_size_mb
        )

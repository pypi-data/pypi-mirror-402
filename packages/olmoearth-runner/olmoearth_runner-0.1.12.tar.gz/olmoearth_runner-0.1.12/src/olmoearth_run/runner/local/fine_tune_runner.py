import logging
import uuid
from pathlib import Path
from os import PathLike

import yaml  # type: ignore[import-untyped]

from olmoearth_run.runner.steps.prepare_labeled_windows_step_definition import PrepareLabeledWindowsStepDefinition
from olmoearth_run.shared.models.olmoearth_run_config import (
    OlmoEarthRunConfig,
    PartitionStrategiesConfig,
    PostprocessingStrategiesConfig,
    WindowPrepConfig,
    InferenceResultsConfig,
)
from olmoearth_run.shared.models.model_stage_paths import (
    ANNOTATION_FEATURES_FILE_NAME,
    ANNOTATION_TASK_FEATURES_FILE_NAME,
    DATASET_CONFIG_FILE_NAME,
    OLMOEARTH_RUN_CONFIG_FILE_NAME,
    MODEL_CONFIG_FILE_NAME,
    ModelStagePaths,
)
from olmoearth_run.shared.models.api.task_args import PrepareLabeledWindowsTaskArgs, DatasetBuildFromWindowsTaskArgs, FineTuneTaskArgs
from olmoearth_run.shared.models.api.task_results import PrepareLabeledWindowsTaskResults, InferenceResultsDataType, DatasetBuildFromWindowsTaskResults, FineTuneTaskResults
from olmoearth_run.runner.steps.dataset_build_from_windows_step_definition import DatasetBuildFromWindowsStepDefinition
from olmoearth_run.runner.steps.fine_tuning_step_definition import FineTuningStepDefinition


logger = logging.getLogger(__name__)


class OlmoEarthRunFineTuneRunner:
    def __init__(self,
        project_path: PathLike,
        scratch_path: PathLike,
    ):
        self.project_path = Path(project_path)
        self.scratch_path = Path(scratch_path)
        self.model_stage_paths = ModelStagePaths(root_path=str(self.scratch_path))
        self.dataset_path = Path(self.model_stage_paths.default_dataset_path)
        self.step_id = uuid.uuid4()

        self._setup_project_env()

    def _setup_project_env(self) -> None:
        """Set up the project environment in the scratch space by creating necessary directories and symlinks."""

        self.dataset_path.mkdir(parents=True, exist_ok=True)

        # Handle olmoearth_run config specially - read it, create WindowPrepConfig, and generate full config
        olmoearth_run_config_path = self.project_path / OLMOEARTH_RUN_CONFIG_FILE_NAME
        if not olmoearth_run_config_path.exists():
            raise FileNotFoundError(f"Required project file not found: {olmoearth_run_config_path}")

        # Read the user's olmoearth_run config (which may only contain window_prep)
        with open(olmoearth_run_config_path, 'r') as f:
            user_config_content = f.read()

        user_config_dict = yaml.safe_load(user_config_content)

        # Extract window_prep config and create WindowPrepConfig
        if 'window_prep' not in user_config_dict:
            raise ValueError("olmoearth_run.yaml must contain a 'window_prep' section for fine-tuning")

        window_prep_config = WindowPrepConfig.model_validate(user_config_dict['window_prep'])

        # Create full OlmoEarthRunConfig with defaults for partition and postprocessing strategies
        full_config = self._create_full_olmoearth_run_config(window_prep_config)

        # Write the full config to scratch directory
        scratch_olmoearth_run_path = Path(self.model_stage_paths.olmoearth_run_config_path)
        scratch_olmoearth_run_path.parent.mkdir(parents=True, exist_ok=True)
        Path(self.model_stage_paths.default_dataset_path).parent.mkdir(parents=True, exist_ok=True)
        with open(scratch_olmoearth_run_path, 'w') as f:
            yaml.dump(full_config.model_dump(mode='json'), f, default_flow_style=False)

        # Handle other files with simple symlinks
        other_files: list[tuple[Path, Path]] = [
            (self.project_path / DATASET_CONFIG_FILE_NAME, Path(self.model_stage_paths.dataset_config_path)),
            (self.project_path / DATASET_CONFIG_FILE_NAME, Path(self.model_stage_paths.dataset_config_path_in_dataset_dir)),
            (self.project_path / ANNOTATION_FEATURES_FILE_NAME, Path(self.model_stage_paths.annotation_features_path)),
            (self.project_path / ANNOTATION_TASK_FEATURES_FILE_NAME, Path(self.model_stage_paths.annotation_task_features_path)),
            (self.project_path / MODEL_CONFIG_FILE_NAME, Path(self.model_stage_paths.model_config_path)),
        ]

        for target, link in other_files:
            # Check if the target file exists and raise an error if it doesn't
            if not target.exists():
                raise FileNotFoundError(f"Required project file not found: {target}")

            if not link.exists():
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(target)

    def _create_full_olmoearth_run_config(self, window_prep_config: WindowPrepConfig) -> OlmoEarthRunConfig:
        """Create a full OlmoEarthRunConfig with default partition and postprocessing strategies."""

        # Create placeholders for non-essential config members
        partition_strategies = PartitionStrategiesConfig(
            partition_request_geometry={"class_path": "placeholder"},
            prepare_window_geometries={"class_path": "placeholder"},
        )
        postprocessing_strategies = PostprocessingStrategiesConfig(
            process_window={ "class_path": "placeholder" },
            process_partition={ "class_path": "placeholder" },
            process_dataset={ "class_path": "placeholder" }
        )

        inference_results_config = InferenceResultsConfig(
            data_type=InferenceResultsDataType.VECTOR
        )

        return OlmoEarthRunConfig(
            partition_strategies=partition_strategies,
            postprocessing_strategies=postprocessing_strategies,
            window_prep=window_prep_config,
            inference_results_config=inference_results_config,
        )

    def prepare_labeled_windows(self) -> PrepareLabeledWindowsTaskResults:
        logger.info("Preparing labeled windows")
        task_args = PrepareLabeledWindowsTaskArgs(
            dataset_path=str(self.dataset_path),
            scratch_path=str(self.scratch_path),
        )
        return PrepareLabeledWindowsStepDefinition().run(task_args)

    def build_dataset_from_windows(self) -> DatasetBuildFromWindowsTaskResults:
        logger.info("Building dataset from windows")
        task_args = DatasetBuildFromWindowsTaskArgs(
            dataset_path=str(self.dataset_path)
        )
        return DatasetBuildFromWindowsStepDefinition().run(task_args)

    def fine_tune(self) -> FineTuneTaskResults:
        logger.info("Fine tuning")
        task_args = FineTuneTaskArgs(
            dataset_path=str(self.dataset_path),
            scratch_path=str(self.scratch_path),
            step_id=self.step_id,
        )
        return FineTuningStepDefinition().run(task_args)

    def run_pipeline(self) -> None:
        logger.info("Running full fine tune pipeline")
        self.prepare_labeled_windows()
        self.build_dataset_from_windows()
        self.fine_tune()

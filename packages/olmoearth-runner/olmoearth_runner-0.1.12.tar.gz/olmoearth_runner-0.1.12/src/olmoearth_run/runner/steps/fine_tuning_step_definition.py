import logging
import tempfile
from contextlib import contextmanager
from uuid import UUID
from typing_extensions import override, Iterator

from rslearn.arg_parser import RslearnArgumentParser
from rslearn.lightning_cli import RslearnLightningCLI
from rslearn.train.data_module import RslearnDataModule
from rslearn.train.lightning_module import RslearnLightningModule
from upath import UPath
import wandb

from olmoearth_run.runner.models.operational_context import ModelOperationalContext
from olmoearth_run.runner.steps.base_step_definition import BaseStepDefinition
from olmoearth_run.runner.tools.olmoearth_config.loaders.config import ConfigClassLoader
from olmoearth_run.runner.tools.olmoearth_config.transpilers.olmoearth_to_rslearn import to_model_config_yaml
from olmoearth_run.shared.models.api.step_type import StepType
from olmoearth_run.shared.models.api.task_args import FineTuneTaskArgs
from olmoearth_run.shared.models.api.task_results import FineTuneTaskResults, WandbRunInfo
from olmoearth_run.shared.models.fine_tuning_scratch_space import FineTuningScratchSpace
from olmoearth_run.shared.models.model_stage_paths import ModelStagePaths, TRAINER_LAST_CHECKPOINT_FILE_NAME
from olmoearth_run.shared.models.rslearn_template_vars import RslearnTemplateVars
from olmoearth_run.config import OlmoEarthSettings
from olmoearth_shared.tools.gcs_tools import copy_files_from_gcs_directory, is_gcs_path

logger = logging.getLogger(__name__)


# TODOs:
# 1. Get performance metrics for the best checkpoint out of this step.
# 2. Add a trainer callback that emits progress signal to orchestrator.

class FineTuningStepDefinition(BaseStepDefinition[FineTuneTaskArgs, FineTuneTaskResults]):
    @override
    def run(self, task_args: FineTuneTaskArgs) -> FineTuneTaskResults:
        """Execute the fine tuning step."""
        logger.info("Starting fine tuning step")

        scratch_space = FineTuningScratchSpace(root_path=task_args.scratch_path)
        model_stage_paths = scratch_space.model_stage_paths
        wandb_name = make_wandb_run_name(task_args.step_id)

        # Transpile OlmoEarthConfig to model.yaml if present
        if UPath(scratch_space.olmoearth_config_path).exists():
            transpile_and_write_model_config(scratch_space, wandb_name)

        with execution_env(model_stage_paths, wandb_name) as rslearn_env_vars:
            logger.info(f"Running fit with environment variables: {rslearn_env_vars.model_dump_json()}")
            run_fit(model_stage_paths, wandb_name=wandb_name)
            best_checkpoint_path = find_best_checkpoint(UPath(rslearn_env_vars.TRAINER_DATA_PATH))
            wandb_info = get_wandb_run_info(wandb_name, rslearn_env_vars.WANDB_PROJECT, rslearn_env_vars.WANDB_ENTITY)

        return FineTuneTaskResults(
            checkpoint_path=best_checkpoint_path,
            wandb_run_info=wandb_info
        )


@contextmanager
def execution_env(model_stage_paths: ModelStagePaths, wandb_name: str) -> Iterator[RslearnTemplateVars]:
    """
    This context manager does two things:
    1. Initializes RslearnTemplateVars with the correct parameter values.
    2. Detects whether we are running in GCS, and pre-fetches all files into a temporary directory for performance reasons.

    In both cases, we ensure the yielded RslearnTemplateVars will target the original checkpoint path location for durable
    writes of intermediate states.
    """
    if is_gcs_path(model_stage_paths.root_path):
        # Need to copy from GCS to temporary directory for performance reasons
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_files_from_gcs_directory(
                gcs_source_dir=model_stage_paths.root_path,
                local_dest_dir=temp_dir,
                num_workers=OlmoEarthSettings.gcs_storage_manager_thread_count,
                worker_type="thread"
            )
            local_model_stage_paths = ModelStagePaths(root_path=temp_dir)
            rslearn_env_vars = RslearnTemplateVars.from_model_stage_paths(local_model_stage_paths, wandb_name=wandb_name)
            rslearn_env_vars.TRAINER_DATA_PATH = model_stage_paths.trainer_checkpoints_path  # we still want to write checkpoints remotely
            with rslearn_env_vars.temp_env():
                yield rslearn_env_vars

    else:
        rslearn_env_vars = RslearnTemplateVars.from_model_stage_paths(model_stage_paths, wandb_name=wandb_name)
        with rslearn_env_vars.temp_env():
            yield rslearn_env_vars


def make_wandb_run_name(step_id: UUID) -> str:
    return f"fine-tune-{step_id}"


def run_fit(model_stage_paths: ModelStagePaths, wandb_name: str) -> None:
    """Runs the rslearn fit command"""
    fit_args = ["fit", "--config", model_stage_paths.model_config_path]

    if UPath(model_stage_paths.trainer_last_checkpoint_path).exists():
        logger.info(f"Resuming training from checkpoint: {model_stage_paths.trainer_last_checkpoint_path}")
        fit_args += ["--ckpt_path", model_stage_paths.trainer_last_checkpoint_path]

    # We need to catch SystemExit because rslearn or any of its dependencies might call sys.exit() which will
    # wrest control away from us and crash the step without informing the orchestrator.
    try:
        logger.info(f"Running training with args: {fit_args}")
        RslearnLightningCLI(
            model_class=RslearnLightningModule,
            datamodule_class=RslearnDataModule,
            parser_class=RslearnArgumentParser,
            args=fit_args,
            subclass_mode_model=True,
            subclass_mode_data=True,
            save_config_kwargs={"overwrite": True},
        )
    except SystemExit as e:
        if e.code != 0:
            raise RuntimeError(f"rslearn exited with code {e.code}") from e


def find_best_checkpoint(trainer_data_path: UPath) -> str:
    """
    Find the best checkpoint from the trainer data path.

    Logic:
    1. Iterate over all .ckpt files in trainer_data_path
    2. If there's only TRAINER_LAST_CHECKPOINT_FILE_NAME, return that
    3. Otherwise, return the first non-TRAINER_LAST_CHECKPOINT_FILE_NAME found

    Note: if the user is saving top_k>1 checkpoints, we cannot actually find the
    *BEST* checkpoint, only an arbitrary one from the top k best.
    Standard practice in rslp is to use top_k=1 for exactly this reason.

    Returns:
        Full path to the best checkpoint file
    """
    last_checkpoint_path = None

    if trainer_data_path.exists() and trainer_data_path.is_dir():
        for file_path in trainer_data_path.iterdir():
            if file_path.suffix == '.ckpt':
                if file_path.name == TRAINER_LAST_CHECKPOINT_FILE_NAME:
                    last_checkpoint_path = file_path
                else:
                    return str(file_path)

    if last_checkpoint_path:
        return str(last_checkpoint_path)

    raise FileNotFoundError(f"No checkpoint files found in {trainer_data_path}")


def get_wandb_run_info(wandb_name: str, project: str | None, entity: str | None) -> WandbRunInfo:
    """
    Get wandb run information by searching for the run by name.

    Args:
        wandb_name: The wandb run name to search for
        project: The wandb project name
        entity: The wandb entity name

    Returns:
        WandbRunInfo containing run_id and url

    Raises:
        ValueError: If no run is found with the given name
        ImportError: If wandb is not available
    """
    try:
        api = wandb.Api()

        if not project or not entity:
            raise ValueError("WANDB_PROJECT and WANDB_ENTITY must be configured")

        runs = api.runs(f"{entity}/{project}", filters={"display_name": wandb_name})

        if not runs:
            raise ValueError(f"No wandb run found with name '{wandb_name}' in project '{entity}/{project}'")

        # Get the first (most recent) matching run
        run = runs[0]

        return WandbRunInfo(run_id=run.id, url=run.url)

    except Exception as e:
        logger.warning(f"Failed to get wandb run info for {wandb_name}: {e}")
        # Return empty values as fallback
        return WandbRunInfo(run_id="", url="")


def transpile_and_write_model_config(scratch_space: FineTuningScratchSpace, wandb_name: str) -> None:
    """
    JIT transpile OlmoEarthConfig to rslearn model.yaml and write to expected location.
    """
    logger.info(f"Loading OlmoEarthConfig from {scratch_space.olmoearth_config_path}")
    config = ConfigClassLoader.load_olmoearth_config(scratch_space.olmoearth_config_path)

    model_stage_paths = scratch_space.model_stage_paths
    ops_context = ModelOperationalContext(
        step_type=StepType.FINE_TUNE,
        dataset_path=model_stage_paths.default_dataset_path,
        num_data_worker_processes=OlmoEarthSettings.NUM_WORKERS,
        wandb_name=wandb_name,
        model_stage_paths=model_stage_paths,
    )

    config_path = UPath(model_stage_paths.model_config_path)
    logger.info(f"Writing transpiled model config to {config_path}")
    config_path.write_text(to_model_config_yaml(config, ops_context))

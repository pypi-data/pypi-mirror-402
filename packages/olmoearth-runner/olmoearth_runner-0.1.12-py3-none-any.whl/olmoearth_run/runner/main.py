import argparse
import logging
import multiprocessing
import signal
import sys
import uuid


# Now safe to import modules that define metrics
from olmoearth_run.api_clients.olmoearth_run.olmoearth_run_api_client import OlmoEarthRunApiClient
from olmoearth_run.config import OlmoEarthSettings
from olmoearth_run.runner.steps.base_step_definition import BaseStepDefinition
from olmoearth_run.shared.models.api.task import TaskResponseWithStepAndWorkflow
from olmoearth_shared.api.run.status import Status
from olmoearth_run.shared.models.api.step_type import StepType
from olmoearth_shared.tools.telemetry.logging_tools import configure_logging
from olmoearth_shared.tools.telemetry.prometheus import make_standalone_metrics_server


# Configure logging at startup - must happen first
configure_logging()
logger = logging.getLogger(__name__)


# Set multiprocessing start method early, before any other imports that might use multiprocessing
multiprocessing.set_start_method("forkserver", force=True)


def main() -> None:
    """Main entry point for the oerunner command."""
    logger.info("Starting olmoearth runner")

    # Initialize Prometheus metrics server
    make_standalone_metrics_server(OlmoEarthSettings.PROMETHEUS_MULTIPROC_DIR, OlmoEarthSettings.PROMETHEUS_METRICS_SERVER_PORT)

    parser = argparse.ArgumentParser(description="OlmoEarthRun task runner")
    parser.add_argument("--task-id", type=uuid.UUID, required=True, help="Task ID to load and process")

    args = parser.parse_args()
    logger.info(f"Starting OlmoEarthRun task runner with args: {args}")
    task_id = args.task_id

    # Initialize OlmoEarthRun client
    client = OlmoEarthRunApiClient(base_url=OlmoEarthSettings.OERUN_API_URL)

    # Let OlmoEarthRun know that we've started, and grab the full task
    task = _mark_task_running(task_id, client)

    # Install a sigterm handler in case we get killed
    def handle_sigterm(signum: int, frame: object) -> None:
        """Handle SIGTERM signal by marking the current task as failed."""
        logger.warning("Received SIGTERM signal")
        logger.info(f"Marking task {task_id} as FAILED due to SIGTERM")
        client.tasks.update_task(task_id, Status.FAILED)
        sys.exit(128 + signum)

    signal.signal(signal.SIGTERM, handle_sigterm)

    # Now try to execute the step
    step_def = None
    try:
        if not task.step:
            raise ValueError(f"Unexpected missing Step on {task.id=}")
        step_def = _get_step_def(task.step.step_type)()
        logger.info(f"Starting Running Step: {step_def.__class__.__name__}")
        results = step_def.run(task.args)
        logger.info(f"Step completed successfully: {step_def.__class__.__name__}")

        client.tasks.update_task(task.id, Status.COMPLETED, results)
    except Exception as e:
        logger.exception(f"Error executing task {task_id}: {e}")
        error_message = str(e)
        client.tasks.update_task(task_id, Status.FAILED, error_message=error_message)
        if step_def:
            step_def.on_task_error(task.args, e)
        raise


def _mark_task_running(task_id: uuid.UUID, client: OlmoEarthRunApiClient) -> TaskResponseWithStepAndWorkflow:
    try:
        task_response = client.tasks.update_task(task_id, Status.RUNNING)
        if not task_response.records:
            raise ValueError(f"Could not find: {task_id=} : {task_response}")

        task = task_response.records[0]
        if not task.workflow or not task.step:
            raise ValueError(f"Unexpected missing Workflow or Step for {task.id=}")
        logger.info(f"Loaded task: {task.id}, Step: {task.step.id}, Workflow: {task.workflow.id}")
        return task
    except Exception as e:
        raise Exception(f"Error loading {task_id=}: {e}") from e


def _get_step_def(step_type: StepType) -> type[BaseStepDefinition]:
    """
    Returns an instance of the StepDefinition class for this step type.
    We intentionally lazy import all of these classes since we don't want to load any of their libraries/dependencies
    if not necessary.  This has a huge impact with the ML dependencies of the FineTuning / Inference steps.
    """
    if step_type == StepType.CREATE_PARTITIONS:
        from olmoearth_run.runner.steps.create_partitions_step_definition import CreatePartitionsStepDefinition
        return CreatePartitionsStepDefinition
    elif step_type == StepType.DATASET_BUILD:
        from olmoearth_run.runner.steps.dataset_build_step_definition import DatasetBuildStepDefinition
        return DatasetBuildStepDefinition
    elif step_type == StepType.DATASET_BUILD_FROM_WINDOWS:
        from olmoearth_run.runner.steps.dataset_build_from_windows_step_definition import \
            DatasetBuildFromWindowsStepDefinition
        return DatasetBuildFromWindowsStepDefinition
    elif step_type == StepType.PREPARE_LABELED_WINDOWS:
        from olmoearth_run.runner.steps.prepare_labeled_windows_step_definition import \
            PrepareLabeledWindowsStepDefinition
        return PrepareLabeledWindowsStepDefinition
    elif step_type == StepType.FINE_TUNE:
        from olmoearth_run.runner.steps.fine_tuning_step_definition import FineTuningStepDefinition
        return FineTuningStepDefinition
    elif step_type == StepType.RUN_INFERENCE:
        from olmoearth_run.runner.steps.run_inference_step_definition import RunInferenceStepDefinition
        return RunInferenceStepDefinition
    elif step_type == StepType.POSTPROCESS_PARTITION:
        from olmoearth_run.runner.steps.postprocess_partition_step_definition import \
            PostprocessPartitionStepDefinition
        return PostprocessPartitionStepDefinition
    elif step_type == StepType.COMBINE_PARTITIONS:
        from olmoearth_run.runner.steps.combine_partitions_step_definition import CombinePartitionsStepDefinition
        return CombinePartitionsStepDefinition
    else:
        raise ValueError(f"Unsupported step type: {step_type}")


if __name__ == "__main__":
    main()

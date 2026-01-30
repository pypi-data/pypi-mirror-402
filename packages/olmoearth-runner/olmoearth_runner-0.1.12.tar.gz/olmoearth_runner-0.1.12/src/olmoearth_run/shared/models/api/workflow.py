"""
This is not in shared because we don't expose StepResponse outside of Run API
"""

from pydantic import Field

from olmoearth_run.shared.models.api.step import StepResponse
from olmoearth_shared.tools.gcs_tools import read_text_from_gcs
from olmoearth_shared.api.run.prediction_geometry import PredictionRequestCollection
from olmoearth_shared.api.run.workflow import WorkflowResponse
from olmoearth_shared.api.run.workflow_args import PredictionWorkflowArgs


class WorkflowResponseWithSteps(WorkflowResponse):
    """
    If we want to provide the full list of steps along with the workflow, use this model.
    """
    steps: list[StepResponse] = Field(
        description="The list of Steps that make up the Workflow",
    )


def load_prediction_geometry(workflow_args: PredictionWorkflowArgs) -> PredictionRequestCollection:
    """Load and return the PredictionRequestCollection from GCS."""
    geojson = read_text_from_gcs(workflow_args.geometry_gcs_path)
    return PredictionRequestCollection.model_validate_json(geojson)

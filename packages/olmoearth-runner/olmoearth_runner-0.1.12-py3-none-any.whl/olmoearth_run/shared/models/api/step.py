import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from olmoearth_shared.api.run.status import Status
from olmoearth_run.shared.models.api.step_type import StepType


class StepMetrics(BaseModel):
    total_compute_time_seconds: int | None = Field(default=None, description="The total compute time in seconds for this step. This is the sum of completed_at - started_at for all task attempts")


class StepResponse(BaseModel):
    """
    The model we expose over the API to describe a Step.
    Steps are typically provided as part of the WorkflowResponse
    """
    id: uuid.UUID
    workflow_id: uuid.UUID = Field(description="The ID of the Workflow this Step belongs to")
    step_type: StepType = Field(description="The type of Step, e.g., 'PREDICTION', 'DATASET_BUILD'")
    step_index: int = Field(ge=0, description="The index of the Step in the Workflow")
    status: Status = Field(description="The current status of the Step")
    metrics: StepMetrics = Field(description="Metrics related to the Step's execution")

    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = Field(default=None, description="When the Step started running")
    completed_at: datetime | None = Field(
        default=None,
        description="The date and time when the Step was completed in either a success or failed state."
    )

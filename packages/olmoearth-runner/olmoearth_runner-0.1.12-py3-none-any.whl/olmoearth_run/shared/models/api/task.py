import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from olmoearth_shared.api.common.search_filters import DatetimeFilter, KeywordFilter, SortDirection
from olmoearth_shared.api.run.status import Status
from olmoearth_run.shared.models.api.step import StepResponse
from olmoearth_run.shared.models.api.task_args import TaskArgs, TaskArgsType
from olmoearth_run.shared.models.api.task_results import TaskResults
from olmoearth_shared.api.run.workflow import WorkflowResponse


class TaskIncludeField(str, Enum):
    """Fields that can be included in task responses via the 'include' parameter."""
    STEP = "step"
    WORKFLOW = "workflow"


# Constant for including all relationships
TASK_INCLUDE_ALL = [TaskIncludeField.STEP, TaskIncludeField.WORKFLOW]


class TaskAttempt(BaseModel):
    """
    A record of a single task execution attempt.
    We create one of these records everytime we submit a task to an executor to run.
    The executor_url is populated dynamically by the API and not stored in the database.
    """
    status: Status = Field(description="The final status of this attempt")
    executor_id: str | None = Field(
        default=None,
        description="The executor ID for this attempt"
    )
    executor_url: str | None = Field(
        default=None,
        description="The executor platform URL for this attempt (populated by the API)"
    )
    compute_resource: str | None = Field(
        default=None,
        description="The compute resource (e.g. machine type) used for this attempt"
    )
    container_image_url: str | None = Field(default=None, description="The exact URL used to execute this Attempt")
    error_message: str | None = Field(
        default=None,
        description="Error message if this attempt failed"
    )
    submitted_at: datetime | None = Field(default=None, description="When this attempt was submitted to the executor")
    started_at: datetime | None = Field(default=None, description="When the worker called back to ESRun that the task was running")
    completed_at: datetime | None = Field(
        default=None,
        description="When this attempt completed or failed"
    )


class TaskAttempts(BaseModel):
    """
    Wrapper model for the list of previous task attempts.
    Used for JSONB serialization in the database.
    """
    attempts: list[TaskAttempt] = Field(default_factory=list)

    def get_current_attempt(self) -> TaskAttempt:
        """Returns the most recent attempt."""
        return self.attempts[-1]


class TaskResponse(BaseModel):
    """
    The model we provide when asked for a Task over the API.
    """

    id: uuid.UUID = Field(description="The ID of the Task")
    step_id: uuid.UUID = Field(description="The ID of the Step this Task belongs to")
    status: Status = Field(description="The current status of the Task")
    args: TaskArgs = Field(
        description="The arguments provided to the Task. The schema of this is defined by the Step"
    )
    results: TaskResults | None = Field(
        default=None,
        description="Result data from the Task, the schema of which is defined by the Step"
    )
    created_at: datetime = Field(description="The date and time when the Task was created")
    updated_at: datetime = Field(description="The date and time when the Task was last updated")
    completed_at: datetime | None = Field(
        default=None,
        description="The date and time when the Task was completed, either successfully or with failure"
    )
    error_message: str | None = Field(
        default=None,
        description="Error details if the Task failed"
    )
    task_attempts: list[TaskAttempt] = Field(
        default_factory=list,
        description="History of execution attempts"
    )

    def get_args(self, args_type: type[TaskArgsType]) -> TaskArgsType:
        if not isinstance(self.args, args_type):
            raise ValueError(f"Task args are mismatched type: wanted {args_type}, got {type(self.args)}")
        return self.args


class TaskResponseWithStepAndWorkflow(TaskResponse):
    """
    When asking about only a task, you often want the context of the Step/Workflow associated with it.
    This model provides that. The step and workflow fields are optional and controlled by the 'include' parameter.
    """
    step: StepResponse | None = None
    workflow: WorkflowResponse | None = None


class TaskUpdateRequest(BaseModel):
    """
    Payload sent by a Task when it starts, completes, fails, etc. A completed Task may include
    detailed results that get handled as part of Step processing.
    """

    status: Status = Field(description="The new Task status")
    results: TaskResults | None = Field(
        default=None,
        description="Result data from the Task, the schema of which is defined by the Step"
    )
    error_message: str | None = Field(default=None, description="Error message if the Task failed")


class TaskSortField(str, Enum):
    """Valid fields for sorting tasks in search results."""
    STATUS = "status"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    COMPLETED_AT = "completed_at"


class SearchTasksRequest(BaseModel):
    """Request model for searching tasks"""
    id: KeywordFilter[uuid.UUID] | None = None
    step_id: KeywordFilter[uuid.UUID] | None = None
    status: KeywordFilter[Status] | None = None
    created_at: DatetimeFilter | None = None
    updated_at: DatetimeFilter | None = None
    completed_at: DatetimeFilter | None = None

    # Pagination and sorting
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    sort_by: TaskSortField = Field(default=TaskSortField.CREATED_AT)
    sort_direction: SortDirection = Field(default=SortDirection.DESC)

    # Relationship inclusion
    include: list[TaskIncludeField] | None = Field(default=None,description="Relationships to include")


class TaskExecutorStatus(BaseModel):
    status: Status = Field(description="The current status of the Task as reported by the executor")
    details: list[str] = Field(
        default_factory=list,
        description="Any additional information the executor can provide about this Task"
    )
    last_updated: datetime | None = Field(
        description="If available, the date of the most recent information from the executor"
    )
    url: str = Field(description="A url in the Executor platform to view more information")
    logs_url: str | None = Field(default=None, description="URL to view logs for executor")

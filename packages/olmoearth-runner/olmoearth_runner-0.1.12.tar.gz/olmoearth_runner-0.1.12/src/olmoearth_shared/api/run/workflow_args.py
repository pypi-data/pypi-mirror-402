import uuid
from typing import Annotated, Literal, TypeVar

from pydantic import BaseModel, Field, model_validator

from olmoearth_shared.api.run.prediction_geometry import PredictionRequestCollection
from olmoearth_shared.api.run.workflow_type import WorkflowType
from olmoearth_shared.models.olmoearth_config.olmoearth_config import OlmoEarthConfig


class BaseWorkflowArgs(BaseModel):
    workflow_type: WorkflowType = Field(
        description="The enumerated string identifying the category of Workflow being represented"
    )


class PredictionWorkflowCreateArgs(BaseWorkflowArgs):
    """Set of arguments required for creating a Prediction Workflow"""

    workflow_type: Literal[WorkflowType.PREDICTION] = Field(default=WorkflowType.PREDICTION)
    model_pipeline_id: uuid.UUID = Field(
        description="The ID of the ModelPipeline to be run for this prediction Workflow"
    )
    geometry: PredictionRequestCollection = Field(description="A GeoJSON feature collection specifying geometries and time ranges on which to run prediction")
    min_window_success_rate: float | None = Field(
        default=0.9,
        description="Minimum required ratio of non-rejected windows (prepared + skipped) to total windows. If None, the check is skipped."
    )


class PredictionWorkflowArgs(BaseWorkflowArgs):
    """Stored/response args for a Prediction Workflow (geometry stored at GCS path)."""
    workflow_type: Literal[WorkflowType.PREDICTION] = Field(default=WorkflowType.PREDICTION)
    model_pipeline_id: uuid.UUID = Field(
        description="The ID of the ModelPipeline to be run for this prediction Workflow"
    )
    geometry_gcs_path: str = Field(description="GCS path to the GeoJSON file specifying geometries and time ranges on which to run prediction")
    min_window_success_rate: float | None = Field(default=0.9, description="Minimum required ratio of non-rejected windows (prepared + skipped) to total windows. If None, the check is skipped.")


class DatasetBuildFromWindowsWorkflowArgs(BaseWorkflowArgs):
    """Arguments for building a dataset from pre-created windows."""
    workflow_type: Literal[WorkflowType.DATASET_BUILD_FROM_WINDOWS] = Field(default=WorkflowType.DATASET_BUILD_FROM_WINDOWS)
    container_image_id: uuid.UUID = Field(description="The ID of the container image to build the dataset with")
    dataset_path: str = Field(description="Path to the dataset with pre-created windows")
    total_workers: int = Field(default=1, description="Number of parallel tasks to create for processing windows")
    min_window_success_rate: float | None = Field(default=0.9, description="Minimum required ratio of non-rejected windows (prepared + skipped) to total windows. If None, the check is skipped.")


class LegacyFineTuningConfigParams(BaseModel):
    """Configuration file strings for legacy model + dataset definitions."""
    olmoearth_run_config_yaml: str = Field(description="The OlmoEarthRun configuration (YAML string)")
    dataset_config_json: str = Field(description="The dataset config that will be used to build the dataset (JSON string)")
    model_config_yaml: str = Field(description="The model config that will be used to train the model (YAML string)")


class BaseFineTuningWorkflowArgs(BaseWorkflowArgs):
    """Common fields for fine-tuning workflow args (both create and stored versions)."""
    workflow_type: Literal[WorkflowType.FINE_TUNING] = Field(default=WorkflowType.FINE_TUNING)
    annotation_features_path: str = Field(description="Path to the GeoJSON file containing annotation features")
    annotation_task_features_path: str = Field(description="Path to the GeoJSON file containing annotation task features")
    foundation_model_id: uuid.UUID = Field(description="The ID of foundation model to be staged for fine-tuning")
    container_image_id: uuid.UUID = Field(description="The ID of the container image to be used for fine-tuning")
    legacy_config: LegacyFineTuningConfigParams | None = Field(default=None, description="Legacy config parameters")
    model_name_prefix: str = Field(description="Prefix for the resulting fine-tuned model pipeline name (timestamp will be appended)")
    min_window_success_rate: float | None = Field(default=0.9, description="Minimum required ratio of non-rejected windows (prepared + skipped) to total windows. If None, the check is skipped.")


class FineTuningWorkflowCreateArgs(BaseFineTuningWorkflowArgs):
    """Arguments for creating a Fine Tuning Workflow (olmoearth_config stored separately)."""
    olmoearth_config: OlmoEarthConfig | None = Field(default=None, description="Unified OlmoEarth config (stored separately in olmoearth_configs table)")

    @model_validator(mode="after")
    def validate_config_mutex(self) -> "FineTuningWorkflowCreateArgs":
        """Validate that exactly one of olmoearth_config or legacy_config is set."""
        has_unified = self.olmoearth_config is not None
        has_legacy = self.legacy_config is not None

        if has_unified ^ has_legacy:
            return self

        raise ValueError("Must specify exactly one of olmoearth_config or legacy_config")


class FineTuningWorkflowArgs(BaseFineTuningWorkflowArgs):
    """Stored/response args for a Fine Tuning Workflow (olmoearth_config referenced by ID)."""
    olmoearth_config_id: uuid.UUID | None = Field(default=None, description="ID of the OlmoEarth config in the olmoearth_configs table")

    @model_validator(mode="after")
    def validate_config_mutex(self) -> "FineTuningWorkflowArgs":
        """Validate that exactly one of olmoearth_config_id or legacy_config is set."""
        has_unified = self.olmoearth_config_id is not None
        has_legacy = self.legacy_config is not None

        if has_unified ^ has_legacy:
            return self

        raise ValueError("Must specify exactly one of olmoearth_config_id or legacy_config")


# Stored/response args (what comes back from the API and is stored in DB)
WorkflowArgs = Annotated[
    FineTuningWorkflowArgs | PredictionWorkflowArgs | DatasetBuildFromWindowsWorkflowArgs,
    Field(discriminator='workflow_type')
]
WorkflowArgsType = TypeVar("WorkflowArgsType", bound=BaseWorkflowArgs)

# Create args (what clients send to create a workflow - may have full objects that get stored elsewhere)
WorkflowCreateArgs = Annotated[
    FineTuningWorkflowCreateArgs | PredictionWorkflowCreateArgs | DatasetBuildFromWindowsWorkflowArgs,
    Field(discriminator='workflow_type')
]
WorkflowCreateArgsType = TypeVar("WorkflowCreateArgsType", bound=BaseWorkflowArgs)

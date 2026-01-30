from enum import StrEnum

from pydantic import BaseModel, Field

from olmoearth_run.config import OlmoEarthSettings
from olmoearth_run.shared.models.api.step_type import StepType
from olmoearth_run.shared.models.model_stage_paths import ModelStagePaths


class DataSource(StrEnum):
    PLANETARY_COMPUTER = "planetary_computer"


class DatasetOperationalContext(BaseModel):
    """Environment/context-specific information necessary for controlling behavior of dataset operations."""
    data_source: DataSource = Field(default=DataSource.PLANETARY_COMPUTER, description="The data source for acquiring imagery")
    dataset_path: str = Field(description="The path to the rslearn dataset to be used for training/validation/testing/inference")


class ModelOperationalContext(BaseModel):
    """Environment/context-specific information necessary for controlling behavior of dataset and model operations."""

    step_type: StepType = Field(description="The type of step being performed")
    dataset_path: str = Field(description="The path to the rslearn dataset to be used for training/validation/testing/inference")
    num_data_worker_processes: int = Field(description="The number of concurrent workers to use for data loading for lightning ops, or to perform dataset operations in parallel")
    batch_size: int = Field(default=1, description="The number of inputs to process in each forward pass.")
    wandb_name: str = Field(default="N/A", description="The name of the wandb run")
    model_stage_paths: ModelStagePaths | None = Field(default=None, description="The paths to the model stage directories")

    @property
    def is_training(self) -> bool:
        return self.step_type == StepType.FINE_TUNE

    @property
    def wandb_project_name(self) -> str:
        return OlmoEarthSettings.WANDB_PROJECT

    @property
    def wandb_entity(self) -> str:
        return OlmoEarthSettings.WANDB_ENTITY

"""
This module specifies the template variables we expect to be
present in an rslearn model.yaml. They are parameters that the
OlmoEarthRun framework needs to control during its execution.

Values will be injected as environment variables for interpolation
into model.yaml by rslearn itself.
"""

import logging
import os
from contextlib import contextmanager
from typing import Iterator

from pydantic import BaseModel, Field

from olmoearth_run.config import OlmoEarthSettings
from olmoearth_run.shared.models.model_stage_paths import ModelStagePaths
from olmoearth_run.shared.models.prediction_scratch_space import WINDOW_OUTPUT_LAYER_NAME


logger = logging.getLogger(__name__)


class RslearnTemplateVars(BaseModel):
    DATASET_PATH: str = Field(description="Path to the rslearn dataset to be read from/written to")
    EXTRA_FILES_PATH: str = Field(description="Path to the extra pretrained model/data preprocessing config files")
    TRAINER_DATA_PATH: str = Field(description="Path to the rslearn trainer data directory. For intermediate checkpoints, trainer state, etc.")
    NUM_WORKERS: int = Field(description="Number of concurrent workers to use")
    PREDICTION_OUTPUT_LAYER: str = Field(description="Name of the rslearn output layer for model predictions")
    WANDB_PROJECT: str | None = Field(description="wandb project for the trainer to log metrics to")
    WANDB_NAME: str | None = Field(description="wandb name for the trainer to log metrics to")
    WANDB_ENTITY: str | None = Field(description="wandb entity for the trainer to log metrics to")

    @classmethod
    def from_model_stage_paths(cls, model_stage_paths: ModelStagePaths, dataset_path: str | None = None, wandb_name: str | None = None, num_workers: int | None = None) -> "RslearnTemplateVars":
        return RslearnTemplateVars(
            DATASET_PATH=dataset_path or model_stage_paths.default_dataset_path,
            EXTRA_FILES_PATH=model_stage_paths.extra_model_files_path,
            TRAINER_DATA_PATH=model_stage_paths.trainer_checkpoints_path,
            NUM_WORKERS=num_workers if num_workers is not None else OlmoEarthSettings.NUM_WORKERS,
            PREDICTION_OUTPUT_LAYER=WINDOW_OUTPUT_LAYER_NAME,
            WANDB_PROJECT=OlmoEarthSettings.WANDB_PROJECT,
            WANDB_NAME=wandb_name,
            WANDB_ENTITY=OlmoEarthSettings.WANDB_ENTITY,
        )

    @classmethod
    def validate_yaml(cls, yaml_str: str) -> None:
        """Validate that the yaml string contains references to all required environment variables."""
        error_messages = []

        for field_name, field_info in cls.model_fields.items():
            template_var = f"${{{field_name}}}"
            if template_var not in yaml_str:
                if field_info.description:
                    error_messages.append(f"{template_var}: {field_info.description}")
                else:
                    error_messages.append(template_var)

        if error_messages:
            error_message = "\n".join(["YAML file was missing required template variables"] + error_messages)
            raise ValueError(error_message)

    @contextmanager
    def temp_env(self) -> Iterator[None]:
        """Temporarily set environment variables that aren't already set, restore on exit."""
        original_values: dict[str, str | None] = {}
        keys_we_set: list[str] = []
        try:
            # Only set values for keys that aren't already in the environment
            for key, value in self.model_dump().items():
                if key not in os.environ:
                    os.environ[key] = str(value)
                    keys_we_set.append(key)
                    original_values[key] = None  # Track that we set this
            yield
        finally:
            # Only restore/remove the keys we actually set
            for key in keys_we_set:
                os.environ.pop(key, None)

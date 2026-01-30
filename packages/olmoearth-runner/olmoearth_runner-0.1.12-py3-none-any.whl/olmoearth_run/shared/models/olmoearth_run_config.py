"""
OlmoEarthRun configuration model representing the structure of olmoearth_run.yaml files.

This model captures the configuration structure for OlmoEarthRun workflows,
including partition strategies, postprocessing strategies, and window preparation.
"""

from typing import Any

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

from olmoearth_shared.api.run.inference_results_config import InferenceResultsConfig


class PartitionStrategiesConfig(BaseModel):
    """Configuration for partition strategies."""
    partition_request_geometry: dict[str, Any] = Field(
        description="Configuration for partitioning request geometry"
    )
    prepare_window_geometries: dict[str, Any] = Field(
        description="Configuration for preparing window geometries"
    )


class PostprocessingStrategiesConfig(BaseModel):
    """Configuration for postprocessing strategies."""
    process_window: dict[str, Any] = Field(
        description="Configuration for window-level postprocessing"
    )
    process_partition: dict[str, Any] = Field(
        description="Configuration for partition-level postprocessing"
    )
    process_dataset: dict[str, Any] = Field(
        description="Configuration for dataset-level postprocessing"
    )


class WindowPrepConfig(BaseModel):
    """Configuration for window preparation."""
    sampler: dict[str, Any] | None = Field(
        default=None,
        description="Configuration for sampler (optional, defaults to NoopSampler if not provided)"
    )
    labeled_window_preparer: dict[str, Any] = Field(
        description="Configuration for labeled window preparer"
    )
    data_splitter: dict[str, Any] = Field(
        description="Configuration for data splitter (mandatory)"
    )
    label_layer: str = Field(
        description="Name of the dataset layer where labeled windows should be written"
    )
    group_name: str = Field(
        default="default",
        description="Name of the group to store training windows",
    )
    split_property: str = Field(
        default="split",
        description="Name of the window options property to use for storing split assignment for training windows",
    )


class OlmoEarthRunConfig(BaseModel):
    """
    Root configuration model for OlmoEarthRun YAML files.

    This model represents the structure of olmoearth_run.yaml configuration files
    used to configure OlmoEarthRun workflows. Each section contains dictionaries
    that will be used by OlmoEarthRunConfigLoader to instantiate the appropriate
    classes using the _instantiate_from_dict method.
    """

    inference_results_config: InferenceResultsConfig = Field(
        description="Configuration for inference results"
    )

    partition_strategies: PartitionStrategiesConfig = Field(
        description="Strategies for partitioning geometries"
    )
    postprocessing_strategies: PostprocessingStrategiesConfig = Field(
        description="Strategies for postprocessing results"
    )
    window_prep: WindowPrepConfig | None = Field(
        default=None,
        description="Configuration for window preparation including labeled window preparer and optional data splitter"
    )

    # Allow additional fields for other configuration that might exist
    # but isn't directly related to class loading
    model_config = {"extra": "allow"}

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "OlmoEarthRunConfig":
        """
        Parse OlmoEarthRun configuration from a YAML string.

        Args:
            yaml_content: YAML content as a string

        Returns:
            OlmoEarthRunConfig object parsed from the YAML content

        Raises:
            ValueError: If the YAML content is malformed or doesn't match the expected structure
        """
        try:
            raw_config = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError("Invalid YAML in olmoearth_run_config") from e

        try:
            return cls.model_validate(raw_config)
        except Exception as e:  # Catch ValidationError and other pydantic errors
            raise ValueError(f"Invalid olmoearth_run_config structure. {e}") from e

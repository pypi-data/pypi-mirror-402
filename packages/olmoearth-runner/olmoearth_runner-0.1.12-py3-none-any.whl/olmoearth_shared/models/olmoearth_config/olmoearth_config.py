import yaml
from pydantic import BaseModel, Field

from olmoearth_shared.models.olmoearth_config.data.data import Data
from olmoearth_shared.models.olmoearth_config.input_preprocessing.input_preprocessing import InputPreprocessing
from olmoearth_shared.models.olmoearth_config.labeled_data_prep.labeled_data_prep import LabeledDataPrep
from olmoearth_shared.models.olmoearth_config.model.model import Model
from olmoearth_shared.models.olmoearth_config.prediction_requests.prediction_requests import PredictionRequests
from olmoearth_shared.models.olmoearth_config.training.training import Training


class OlmoEarthConfig(BaseModel):
    """
    Unified configuration for OlmoEarth: data requirements, model, dataset prep, training, prediction.
    """

    config_version: str = Field(description="The version of the configuration")
    data: Data = Field(description="Specifies the required data modalities, temporality of the data to retrieve, and the output schema (when a `model` is defined).")
    model: Model | None = Field(default=None, description="Defines the model architecture and the tasks to perform during inference.")
    input_preprocessing: InputPreprocessing | None = Field(default=None, description="Defines how input tensors are prepared or transformed before being provided to the model.")
    labeled_data_prep: LabeledDataPrep | None = Field(default=None, description="Controls the preparation of labeled data for training.")
    training: Training | None = Field(default=None, description="Configuration for the training")
    prediction_requests: PredictionRequests | None = Field(default=None, description="Controls the prediction requests for the model.")

    @property
    def version_major(self) -> int:
        """Extract major version component from config_version (e.g., '1.2.3' -> 1)."""
        return self._parse_semver_part(0)

    @property
    def version_minor(self) -> int:
        """Extract minor version component from config_version (e.g., '1.2.3' -> 2)."""
        return self._parse_semver_part(1)

    @property
    def version_micro(self) -> int:
        """Extract micro/patch version component from config_version (e.g., '1.2.3' -> 3)."""
        return self._parse_semver_part(2)

    def _parse_semver_part(self, index: int) -> int:
        """Parse a specific part of the semver string, handling pre-release/build metadata."""
        # Strip any pre-release (-beta.1) or build metadata (+build.123)
        base_version = self.config_version.split('-')[0].split('+')[0]
        parts = base_version.split('.')
        return int(parts[index]) if len(parts) > index else 0

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "OlmoEarthConfig":
        """
        Parse OlmoEarth configuration from a YAML string.

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
            raise ValueError(f"Invalid olmoearth_config structure. {e}") from e

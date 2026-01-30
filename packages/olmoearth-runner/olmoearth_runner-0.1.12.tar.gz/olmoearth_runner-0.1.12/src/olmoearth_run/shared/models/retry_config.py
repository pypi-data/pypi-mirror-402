"""
Retry configuration for different step types.
Defines automatic retry behavior with exponential backoff.
"""
import random

from pydantic import BaseModel, Field

from olmoearth_run.shared.models.api.step_type import StepType


class StepRetryConfig(BaseModel):

    max_retries: int = Field(
        default=0,
        ge=0,
        description="Maximum number of retries after initial failure. 0 means no retries."
    )
    base_delay_seconds: float = Field(
        default=60.0,
        ge=0,
        description="Delay in seconds between retries. Actual delay = base_delay * (2 ^ retry_attempt)"
    )

    def get_delay_seconds(self, retry_attempt: int) -> float:
        """
        Number of seconds to wait before the next retry attempt using exponential backoff with jitter
        This picks a random delay between half the delay and the total delay. Helps to avoid herd risk.
        """
        constant_delay = self.base_delay_seconds * (2 ** retry_attempt)
        return (constant_delay) / 2 + random.uniform(0, (constant_delay) / 2)


# Same defaults on all step types to start with to keep it simple
# These should be tuned per step type based on observations in real data
# NOTE: If the step type is not in the dictionary, the automatic retries are disabled
STEP_TYPE_RETRY_CONFIGS: dict[StepType, StepRetryConfig] = {
    StepType.PREPARE_LABELED_WINDOWS: StepRetryConfig(max_retries=3, base_delay_seconds=60.0),
    StepType.CREATE_PARTITIONS: StepRetryConfig(max_retries=2, base_delay_seconds=60.0),
    StepType.DATASET_BUILD: StepRetryConfig(max_retries=5, base_delay_seconds=60.0),
    StepType.DATASET_BUILD_FROM_WINDOWS: StepRetryConfig(max_retries=3, base_delay_seconds=60.0),
    StepType.FINE_TUNE: StepRetryConfig(max_retries=3, base_delay_seconds=60.0),
    StepType.RUN_INFERENCE: StepRetryConfig(max_retries=2, base_delay_seconds=60.0),
    StepType.POSTPROCESS_PARTITION: StepRetryConfig(max_retries=2, base_delay_seconds=60.0),
    StepType.COMBINE_PARTITIONS: StepRetryConfig(max_retries=2, base_delay_seconds=60.0),
}


def get_retry_config(step_type: StepType) -> StepRetryConfig:
    return STEP_TYPE_RETRY_CONFIGS.get(step_type, StepRetryConfig())

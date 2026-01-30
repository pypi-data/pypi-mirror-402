from pydantic import BaseModel, Field

from olmoearth_shared.models.olmoearth_config.input_preprocessing.samplers import TrainingSampler
from olmoearth_shared.models.olmoearth_config.input_preprocessing.transforms import Transform


class DefaultInputPreprocessing(BaseModel):
    input_size: int = Field(ge=1, description="Extracts square crops from the provided images at this size, which become individual inputs in inference batches after the transform pipeline is complete.")
    transforms: list[Transform] = Field(default_factory=lambda: [], description="The transforms to apply to the input tensors before they are provided to the model.")


class TrainingSplitInputPreprocessing(BaseModel):
    input_size: int | None = Field(default=None, ge=1, description="Overrides the default input_size for this split.")
    transforms: list[Transform] | None = Field(
        default=None,
        description="Transforms to apply to inputs. Replaces default transforms; takes precedence over additional_transforms.",
    )
    additional_transforms: list[Transform] | None = Field(
        default=None,
        description="Additional transforms to apply beyond the default transforms.",
    )
    sampler: TrainingSampler | None = Field(
        default=None,
        description="Samples down the data to a smaller set based on the given strategy.",
    )


class PredictInputPreprocessing(BaseModel):
    input_size: int | None = Field(default=None, ge=1, description="Overrides the default input_size for this split.")
    overlap_pixels: int = Field(
        ge=0,
        description="Overlap between cropped inputs; also used when merging inference outputs.",
    )
    transforms: list[Transform] | None = Field(
        default=None,
        description="Transforms to apply to inputs. Replaces default transforms; takes precedence over additional_transforms.",
    )
    additional_transforms: list[Transform] | None = Field(
        default=None,
        description="Additional transforms to apply beyond the default transforms.",
    )


class InputPreprocessing(BaseModel):
    """
    Defines how input tensors are prepared before being provided to the model.
    Each training dataset split (train, val, test) can have its own preprocessing configuration,
    as can input data at inference ("predict") time.
    All take their base configuration from "default", which can be overridden for each group.
    """
    default: DefaultInputPreprocessing = Field(description="Default input preprocessing configuration")
    train: TrainingSplitInputPreprocessing | None = None
    val: TrainingSplitInputPreprocessing | None = None
    test: TrainingSplitInputPreprocessing | None = None
    predict: PredictInputPreprocessing | None = None

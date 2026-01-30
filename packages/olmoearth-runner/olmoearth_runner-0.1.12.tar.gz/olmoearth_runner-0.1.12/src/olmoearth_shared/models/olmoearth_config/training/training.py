from pydantic import BaseModel, Field

from olmoearth_shared.models.olmoearth_config.training.optimizers import Optimizer
from olmoearth_shared.models.olmoearth_config.training.schedulers import Scheduler


class EncoderFreezing(BaseModel):
    """Controls when encoder weights are eligible for updates during training."""
    unfreeze_at_epoch: int = Field(ge=0, description="The epoch at which weights in the encoder can be updated by the optimizer.")
    unfreeze_lr_factor: float = Field(ge=0, description="The factor by which the learning rate is multiplied when the encoder is unfrozen.")


class Checkpointing(BaseModel):
    """Controls how the model is saved during training."""
    save_top_k: int = Field(ge=1, description="The number of checkpoints to save based on the monitored quantity.")
    save_last: bool = Field(default=True, description="Whether to save the last checkpoint.")


class Training(BaseModel):
    """Controls the model training process."""
    max_epochs: int = Field(ge=1, description="The maximum number of epochs to train for.")
    batch_size: int = Field(ge=1, description="The number of inputs to process in each training batch (see: `input_preprocessing`).")
    optimizer: Optimizer = Field(description="Controls the optimization algorithm used to update the model's weights.")
    scheduler: Scheduler = Field(description="Controls how the learning rate is modified over the course of training.")
    encoder_freezing: EncoderFreezing = Field(description="Controls when encoder weights are eligible for updates during training.")
    checkpointing: Checkpointing = Field(description="Controls how the model weights are periodically saving during training.")

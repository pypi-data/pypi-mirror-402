from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypeAliasType

MAX_OLMOEARTH_PATCH_SIZE = 8


class EncoderName(StrEnum):
    OLMOEARTH = "olmoearth"
    MANUAL = "manual"


class OlmoEarthEncoderSourceName(StrEnum):
    HUGGINGFACE = "huggingface"
    REGISTRY = "registry"
    MODEL_PATH = "model_path"
    DISTRIBUTED_CHECKPOINT = "distributed_checkpoint"


class OlmoEarthFromHuggingFace(BaseModel):
    """OlmoEarth encoder loaded from HuggingFace model ID."""
    name: Literal[OlmoEarthEncoderSourceName.HUGGINGFACE]
    model_id: str = Field(description="The ID of the model to use (sourced from HF)")


class OlmoEarthFromRegistry(BaseModel):
    """OlmoEarth encoder loaded from OlmoEarth's foundation model registry."""
    name: Literal[OlmoEarthEncoderSourceName.REGISTRY]
    model_name: str = Field(description="The name of the foundation model to use from OlmoEarth's registry")
    embedding_size: int = Field(description="The number of dimensions in the embeddings the encoder produces.")


class OlmoEarthFromModelPath(BaseModel):
    """
    OlmoEarth encoder loaded from a model checkpoint + config path. For unpublished models.
    Note: the embedding size must be explicitly provided, as we have no catalog or metadata to consult.
    """
    name: Literal[OlmoEarthEncoderSourceName.MODEL_PATH]
    model_path: str = Field(description="The path to the model checkpoint + config to use")
    embedding_size: int = Field(description="The number of dimensions in the embeddings the encoder produces.")


class OlmoEarthFromDistributedCheckpoint(BaseModel):
    """
    OlmoEarth encoder loaded from distributed checkpoint files + config. For in-flight pretraining checkpoints.
    Note: the embedding size must be explicitly provided, as we have no catalog or metadata to consult.
    """
    name: Literal[OlmoEarthEncoderSourceName.DISTRIBUTED_CHECKPOINT]
    checkpoint_path: str = Field(description="The path to the distributed checkpoint files + config to use")
    embedding_size: int = Field(description="The number of dimensions in the embeddings the encoder produces.")


OlmoEarthSource = TypeAliasType(
    "OlmoEarthSource",
    Annotated[
        OlmoEarthFromHuggingFace | OlmoEarthFromRegistry | OlmoEarthFromModelPath | OlmoEarthFromDistributedCheckpoint,
        Field(discriminator="name")
    ]
)


class OlmoEarthEncoder(BaseModel):
    """OlmoEarth encoder configuration."""
    name: Literal[EncoderName.OLMOEARTH]
    patch_size: int = Field(ge=1, le=MAX_OLMOEARTH_PATCH_SIZE, description="The size of the patch to use for the model")
    source: OlmoEarthSource = Field(description="Where to load the OlmoEarth encoder from")


class EscapeHatchEncoder(BaseModel):
    """
    TODO: Implement this fully.
    """
    name: Literal[EncoderName.MANUAL]


Encoder = TypeAliasType(
    "Encoder",
    Annotated[
        OlmoEarthEncoder | EscapeHatchEncoder,
        Field(discriminator="name")
    ]
)

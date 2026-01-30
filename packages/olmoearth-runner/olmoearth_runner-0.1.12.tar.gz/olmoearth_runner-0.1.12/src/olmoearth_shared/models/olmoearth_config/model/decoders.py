from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypeAliasType


class SegmentationDecoderName(StrEnum):
    UPSAMPLE_CONV = "upsample_conv"
    UNET = "unet"


class UpsampleConvSegmentationDecoder(BaseModel):
    """
    A decoder that upsamples the embeddings using a convolutional layer before passing to a segmentation decoder head.
    """
    name: Literal[SegmentationDecoderName.UPSAMPLE_CONV]


class UnetSegmentationDecoder(BaseModel):
    """
    A decoder that uses a U-Net architecture to perform segmentation.
    """
    name: Literal[SegmentationDecoderName.UNET]


SegmentationDecoder = TypeAliasType(
    "SegmentationDecoder",
    Annotated[
        UpsampleConvSegmentationDecoder | UnetSegmentationDecoder,
        Field(discriminator="name")
    ]
)


# TODO: classification, per-pixel regression, regression, and detection decoders

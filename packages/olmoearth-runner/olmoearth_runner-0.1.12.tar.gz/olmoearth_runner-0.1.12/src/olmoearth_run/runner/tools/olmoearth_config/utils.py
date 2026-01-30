from typing import assert_never

from rslearn.config import DType

from olmoearth_run.runner.tools.olmoearth_config.constants import (
    DATA_SPLIT_KEY,
    DEFAULT_GROUP_NAME,
    LABEL_LAYER_NAME,
    OLMOEARTH_ENCODER_RESOLUTION_METERS,
)
from olmoearth_run.shared.models.olmoearth_run_config import OlmoEarthRunConfig
from olmoearth_shared.models.olmoearth_config.data.output import (
    ClassificationValue,
    RasterField,
    RasterOutput,
    RegressionField,
    SegmentationField,
)
from olmoearth_shared.models.olmoearth_config.model.encoders import EscapeHatchEncoder, OlmoEarthEncoder
from olmoearth_shared.models.olmoearth_config.olmoearth_config import OlmoEarthConfig


class OutputFieldUtils:
    """Utilities for deriving execution-time values from output field definitions."""

    @staticmethod
    def get_dtype_for_field(field: RasterField) -> DType:
        """
        Derive the appropriate DType for a raster field based on its type.

        - SegmentationField: dtype derived from max class value
        - RegressionField: always FLOAT32
        """
        match field:
            case SegmentationField(allowed_values=allowed_values, nodata_value=nodata_value):
                return OutputFieldUtils.dtype_from_allowed_values(allowed_values, nodata_value)
            case RegressionField():
                return DType.FLOAT32
            case _ as unreachable:
                assert_never(unreachable)

    @staticmethod
    def dtype_from_allowed_values(
        allowed_values: list[ClassificationValue], nodata_value: int | None
    ) -> DType:
        """
        Determine the minimum dtype needed to represent all allowed values.

        Considers both the class values and the nodata value (if any).
        """
        values = [av.value for av in allowed_values]
        if nodata_value is not None:
            values.append(nodata_value)
        max_value = max(values)

        if max_value <= 2**8 - 1:
            return DType.UINT8
        elif max_value <= 2**16 - 1:
            return DType.UINT16
        else:
            raise ValueError(f"Maximum value {max_value} is too large for any supported dtype")

    @staticmethod
    def get_nodata_for_field(field: RasterField) -> int | float | None:
        match field:
            case SegmentationField(nodata_value=nodata_value):
                return nodata_value
            case RegressionField(nodata_value=nodata_value):
                return nodata_value
            case _ as unreachable:
                assert_never(unreachable)


class ConfigUtils:
    """Top-level utilities for deriving execution-time values from OlmoEarthConfig or OlmoEarthRunConfig."""

    @staticmethod
    def get_label_layer_name(config: OlmoEarthRunConfig | OlmoEarthConfig) -> str:
        """Get the name of the dataset layer where window labels are written."""
        if isinstance(config, OlmoEarthRunConfig):
            if not config.window_prep:
                raise ValueError("window_prep configuration is required")
            return config.window_prep.label_layer
        return LABEL_LAYER_NAME

    @staticmethod
    def get_group_name(config: OlmoEarthRunConfig | OlmoEarthConfig) -> str:
        """Get the group name for storing windows in the dataset."""
        if isinstance(config, OlmoEarthRunConfig):
            if not config.window_prep:
                raise ValueError("window_prep configuration is required")
            return config.window_prep.group_name
        return DEFAULT_GROUP_NAME

    @staticmethod
    def get_split_property(config: OlmoEarthRunConfig | OlmoEarthConfig) -> str:
        """Get the property name for storing split assignment in window metadata."""
        if isinstance(config, OlmoEarthRunConfig):
            if not config.window_prep:
                raise ValueError("window_prep configuration is required")
            return config.window_prep.split_property
        return DATA_SPLIT_KEY

    @staticmethod
    def get_window_resolution(config: OlmoEarthConfig) -> float:
        """
        Get the window resolution (meters per pixel) for the model input/output rasters.
        """
        if config.model is None:
            raise ValueError("Model configuration is required to determine window resolution")

        encoder = config.model.encoder
        match encoder:
            case OlmoEarthEncoder():
                return OLMOEARTH_ENCODER_RESOLUTION_METERS
            case EscapeHatchEncoder():
                raise NotImplementedError(
                    "Cannot yet determine window resolution for escape hatch encoders"
                )
            case _ as unreachable:
                assert_never(unreachable)

    @staticmethod
    def get_raster_output_field(config: OlmoEarthConfig) -> RasterField:
        if config.data.output is None:
            raise ValueError("Cannot find output field without data.output configuration.")

        if not isinstance(config.data.output, RasterOutput):
            raise ValueError("Expected RasterOutput, encountered VectorOutput.")

        if len(config.data.output.fields) != 1:
            raise ValueError("Expected exactly one output field, encountered multiple.")

        return list(config.data.output.fields.values())[0]

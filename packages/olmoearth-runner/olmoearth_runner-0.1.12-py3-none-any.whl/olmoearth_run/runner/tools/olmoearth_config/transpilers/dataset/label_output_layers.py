from typing import assert_never, cast

from rslearn.config import dataset

from olmoearth_run.runner.models.operational_context import DatasetOperationalContext
from olmoearth_run.runner.tools.olmoearth_config.constants import LABEL_LAYER_NAME, OUTPUT_LAYER_NAME
from olmoearth_run.runner.tools.olmoearth_config.utils import OutputFieldUtils
from olmoearth_shared.models.olmoearth_config.data.output import RasterField, RasterOutput, SegmentationField, RegressionField, VectorOutput
from olmoearth_shared.models.olmoearth_config.olmoearth_config import OlmoEarthConfig


class LabelOutputLayers:
    @staticmethod
    def generate_label_and_output_layers(olmoearth_config: OlmoEarthConfig, ops_context: DatasetOperationalContext) -> dict[str, dataset.LayerConfig]:
        """Generates all required rslearn label and output layers from the unified config, based on the output schemas and model task definitions."""
        label_output_layers: dict[str, dataset.LayerConfig] = {}

        output = olmoearth_config.data.output
        model = olmoearth_config.model

        if output is None:
            raise ValueError("No output schema specified")

        if len(output.fields) != 1:
            raise ValueError("Only one output field per model is supported at this time")

        field_name = list(output.fields.keys())[0]
        field = list(output.fields.values())[0]

        match output:
            case RasterOutput():
                label_output_layers[LABEL_LAYER_NAME] = LabelOutputLayers.generate_layer_for_raster_field(field_name, cast(RasterField, field), olmoearth_config, ops_context)
                if model:
                    label_output_layers[OUTPUT_LAYER_NAME] = LabelOutputLayers.generate_layer_for_raster_field(field_name, cast(RasterField, field), olmoearth_config, ops_context)
            case VectorOutput():
                raise ValueError("Vector outputs are not supported at this time")
            case _ as unreachable:
                assert_never(unreachable)

        return label_output_layers

    @staticmethod
    def generate_layer_for_raster_field(field_name: str, field: RasterField, olmoearth_config: OlmoEarthConfig, ops_context: DatasetOperationalContext) -> dataset.LayerConfig:
        """These may diverge for label vs output layers in the future, but are currently identical."""
        match field:
            case SegmentationField():
                return RasterFieldTranspilers.generate_segmentation_layer(field_name, field)
            case RegressionField():
                raise ValueError("Regression fields are not supported at this time")
            case _:
                assert_never(field)


class RasterFieldTranspilers:
    """Transpilers for individual raster field types into rslearn layers."""

    @staticmethod
    def generate_segmentation_layer(field_name: str, field: SegmentationField) -> dataset.LayerConfig:
        dtype = OutputFieldUtils.dtype_from_allowed_values(field.allowed_values, field.nodata_value)

        return dataset.LayerConfig(
            type=dataset.LayerType.RASTER,
            band_sets=[
                dataset.BandSetConfig(
                    bands=[field_name],
                    dtype=dtype,
                )
            ],
        )

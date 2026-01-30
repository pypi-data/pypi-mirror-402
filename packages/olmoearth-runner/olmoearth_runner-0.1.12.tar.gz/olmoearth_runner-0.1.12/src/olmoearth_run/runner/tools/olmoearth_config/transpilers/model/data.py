from typing import assert_never, cast

from rslearn.config import dataset
from rslearn.dataset.window import get_window_layer_dir
from upath import UPath

from olmoearth_run.runner.models import rslearn_config
from olmoearth_run.runner.models.operational_context import ModelOperationalContext
from olmoearth_run.runner.tools.olmoearth_config.constants import OLMOEARTH_SENTINEL2_L2A_BANDS, LABEL_LAYER_NAME, SENTINEL2_L2A, DATA_SPLIT_KEY, TARGET, TARGET_SELECTOR_PREFIX
from olmoearth_run.shared.models.data_split_type import DataSplitType
from olmoearth_shared.models.olmoearth_config.data.data import Data, Output
from olmoearth_shared.models.olmoearth_config.data.output import RegressionField, SegmentationField, RasterOutput, VectorOutput, RasterField
from olmoearth_shared.models.olmoearth_config.data.temporality import Temporality, SampledTemporality, RepeatingIntervalTemporality
from olmoearth_shared.models.olmoearth_config.data_type import DataType
from olmoearth_shared.models.olmoearth_config.input_preprocessing.input_preprocessing import DefaultInputPreprocessing, TrainingSplitInputPreprocessing, PredictInputPreprocessing
from olmoearth_shared.models.olmoearth_config.input_preprocessing.transforms import Transform, OlmoEarthNormalize, RandomFlip
from olmoearth_shared.models.olmoearth_config.model.encoders import Encoder, EscapeHatchEncoder, OlmoEarthEncoder
from olmoearth_shared.models.olmoearth_config.model.model import Model
from olmoearth_shared.models.olmoearth_config.input_preprocessing.transforms import TransformName
from olmoearth_shared.models.olmoearth_config.model.tasks import SegmentationTask
from olmoearth_shared.models.olmoearth_config.olmoearth_config import OlmoEarthConfig


class DataTranspiler:
    @staticmethod
    def generate_data_module_config(olmoearth_config: OlmoEarthConfig, ops_context: ModelOperationalContext) -> rslearn_config.DataModule:
        model = olmoearth_config.model
        preprocessing = olmoearth_config.input_preprocessing
        data = olmoearth_config.data

        if not model:
            raise ValueError("No model configuration provided, cannot make a data module config")

        if not preprocessing:
            raise ValueError("No input preprocessing configuration provided, cannot make a data module config")

        if not data.output:
            raise ValueError("No output schema specified, cannot make a data module config")

        return rslearn_config.RslearnDataModule(
            class_path=rslearn_config.ClassPath.RSLEARN_DATA_MODULE,
            init_args=rslearn_config.RslearnDataModuleInitArgs(
                path=ops_context.dataset_path,
                batch_size=OpsUtils.get_batch_size(olmoearth_config, ops_context),
                num_workers=ops_context.num_data_worker_processes,
                inputs=InputsTranspilers.generate_inputs(olmoearth_config.data, model.encoder, ops_context),
                task=TaskTranspilers.generate_task(model, data.output),
                default_config=PreprocessingTranspilers.generate_default_config(preprocessing.default, model, olmoearth_config.data),
                train_config=PreprocessingTranspilers.generate_training_split_config(DataSplitType.TRAIN, preprocessing.default, preprocessing.train, model, olmoearth_config.data),
                val_config=PreprocessingTranspilers.generate_training_split_config(DataSplitType.VAL, preprocessing.default, preprocessing.val, model, olmoearth_config.data),
                test_config=PreprocessingTranspilers.generate_training_split_config(DataSplitType.TEST, preprocessing.default, preprocessing.test, model, olmoearth_config.data),
                predict_config=PreprocessingTranspilers.generate_predict_config(preprocessing.default, preprocessing.predict, model, olmoearth_config.data),
            ),
        )


class InputsTranspilers:
    @staticmethod
    def generate_inputs(data: Data, encoder: Encoder, ops_context: ModelOperationalContext) -> dict[str, rslearn_config.DataInputArgs]:
        inputs: dict[str, rslearn_config.DataInputArgs] = {}

        modalities = data.modalities
        if modalities.sentinel2_l2a:
            inputs[SENTINEL2_L2A] = InputsTranspilers.generate_sentinel2_l2a_input_args(data.temporality, encoder)

        if ops_context.is_training:
            if data.output is None:
                raise ValueError("No output schema specified, cannot generate targets")
            inputs[TARGET] = InputsTranspilers.generate_training_target_args(data.output)

        return inputs

    @staticmethod
    def generate_sentinel2_l2a_input_args(temporality: Temporality, encoder: Encoder) -> rslearn_config.DataInputArgs:
        match encoder:
            case OlmoEarthEncoder():
                return rslearn_config.DataInputArgs(
                    data_type=DataType.RASTER,
                    layers=InputsTranspilers.generate_layer_names(temporality, SENTINEL2_L2A),
                    bands=OLMOEARTH_SENTINEL2_L2A_BANDS,
                    passthrough=True,
                    dtype=dataset.DType.FLOAT32.name,
                    load_all_layers=True,
                )
            case EscapeHatchEncoder():
                raise NotImplementedError("Escape hatch encoders are not supported at this time")
            case _:
                assert_never(encoder)

    @staticmethod
    def generate_training_target_args(output: Output) -> rslearn_config.DataInputArgs:
        if len(output.fields) != 1:
            raise NotImplementedError("Only one output field per model is supported at this time")

        field_name = list(output.fields.keys())[0]
        field = list(output.fields.values())[0]

        match output:
            case RasterOutput():
                return InputsTranspilers.generate_raster_training_target_args(field_name, cast(RasterField, field))
            case VectorOutput():
                raise NotImplementedError("Vector outputs are not supported at this time")
            case _ as unreachable:
                assert_never(unreachable)

    @staticmethod
    def generate_raster_training_target_args(field_name: str, field: RasterField) -> rslearn_config.DataInputArgs:
        match field:
            case SegmentationField():
                dtype = dataset.DType.INT32.name
            case RegressionField():
                dtype = dataset.DType.FLOAT32.name
            case _ as unreachable:
                assert_never(unreachable)

        return rslearn_config.DataInputArgs(
            data_type=DataType.RASTER,
            layers=[LABEL_LAYER_NAME],
            bands=[field_name],
            dtype=dtype,
            is_target=True,
        )

    @staticmethod
    def generate_layer_names(temporality: Temporality, modality_name: str) -> list[str]:
        # TODO: DRY up this temporality-> num images logic. used in dataset generation too.
        match temporality:
            case SampledTemporality():
                num_layers = temporality.num_samples
            case RepeatingIntervalTemporality():
                num_layers = temporality.num_periods
            case _:
                assert_never(temporality)

        # Use a dummy window path - we only care about the folder name at the end
        dummy_window_path = UPath("/dummy")

        layer_names = []
        for group_idx in range(num_layers):
            layer_dir = get_window_layer_dir(dummy_window_path, modality_name, group_idx)
            layer_name = layer_dir.name
            layer_names.append(layer_name)

        return layer_names


class TaskTranspilers:
    @staticmethod
    def generate_task(model: Model, output: Output) -> rslearn_config.Task:
        if len(model.tasks) != 1:
            raise NotImplementedError("Only one task is supported for now")

        task = list(model.tasks.values())[0]
        task_name = list(model.tasks.keys())[0]

        match task:
            case SegmentationTask():
                return TaskTranspilers.generate_segmentation_task(task_name, task, output)
            case _ as unreachable:
                assert_never(unreachable)

    @staticmethod
    def generate_segmentation_task(task_name: str, task: SegmentationTask, output: Output) -> rslearn_config.Task:
        field = output.fields[task_name]
        if not isinstance(field, SegmentationField):
            raise ValueError(f"Task {task_name} is not a segmentation task")

        num_classes = len(field.allowed_values)
        nodata_value = field.nodata_value

        return rslearn_config.SegmentationTask(
            class_path=rslearn_config.ClassPath.SEGMENTATION_TASK,
            init_args=rslearn_config.SegmentationTaskInitArgs(
                num_classes=num_classes,
                nodata_value=nodata_value,
                metric_kwargs={"average": "micro"},
            )
        )


class PreprocessingTranspilers:
    @staticmethod
    def generate_default_config(default: DefaultInputPreprocessing, model: Model, data: Data) -> rslearn_config.PreprocessingArgs:
        return rslearn_config.PreprocessingArgs(
            patch_size=default.input_size,
            transforms=PreprocessingTranspilers.generate_transforms_list(default.transforms, None, None, model.encoder, data),
        )

    @staticmethod
    def generate_training_split_config(split_type: DataSplitType, default: DefaultInputPreprocessing, training_split: TrainingSplitInputPreprocessing | None, model: Model, data: Data) -> rslearn_config.PreprocessingArgs:
        tags = {DATA_SPLIT_KEY: split_type.value}
        transforms_list = None
        patch_size = None

        if training_split is not None:
            transforms_list = PreprocessingTranspilers.generate_transforms_list(default.transforms, training_split.transforms, training_split.additional_transforms, model.encoder, data)
            patch_size = training_split.input_size if training_split.input_size is not None else None

            if training_split.sampler is not None:
                raise NotImplementedError("Samplers are not yet supported at this time")

        return rslearn_config.PreprocessingArgs(
            tags=tags,
            patch_size=patch_size,
            transforms=transforms_list,
        )

    @staticmethod
    def generate_predict_config(default: DefaultInputPreprocessing, predict_split: PredictInputPreprocessing | None, model: Model, data: Data) -> rslearn_config.PreprocessingArgs:
        input_size = default.input_size
        overlap_pixels = 0
        transforms_list = None
        patch_size = None

        if predict_split is not None:
            if predict_split.input_size is not None:
                input_size = predict_split.input_size
                patch_size = predict_split.input_size
            overlap_pixels = predict_split.overlap_pixels

            if predict_split.transforms is not None or predict_split.additional_transforms is not None:
                transforms_list = PreprocessingTranspilers.generate_transforms_list(
                    default.transforms,
                    predict_split.transforms,
                    predict_split.additional_transforms,
                    model.encoder,
                    data
                )

        overlap_ratio = None if overlap_pixels == 0 else overlap_pixels / input_size

        return rslearn_config.PreprocessingArgs(
            patch_size=patch_size,
            transforms=transforms_list,
            load_all_patches=True,
            skip_targets=True,
            overlap_ratio=overlap_ratio,
        )

    @staticmethod
    def generate_transforms_list(default_transforms: list[Transform], override_transforms: list[Transform] | None, additional_transforms: list[Transform] | None, encoder: Encoder, data: Data) -> list[rslearn_config.Transform]:
        transforms: list[Transform] = []

        match encoder:
            case OlmoEarthEncoder():
                transforms.append(OlmoEarthNormalize(name=TransformName.OLMOEARTH_NORMALIZE))
            case EscapeHatchEncoder():
                raise NotImplementedError("Escape hatch encoders are not supported at this time")
            case _:
                assert_never(encoder)

        if override_transforms is not None:
            transforms.extend(override_transforms)
        elif additional_transforms is not None:
            transforms.extend(default_transforms)
            transforms.extend(additional_transforms)
        else:
            transforms.extend(default_transforms)

        return [TransformTranspilers.generate_transform(transform, data) for transform in transforms]


class TransformTranspilers:
    @staticmethod
    def generate_transform(transform: Transform, data: Data) -> rslearn_config.Transform:
        match transform:
            case OlmoEarthNormalize():
                return TransformTranspilers.generate_olmoearth_normalize_transform(data)
            case RandomFlip():
                return TransformTranspilers.generate_random_flip_transform(transform, data)
            case _ as unreachable:
                assert_never(unreachable)

    @staticmethod
    def generate_olmoearth_normalize_transform(data: Data) -> rslearn_config.Transform:
        band_names = {}
        if data.modalities.sentinel2_l2a:
            band_names[SENTINEL2_L2A] = OLMOEARTH_SENTINEL2_L2A_BANDS

        return rslearn_config.OlmoEarthNormalize(
            class_path=rslearn_config.ClassPath.OLMOEARTH_NORMALIZE,
            init_args=rslearn_config.OlmoEarthNormalizeInitArgs(band_names=band_names),
        )

    @staticmethod
    def generate_random_flip_transform(transform: RandomFlip, data: Data) -> rslearn_config.Transform:
        modalities = data.modalities

        image_selectors: list[str] = []
        if modalities.sentinel2_l2a:
            image_selectors.append(SENTINEL2_L2A)
        if data.output is not None:
            match data.output:
                case RasterOutput():
                    if len(data.output.fields) != 1:
                        raise NotImplementedError("Only one output field per model is supported at this time")
                    field = list(data.output.fields.values())[0]
                    match field:
                        case SegmentationField():
                            image_selectors.append(f"{TARGET_SELECTOR_PREFIX}/classes")
                        case RegressionField():
                            image_selectors.append(f"{TARGET_SELECTOR_PREFIX}/values")
                        case _ as unreachable:
                            assert_never(unreachable)
                    image_selectors.append(f"{TARGET_SELECTOR_PREFIX}/valid")

                case VectorOutput():
                    raise NotImplementedError("Vector outputs are not supported at this time")

                case _:
                    assert_never(data.output)

        return rslearn_config.Flip(
            class_path=rslearn_config.ClassPath.RANDOM_FLIP,
            init_args=rslearn_config.FlipInitArgs(
                image_selectors=image_selectors,
                horizontal=transform.x,
                vertical=transform.y,
            ),
        )


class OpsUtils:
    @staticmethod
    def get_batch_size(olmoearth_config: OlmoEarthConfig, ops_context: ModelOperationalContext) -> int:
        if not ops_context.is_training:
            return ops_context.batch_size

        training = olmoearth_config.training
        if not training:
            raise ValueError("No training configuration provided, cannot get batch size")

        return training.batch_size

from enum import StrEnum
from typing import Annotated, Any, Generic, Literal, TypeVar, Union

from pydantic import BaseModel, Field

from olmoearth_shared.models.olmoearth_config.data_type import DataType


InitArgsT = TypeVar('InitArgsT')
ClassPathT = TypeVar('ClassPathT')


class ClassPath(StrEnum):
    """Enum of rslearn class paths we explicitly transpile to from OlmoEarthConfig."""

    # Lightning/rslearn core classes
    RSLEARN_LIGHTNING_MODULE = "rslearn.train.lightning_module.RslearnLightningModule"
    RSLEARN_DATA_MODULE = "rslearn.train.data_module.RslearnDataModule"

    # Model classes
    SINGLE_TASK_MODEL = "rslearn.models.singletask.SingleTaskModel"

    # Encoder classes
    OLMOEARTH_PRETRAIN_MODEL = "rslearn.models.olmoearth_pretrain.model.OlmoEarth"

    # Decoder classes
    UNET_DECODER = "rslearn.models.unet.UNetDecoder"
    SEGMENTATION_HEAD = "rslearn.train.tasks.segmentation.SegmentationHead"

    # Task classes
    SEGMENTATION_TASK = "rslearn.train.tasks.segmentation.SegmentationTask"

    # Transforms
    OLMOEARTH_NORMALIZE = "rslearn.models.olmoearth_pretrain.norm.OlmoEarthNormalize"
    RANDOM_FLIP = "rslearn.train.transforms.flip.Flip"

    # Training utilities
    PLATEAU_SCHEDULER = "rslearn.train.scheduler.PlateauScheduler"
    ADAMW_OPTIMIZER = "rslearn.train.optimizer.AdamW"

    # Loggers
    WANDB_LOGGER = "lightning.pytorch.loggers.WandbLogger"

    # Trainer Callbacks
    LEARNING_RATE_MONITOR = "lightning.pytorch.callbacks.LearningRateMonitor"
    FREEZE_UNFREEZE_CALLBACK = "rslearn.train.callbacks.freeze_unfreeze.FreezeUnfreeze"
    MODEL_CHECKPOINT_CALLBACK = "lightning.pytorch.callbacks.ModelCheckpoint"
    PREDICTION_WRITER_CALLBACK = "rslearn.train.prediction_writer.RslearnWriter"

    # Writers/Mergers
    RASTER_MERGER = "rslearn.train.prediction_writer.RasterMerger"


class TypedClassConfig(BaseModel, Generic[ClassPathT, InitArgsT]):
    """Typed config variant with required init_args."""
    class_path: ClassPathT
    init_args: InitArgsT


class TypedClassConfigNoArgs(BaseModel, Generic[ClassPathT]):
    """Typed config variant with no init_args."""
    class_path: ClassPathT


class OlmoEarthEncoderInitArgs(BaseModel):
    patch_size: int
    model_id: str | None = None
    model_path: str | None = None
    checkpoint_path: str | None = None
    embedding_size: int | None = None


OlmoEarthEncoder = TypedClassConfig[Literal[ClassPath.OLMOEARTH_PRETRAIN_MODEL], OlmoEarthEncoderInitArgs]


Encoder = Annotated[Union[OlmoEarthEncoder], Field(discriminator='class_path')]


class UNetDecoderInitArgs(BaseModel):
    in_channels: list[list[int]]
    out_channels: int
    conv_layers_per_resolution: int


UNetDecoder = TypedClassConfig[Literal[ClassPath.UNET_DECODER], UNetDecoderInitArgs]


SegmentationHead = TypedClassConfigNoArgs[Literal[ClassPath.SEGMENTATION_HEAD]]


Decoder = Annotated[Union[UNetDecoder, SegmentationHead], Field(discriminator='class_path')]


class ModelInitArgs(BaseModel):
    encoder: list[Encoder]
    decoder: list[Decoder]


Model = TypedClassConfig[Literal[ClassPath.SINGLE_TASK_MODEL], ModelInitArgs]


class PlateauSchedulerInitArgs(BaseModel):
    factor: float
    patience: int
    min_lr: float
    cooldown: int


PlateauScheduler = TypedClassConfig[Literal[ClassPath.PLATEAU_SCHEDULER], PlateauSchedulerInitArgs]


Scheduler = Annotated[Union[PlateauScheduler], Field(discriminator='class_path')]


class AdamWOptimizerInitArgs(BaseModel):
    lr: float


AdamWOptimizer = TypedClassConfig[Literal[ClassPath.ADAMW_OPTIMIZER], AdamWOptimizerInitArgs]


Optimizer = Annotated[Union[AdamWOptimizer], Field(discriminator='class_path')]


class RslearnLightningModuleInitArgs(BaseModel):
    model: Model
    scheduler: Scheduler | None = None
    optimizer: Optimizer | None = None


RslearnLightningModule = TypedClassConfig[Literal[ClassPath.RSLEARN_LIGHTNING_MODULE], RslearnLightningModuleInitArgs]


LightningModule = Annotated[Union[RslearnLightningModule], Field(discriminator='class_path')]


class DataInputArgs(BaseModel):
    data_type: DataType
    layers: list[str]
    bands: list[str]
    dtype: str
    passthrough: bool = False
    load_all_layers: bool = False
    is_target: bool = False


class OlmoEarthNormalizeInitArgs(BaseModel):
    band_names: dict[str, list[str]]


OlmoEarthNormalize = TypedClassConfig[Literal[ClassPath.OLMOEARTH_NORMALIZE], OlmoEarthNormalizeInitArgs]


class FlipInitArgs(BaseModel):
    image_selectors: list[str]
    vertical: bool = True
    horizontal: bool = True


Flip = TypedClassConfig[Literal[ClassPath.RANDOM_FLIP], FlipInitArgs]


Transform = Annotated[OlmoEarthNormalize | Flip, Field(discriminator='class_path')]


class PreprocessingArgs(BaseModel):
    tags: dict[str, Any] | None = None
    patch_size: int | None = None
    transforms: list[Transform] | None = None
    sampler: dict[str, Any] | None = None
    load_all_patches: bool | None = None
    skip_targets: bool | None = None
    overlap_ratio: float | None = None


class SegmentationTaskInitArgs(BaseModel):
    num_classes: int
    nodata_value: int | None = None
    metric_kwargs: dict[str, Any]


SegmentationTask = TypedClassConfig[Literal[ClassPath.SEGMENTATION_TASK], SegmentationTaskInitArgs]


Task = Annotated[SegmentationTask, Field(discriminator='class_path')]


class RslearnDataModuleInitArgs(BaseModel):
    path: str
    batch_size: int
    num_workers: int
    inputs: dict[str, Any]
    task: Task
    default_config: PreprocessingArgs
    train_config: PreprocessingArgs
    val_config: PreprocessingArgs
    test_config: PreprocessingArgs
    predict_config: PreprocessingArgs


RslearnDataModule = TypedClassConfig[Literal[ClassPath.RSLEARN_DATA_MODULE], RslearnDataModuleInitArgs]


DataModule = Annotated[Union[RslearnDataModule], Field(discriminator='class_path')]


class WandbLoggerInitArgs(BaseModel):
    project: str
    name: str
    entity: str


WandbLogger = TypedClassConfig[Literal[ClassPath.WANDB_LOGGER], WandbLoggerInitArgs]


class LearningRateMonitorInitArgs(BaseModel):
    logging_interval: str


LearningRateMonitor = TypedClassConfig[Literal[ClassPath.LEARNING_RATE_MONITOR], LearningRateMonitorInitArgs]


class FreezeUnfreezeCallbackInitArgs(BaseModel):
    module_selector: list[str | int]
    unfreeze_at_epoch: int
    unfreeze_lr_factor: float


FreezeUnfreezeCallback = TypedClassConfig[Literal[ClassPath.FREEZE_UNFREEZE_CALLBACK], FreezeUnfreezeCallbackInitArgs]


class ModelCheckpointCallbackInitArgs(BaseModel):
    monitor: str
    mode: str
    dirpath: str
    save_top_k: int
    save_last: bool


ModelCheckpointCallback = TypedClassConfig[Literal[ClassPath.MODEL_CHECKPOINT_CALLBACK], ModelCheckpointCallbackInitArgs]


class RasterMergerInitArgs(BaseModel):
    padding: int


RasterMerger = TypedClassConfig[Literal[ClassPath.RASTER_MERGER], RasterMergerInitArgs]


class PredictionWriterCallbackInitArgs(BaseModel):
    path: str
    output_layer: str
    merger: RasterMerger | None = None


PredictionWriterCallback = TypedClassConfig[Literal[ClassPath.PREDICTION_WRITER_CALLBACK], PredictionWriterCallbackInitArgs]


TrainerCallback = Annotated[LearningRateMonitor | FreezeUnfreezeCallback | ModelCheckpointCallback | PredictionWriterCallback, Field(discriminator='class_path')]


class Trainer(BaseModel):
    max_epochs: int | None = None
    logger: WandbLogger | None = None
    callbacks: list[TrainerCallback]


class ModelYamlConfig(BaseModel):
    model: LightningModule
    data: DataModule
    trainer: Trainer

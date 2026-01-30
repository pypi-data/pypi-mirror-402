from typing import assert_never

from olmoearth_run.runner.models import rslearn_config
from olmoearth_run.runner.models.operational_context import ModelOperationalContext
from olmoearth_run.runner.tools.olmoearth_config.constants import OLMOEARTH_MODULE_SELECTOR, OUTPUT_LAYER_NAME
from olmoearth_shared.models.olmoearth_config.data.output import Output, RasterOutput
from olmoearth_shared.models.olmoearth_config.input_preprocessing.input_preprocessing import PredictInputPreprocessing
from olmoearth_shared.models.olmoearth_config.model.encoders import Encoder, EscapeHatchEncoder, OlmoEarthEncoder
from olmoearth_shared.models.olmoearth_config.model.model import Model
from olmoearth_shared.models.olmoearth_config.model.tasks import SegmentationTask
from olmoearth_shared.models.olmoearth_config.olmoearth_config import OlmoEarthConfig
from olmoearth_shared.models.olmoearth_config.training.training import Checkpointing, EncoderFreezing


class TrainerTranspiler:
    @staticmethod
    def generate_trainer_config(olmoearth_config: OlmoEarthConfig, ops_context: ModelOperationalContext) -> rslearn_config.Trainer:
        model = olmoearth_config.model
        if not model:
            raise ValueError("No model configuration provided, cannot generate trainer stanza")

        output = olmoearth_config.data.output
        if not output:
            raise ValueError("No output schema specified, cannot generate trainer stanza")

        max_epochs = None
        logger = None
        callbacks: list[rslearn_config.TrainerCallback] = []

        if ops_context.is_training:
            training = olmoearth_config.training
            if not training:
                raise ValueError("No training configuration provided, cannot generate trainer stanza")

            max_epochs = training.max_epochs

            logger = TrainerTranspiler.generate_wandb_logger(ops_context)

            callbacks.extend([
                rslearn_config.LearningRateMonitor(
                    class_path=rslearn_config.ClassPath.LEARNING_RATE_MONITOR,
                    init_args=rslearn_config.LearningRateMonitorInitArgs(
                        logging_interval="epoch",
                    )
                ),
                TrainerTranspiler.generate_freeze_unfreeze_callback(model.encoder, training.encoder_freezing),
                TrainerTranspiler.generate_model_checkpoint_callback(training.checkpointing, model, ops_context),
            ])

        else:
            predict_input_preprocessing = None if not olmoearth_config.input_preprocessing else olmoearth_config.input_preprocessing.predict
            callbacks.append(TrainerTranspiler.generate_prediction_writer_callback(output, predict_input_preprocessing, ops_context))

        return rslearn_config.Trainer(
            max_epochs=max_epochs,
            logger=logger,
            callbacks=callbacks,
        )

    @staticmethod
    def generate_wandb_logger(ops_context: ModelOperationalContext) -> rslearn_config.WandbLogger:
        return rslearn_config.WandbLogger(
            class_path=rslearn_config.ClassPath.WANDB_LOGGER,
            init_args=rslearn_config.WandbLoggerInitArgs(
                project=ops_context.wandb_project_name,
                name=ops_context.wandb_name,
                entity=ops_context.wandb_entity,
            ),
        )

    @staticmethod
    def generate_freeze_unfreeze_callback(encoder: Encoder, encoder_freezing: EncoderFreezing) -> rslearn_config.FreezeUnfreezeCallback:
        module_selector: list[str | int]

        match encoder:
            case OlmoEarthEncoder():
                module_selector = OLMOEARTH_MODULE_SELECTOR
            case EscapeHatchEncoder():
                raise NotImplementedError("Escape hatch encoders are not supported at this time")
            case _ as unreachable:
                assert_never(unreachable)

        return rslearn_config.FreezeUnfreezeCallback(
            class_path=rslearn_config.ClassPath.FREEZE_UNFREEZE_CALLBACK,
            init_args=rslearn_config.FreezeUnfreezeCallbackInitArgs(
                module_selector=module_selector,
                unfreeze_at_epoch=encoder_freezing.unfreeze_at_epoch,
                unfreeze_lr_factor=encoder_freezing.unfreeze_lr_factor,
            ),
        )

    @staticmethod
    def generate_model_checkpoint_callback(checkpointing: Checkpointing, model: Model, ops_context: ModelOperationalContext) -> rslearn_config.ModelCheckpointCallback:
        if len(model.tasks) != 1:
            raise NotImplementedError("Only one task is supported for now")

        task = list(model.tasks.values())[0]

        match task:
            case SegmentationTask():
                monitor = "val_accuracy"
                mode = "max"
            case _ as unreachable:
                assert_never(unreachable)

        if ops_context.model_stage_paths is None:
            raise ValueError("Model stage paths are not set, cannot generate model checkpoint callback")

        return rslearn_config.ModelCheckpointCallback(
            class_path=rslearn_config.ClassPath.MODEL_CHECKPOINT_CALLBACK,
            init_args=rslearn_config.ModelCheckpointCallbackInitArgs(
                monitor=monitor,
                mode=mode,
                dirpath=ops_context.model_stage_paths.trainer_checkpoints_path,
                save_top_k=checkpointing.save_top_k,
                save_last=checkpointing.save_last,
            ),
        )

    @staticmethod
    def generate_prediction_writer_callback(output: Output, predict_input_preprocessing: PredictInputPreprocessing | None, ops_context: ModelOperationalContext) -> rslearn_config.PredictionWriterCallback:
        if len(output.fields) != 1:
            raise NotImplementedError("Only one output field is supported for now")

        dataset_path = ops_context.dataset_path
        output_layer = OUTPUT_LAYER_NAME
        merger = None

        if isinstance(output, RasterOutput):
            padding = 0
            if predict_input_preprocessing:
                padding = predict_input_preprocessing.overlap_pixels // 2

            if padding > 0:
                merger = rslearn_config.RasterMerger(
                    class_path=rslearn_config.ClassPath.RASTER_MERGER,
                    init_args=rslearn_config.RasterMergerInitArgs(
                        padding=padding,
                    ),
                )

        return rslearn_config.PredictionWriterCallback(
            class_path=rslearn_config.ClassPath.PREDICTION_WRITER_CALLBACK,
            init_args=rslearn_config.PredictionWriterCallbackInitArgs(
                path=dataset_path,
                output_layer=output_layer,
                merger=merger,
            ),
        )

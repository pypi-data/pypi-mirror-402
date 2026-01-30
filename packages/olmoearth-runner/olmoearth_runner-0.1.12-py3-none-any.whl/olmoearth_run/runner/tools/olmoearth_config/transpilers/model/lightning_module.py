from typing import assert_never, cast

from olmoearth_run.runner.models import rslearn_config
from olmoearth_run.runner.models.operational_context import ModelOperationalContext
from olmoearth_shared.models.olmoearth_config.data.output import SegmentationField
from olmoearth_shared.models.olmoearth_config.model.decoders import SegmentationDecoder, UnetSegmentationDecoder, UpsampleConvSegmentationDecoder
from olmoearth_shared.models.olmoearth_config.model.encoders import Encoder, EscapeHatchEncoder
from olmoearth_shared.models.olmoearth_config.model.encoders import OlmoEarthEncoder, OlmoEarthFromHuggingFace, OlmoEarthFromRegistry, OlmoEarthFromModelPath, OlmoEarthFromDistributedCheckpoint
from olmoearth_shared.models.olmoearth_config.model.tasks import ModelTask, SegmentationTask
from olmoearth_shared.models.olmoearth_config.olmoearth_config import OlmoEarthConfig
from olmoearth_shared.models.olmoearth_config.training.optimizers import AdamW
from olmoearth_shared.models.olmoearth_config.training.schedulers import Plateau


class LightningModuleTranspiler:
    """Responsible for transpiling unified OlmoEarthConfig into the top-level `model` member rslearn in model config."""

    @staticmethod
    def generate_lightning_module_config(olmoearth_config: OlmoEarthConfig, ops_context: ModelOperationalContext) -> rslearn_config.LightningModule:
        if not olmoearth_config.model:
            raise ValueError("No model configuration provided, cannot make a model stanza")

        encoder = olmoearth_config.model.encoder
        tasks = olmoearth_config.model.tasks

        if len(tasks) != 1:
            raise NotImplementedError("Only one task is supported for now")

        task_name = list(tasks.keys())[0]
        task = tasks[task_name]

        return rslearn_config.RslearnLightningModule(
            class_path=rslearn_config.ClassPath.RSLEARN_LIGHTNING_MODULE,
            init_args=rslearn_config.RslearnLightningModuleInitArgs(
                model=rslearn_config.Model(
                    class_path=rslearn_config.ClassPath.SINGLE_TASK_MODEL,
                    init_args=rslearn_config.ModelInitArgs(
                        encoder=EncoderTranspilers.generate_encoder_layers(encoder, ops_context),
                        decoder=DecoderTranspilers.generate_decoder_layers(task_name, task, olmoearth_config, ops_context)
                    )
                ),
                scheduler=SchedulerTranspilers.generate_scheduler(olmoearth_config, ops_context),
                optimizer=OptimizerTranspilers.generate_optimizer(olmoearth_config, ops_context)
            )
        )


class EncoderTranspilers:
    """Transpiles model encoder configurations into `encoder` layer specifications for rslearn model config."""

    @staticmethod
    def generate_encoder_layers(encoder: Encoder, ops_context: ModelOperationalContext) -> list[rslearn_config.Encoder]:
        """Delegates to the appropriate encoder generation function based on the encoder type."""
        match encoder:
            case OlmoEarthEncoder():
                return EncoderTranspilers.generate_olmoearth_encoder_layers(encoder, ops_context)
            case EscapeHatchEncoder():
                raise NotImplementedError("Escape hatch encoders are not supported at this time")
            case _ as unreachable:
                assert_never(unreachable)

    @staticmethod
    def generate_olmoearth_encoder_layers(encoder: OlmoEarthEncoder, ops_context: ModelOperationalContext) -> list[rslearn_config.Encoder]:
        """Transpiles OlmoEarth encoder configuration into `encoder` layers for rslearn model config."""
        path_size = encoder.patch_size
        model_id = None
        model_path = None
        checkpoint_path = None
        embedding_size = get_embedding_size(encoder)

        match encoder.source:
            case OlmoEarthFromHuggingFace():
                model_id = encoder.source.model_id
            case OlmoEarthFromRegistry():
                model_path = OpsUtils.get_foundation_model_path(ops_context)
            case OlmoEarthFromModelPath():
                model_path = encoder.source.model_path
            case OlmoEarthFromDistributedCheckpoint():
                checkpoint_path = encoder.source.checkpoint_path
            case _ as unreachable:
                assert_never(unreachable)

        return [rslearn_config.OlmoEarthEncoder(
            class_path=rslearn_config.ClassPath.OLMOEARTH_PRETRAIN_MODEL,
            init_args=rslearn_config.OlmoEarthEncoderInitArgs(
                patch_size=path_size,
                model_id=model_id,
                model_path=model_path,
                checkpoint_path=checkpoint_path,
                embedding_size=embedding_size,
            )
        )]


class DecoderTranspilers:
    """Transpiles model task configuration into the `decoder` layers for the rslearn model architecture spec."""

    @staticmethod
    def generate_decoder_layers(task_name: str, task: ModelTask, olmoearth_config: OlmoEarthConfig, ops_context: ModelOperationalContext) -> list[rslearn_config.Decoder]:
        """Delegates to the appropriate decoder generation function based on the task type."""
        match task:
            case SegmentationTask():
                return DecoderTranspilers.generate_segmentation_decoder_layers(task_name, task.decoder, olmoearth_config, ops_context)
            case _ as unreachable:
                assert_never(unreachable)

    @staticmethod
    def generate_segmentation_decoder_layers(task_name: str, decoder: SegmentationDecoder, olmoearth_config: OlmoEarthConfig, ops_context: ModelOperationalContext) -> list[rslearn_config.Decoder]:
        """Delegates to the appropriate segmentation decoder generation function based on the specific decoder type."""
        match decoder:
            case UpsampleConvSegmentationDecoder():
                return DecoderTranspilers.generate_upsample_conv_segmentation_decoder_layers(olmoearth_config, ops_context)
            case UnetSegmentationDecoder():
                return DecoderTranspilers.generate_unet_segmentation_decoder_layers(task_name, olmoearth_config, ops_context)
            case _ as unreachable:
                assert_never(unreachable)

    @staticmethod
    def generate_upsample_conv_segmentation_decoder_layers(olmoearth_config: OlmoEarthConfig, ops_context: ModelOperationalContext) -> list[rslearn_config.Decoder]:
        # TODO: required for Nov4 release LULC models, which use this decoder architecture. Favyen made some changes to rslearn though, so wait till he updates the olmoearth_projects configs.
        raise NotImplementedError("UpsampleConvSegmentationDecoder is not supported at this time")

    @staticmethod
    def generate_unet_segmentation_decoder_layers(task_name: str, olmoearth_config: OlmoEarthConfig, ops_context: ModelOperationalContext) -> list[rslearn_config.Decoder]:
        """Decoder that processes encoder-produced embeddings through U-Net convolutional layers before passing to the segmentation head."""
        output = olmoearth_config.data.output
        model = olmoearth_config.model

        if not output:
            raise ValueError("No output schema specified, cannot generate U-Net decoder stanza")
        if not model:
            raise ValueError("No model specified, cannot generate U-Net decoder stanza")

        num_classes = len(cast(SegmentationField, output.fields[task_name]).allowed_values)
        encoder = model.encoder

        match encoder:
            case OlmoEarthEncoder():
                patch_size = encoder.patch_size
                encoder_embedding_size = get_embedding_size(encoder)
            case EscapeHatchEncoder():
                raise NotImplementedError("Escape hatch encoders are not supported at this time")
            case _ as unreachable:
                assert_never(unreachable)


        return [
            rslearn_config.UNetDecoder(
                class_path=rslearn_config.ClassPath.UNET_DECODER,
                init_args=rslearn_config.UNetDecoderInitArgs(
                    in_channels=[[patch_size, encoder_embedding_size]],
                    out_channels=num_classes,
                    conv_layers_per_resolution=1,
                )
            ),
            rslearn_config.SegmentationHead(class_path=rslearn_config.ClassPath.SEGMENTATION_HEAD)
        ]


class SchedulerTranspilers:
    @staticmethod
    def generate_scheduler(olmoearth_config: OlmoEarthConfig, ops_context: ModelOperationalContext) -> rslearn_config.Scheduler | None:
        if not ops_context.is_training:
            return None

        training = olmoearth_config.training
        if not training:
            raise ValueError("No training configuration provided, cannot generate scheduler stanza")

        match training.scheduler:
            case Plateau():
                return SchedulerTranspilers.generate_plateau_scheduler(training.scheduler)
            case _ as unreachable:
                assert_never(unreachable)

    @staticmethod
    def generate_plateau_scheduler(scheduler: Plateau) -> rslearn_config.PlateauScheduler:
        return rslearn_config.PlateauScheduler(
            class_path=rslearn_config.ClassPath.PLATEAU_SCHEDULER,
            init_args=rslearn_config.PlateauSchedulerInitArgs(
                factor=scheduler.factor,
                patience=scheduler.patience,
                min_lr=scheduler.min_lr,
                cooldown=scheduler.cooldown,
            )
        )


class OptimizerTranspilers:
    @staticmethod
    def generate_optimizer(olmoearth_config: OlmoEarthConfig, ops_context: ModelOperationalContext) -> rslearn_config.Optimizer | None:
        if not ops_context.is_training:
            return None

        training = olmoearth_config.training
        if not training:
            raise ValueError("No training configuration provided, cannot generate optimizer stanza")

        match training.optimizer:
            case AdamW():
                return OptimizerTranspilers.generate_adamw_optimizer(training.optimizer)
            case _ as unreachable:
                assert_never(unreachable)

    @staticmethod
    def generate_adamw_optimizer(optimizer: AdamW) -> rslearn_config.Optimizer:
        return rslearn_config.AdamWOptimizer(
            class_path=rslearn_config.ClassPath.ADAMW_OPTIMIZER,
            init_args=rslearn_config.AdamWOptimizerInitArgs(
                lr=optimizer.lr,
            )
        )


def get_embedding_size(encoder: OlmoEarthEncoder) -> int:
    match encoder.source:
        case OlmoEarthFromHuggingFace(model_id=model_id):
            # Inline to avoid importing torch unless necessary
            # TODO: maybe move these light declarations into constant files?
            from olmoearth_pretrain.model_loader import ModelID  # type: ignore[import-untyped]
            from rslearn.models.olmoearth_pretrain.model import EMBEDDING_SIZES
            try:
                return EMBEDDING_SIZES[ModelID[model_id]]
            except KeyError as e:
                raise ValueError(f"Model ID {model_id} not found") from e
        case OlmoEarthFromRegistry(embedding_size=embedding_size):
            return embedding_size
        case OlmoEarthFromModelPath(embedding_size=embedding_size):
            return embedding_size
        case OlmoEarthFromDistributedCheckpoint(embedding_size=embedding_size):
            return embedding_size
        case _ as unreachable:
            assert_never(unreachable)


class OpsUtils:
    @staticmethod
    def get_foundation_model_path(ops_context: ModelOperationalContext) -> str:
        if ops_context.model_stage_paths is not None:
            return ops_context.model_stage_paths.extra_model_files_path

        raise ValueError("No model stage paths provided in operational context, cannot initialize model config")

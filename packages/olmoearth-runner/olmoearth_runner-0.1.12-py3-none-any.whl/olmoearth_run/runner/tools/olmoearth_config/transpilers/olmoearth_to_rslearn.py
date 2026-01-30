import yaml
from rslearn.config import dataset

from olmoearth_run.runner.models.operational_context import DatasetOperationalContext, ModelOperationalContext
from olmoearth_run.runner.models import rslearn_config
from olmoearth_run.runner.tools.olmoearth_config.transpilers.dataset.label_output_layers import LabelOutputLayers
from olmoearth_run.runner.tools.olmoearth_config.transpilers.dataset.modality_layers import ModalityLayers
from olmoearth_run.runner.tools.olmoearth_config.transpilers.model.data import DataTranspiler
from olmoearth_run.runner.tools.olmoearth_config.transpilers.model.lightning_module import LightningModuleTranspiler
from olmoearth_run.runner.tools.olmoearth_config.transpilers.model.trainer import TrainerTranspiler
from olmoearth_shared.models.olmoearth_config.olmoearth_config import OlmoEarthConfig


def to_dataset_config(olmoearth_config: OlmoEarthConfig, ops_context: DatasetOperationalContext) -> dataset.DatasetConfig:
    """Converts OlmoEarthConfig to rslearn's dataset config object."""
    return dataset.DatasetConfig(
        layers={
            **ModalityLayers.generate_modality_layers(olmoearth_config, ops_context),
            **LabelOutputLayers.generate_label_and_output_layers(olmoearth_config, ops_context)
        },
    )


def to_dataset_config_json(olmoearth_config: OlmoEarthConfig, ops_context: DatasetOperationalContext) -> str:
    """Converts OlmoEarthConfig to rslearn's dataset config as a JSON string."""
    config = to_dataset_config(olmoearth_config, ops_context)
    return config.model_dump_json(exclude_defaults=True, indent=2)


def to_model_config(olmoearth_config: OlmoEarthConfig, ops_context: ModelOperationalContext) -> rslearn_config.ModelYamlConfig:
    """Converts OlmoEarthConfig to rslearn's model config object."""
    return rslearn_config.ModelYamlConfig(
        model=LightningModuleTranspiler.generate_lightning_module_config(olmoearth_config, ops_context),
        data=DataTranspiler.generate_data_module_config(olmoearth_config, ops_context),
        trainer=TrainerTranspiler.generate_trainer_config(olmoearth_config, ops_context),
    )


def to_model_config_yaml(olmoearth_config: OlmoEarthConfig, ops_context: ModelOperationalContext) -> str:
    """Converts OlmoEarthConfig to rslearn's model config as a YAML string."""
    config = to_model_config(olmoearth_config, ops_context)
    return yaml.dump(config.model_dump(mode="json", exclude_defaults=True), default_flow_style=False, sort_keys=False)

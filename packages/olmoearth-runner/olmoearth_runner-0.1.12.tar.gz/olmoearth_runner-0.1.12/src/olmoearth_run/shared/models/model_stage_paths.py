from pydantic import BaseModel, Field


CHECKPOINT_FILE_NAME = "checkpoint.ckpt"
TRAINER_LAST_CHECKPOINT_FILE_NAME = "last.ckpt"
MODEL_CONFIG_FILE_NAME = "model.yaml"
DATASET_CONFIG_FILE_NAME = "dataset.json"
DATASET_CONFIG_FILE_NAME_IN_DATASET_DIR = "config.json"
OLMOEARTH_RUN_CONFIG_FILE_NAME = "olmoearth_run.yaml"
ANNOTATION_FEATURES_FILE_NAME = "annotation_features.geojson"
ANNOTATION_TASK_FEATURES_FILE_NAME = "annotation_task_features.geojson"
EXTRA_MODEL_FILES_DIR_NAME = "extra_model_files"
TRAINER_CHECKPOINTS_DIR_NAME = "trainer_checkpoints"


class ModelStagePaths(BaseModel):
    root_path: str = Field(description="A path to the location containing the configuration files that define the model")

    @property
    def default_dataset_path(self) -> str:
        """Path to the dataset for training/inference"""
        return f"{self.root_path}/dataset"

    @property
    def checkpoint_path(self) -> str:
        """Path to the checkpoint file containing the trained weights and biases"""
        return f"{self.root_path}/{CHECKPOINT_FILE_NAME}"

    @property
    def trainer_checkpoints_path(self) -> str:
        """
        Path lightning manages its in-flight state in during training, including:
        intermediate checkpoint files, trainer state, etc.
        """
        return f"{self.root_path}/{TRAINER_CHECKPOINTS_DIR_NAME}"

    @property
    def trainer_last_checkpoint_path(self) -> str:
        """Path to the last checkpoint file saved by the trainer"""
        return f"{self.trainer_checkpoints_path}/{TRAINER_LAST_CHECKPOINT_FILE_NAME}"

    @property
    def model_config_path(self) -> str:
        """Path to the model config that was used to train this ModelStage"""
        return f"{self.root_path}/{MODEL_CONFIG_FILE_NAME}"

    @property
    def dataset_config_path(self) -> str:
        """Path to the dataset config that defines the windows of this ModelStage"""
        return f"{self.root_path}/{DATASET_CONFIG_FILE_NAME}"

    @property
    def dataset_config_path_in_dataset_dir(self) -> str:
        """The configuration file where it needs to be when actually consumed by rslearn"""
        return f"{self.default_dataset_path}/{DATASET_CONFIG_FILE_NAME_IN_DATASET_DIR}"

    @property
    def olmoearth_run_config_path(self) -> str:
        """
        Path to the OlmoEarthRun config that defines:
            1. Partition strategies: How to split the Workflow into partitioned Tasks; and within a Task how to build individual window `STGeometry`s from a partition
            2. Postprocessing strategies: How to postprocess individual Windows, combine Windows within a Partition, and combine Partitions
            3. Fine tuning window preparation
        """
        return f"{self.root_path}/{OLMOEARTH_RUN_CONFIG_FILE_NAME}"

    @property
    def annotation_features_path(self) -> str:
        """Path to the annotation features GeoJSON file for fine-tuning"""
        return f"{self.root_path}/{ANNOTATION_FEATURES_FILE_NAME}"

    @property
    def annotation_task_features_path(self) -> str:
        """Path to the annotation task features GeoJSON file for fine-tuning"""
        return f"{self.root_path}/{ANNOTATION_TASK_FEATURES_FILE_NAME}"

    @property
    def extra_model_files_path(self) -> str:
        """
        Path to any extra files required to train or operate this model,
        e.g. pretrained embedding model weights + config, preprocessing config
        """
        return f"{self.root_path}/{EXTRA_MODEL_FILES_DIR_NAME}"

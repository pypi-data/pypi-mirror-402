import importlib
from typing import Any

from upath import UPath

from olmoearth_run.runner.tools.partitioners.partition_interface import PartitionInterface
from olmoearth_run.runner.tools.postprocessors.postprocess_interface import PostprocessInterfaceRaster, PostprocessInterfaceVector
from olmoearth_run.runner.tools.labeled_window_preparers.labeled_window_preparer import LabeledWindowPreparer
from olmoearth_run.runner.tools.data_splitters.data_splitter_interface import DataSplitterInterface
from olmoearth_run.runner.tools.samplers.sampler_interface import SamplerInterface
from olmoearth_run.runner.tools.samplers.noop_sampler import NoopSampler
from olmoearth_run.shared.models.olmoearth_run_config import OlmoEarthRunConfig


class OlmoEarthRunConfigLoader:
    @staticmethod
    def load_olmoearth_run_config(yaml_path: str) -> OlmoEarthRunConfig:
        """Load OlmoEarthRun configuration from a YAML file."""
        with UPath(yaml_path).open('r') as file:
            yaml_content = file.read()
        return OlmoEarthRunConfig.from_yaml(yaml_content)

    # Window preparation methods (training phase)
    @classmethod
    def get_labeled_window_preparer(cls, config: OlmoEarthRunConfig) -> LabeledWindowPreparer:
        """Loads and initializes a labeled window preparer based on the OlmoEarthRun configuration."""
        if config.window_prep is None:
            raise ValueError("window_prep configuration is required but not found in OlmoEarthRun config")
        preparer_config = config.window_prep.labeled_window_preparer
        preparer = cls._instantiate_from_dict(preparer_config)
        cls._validate_instance_type(preparer, LabeledWindowPreparer, "LabeledWindowPreparer")
        return preparer

    @classmethod
    def get_data_splitter(cls, config: OlmoEarthRunConfig) -> DataSplitterInterface:
        """Loads and initializes a data splitter based on the OlmoEarthRun configuration."""
        if config.window_prep is None:
            raise ValueError("window_prep configuration is required but not found in OlmoEarthRun config")
        splitter_config = config.window_prep.data_splitter
        splitter = cls._instantiate_from_dict(splitter_config)
        cls._validate_instance_type(splitter, DataSplitterInterface, "DataSplitterInterface")
        return splitter

    @classmethod
    def get_sampler(cls, config: OlmoEarthRunConfig) -> SamplerInterface:
        """Loads and initializes a sampler based on the OlmoEarthRun configuration."""
        if config.window_prep is None:
            raise ValueError("window_prep configuration is required but not found in OlmoEarthRun config")

        # If no sampler config provided, return NoopSampler
        if config.window_prep.sampler is None:
            return NoopSampler()

        sampler_config = config.window_prep.sampler
        sampler = cls._instantiate_from_dict(sampler_config)
        cls._validate_instance_type(sampler, SamplerInterface, "SamplerInterface")
        return sampler

    # Partition strategy methods (inference phase)
    @classmethod
    def get_partition_request_geometry_partitioner(cls, config: OlmoEarthRunConfig) -> PartitionInterface:
        """Loads and initializes a partitioner for partitioning request geometry."""
        return cls._get_partitioner_from_config(config.partition_strategies.partition_request_geometry)

    @classmethod
    def get_prepare_window_geometries_partitioner(cls, config: OlmoEarthRunConfig) -> PartitionInterface:
        """Loads and initializes a partitioner for preparing window geometries."""
        return cls._get_partitioner_from_config(config.partition_strategies.prepare_window_geometries)

    # Postprocessor strategy methods (inference phase)
    @classmethod
    def get_window_postprocessor(cls, config: OlmoEarthRunConfig) -> PostprocessInterfaceRaster | PostprocessInterfaceVector:
        """Loads and initializes a postprocessor for window-level processing."""
        return cls._get_postprocessor_from_config(config.postprocessing_strategies.process_window)

    @classmethod
    def get_partition_postprocessor(cls, config: OlmoEarthRunConfig) -> PostprocessInterfaceRaster | PostprocessInterfaceVector:
        """Loads and initializes a postprocessor for partition-level processing."""
        return cls._get_postprocessor_from_config(config.postprocessing_strategies.process_partition)

    @classmethod
    def get_dataset_postprocessor(cls, config: OlmoEarthRunConfig) -> PostprocessInterfaceRaster | PostprocessInterfaceVector:
        """Loads and initializes a postprocessor for dataset-level processing."""
        return cls._get_postprocessor_from_config(config.postprocessing_strategies.process_dataset)

    @classmethod
    def _get_partitioner_from_config(cls, config_dict: dict[str, Any]) -> PartitionInterface:
        """Helper method to instantiate and validate a partitioner from config."""
        partitioner = cls._instantiate_from_dict(config_dict)
        cls._validate_instance_type(partitioner, PartitionInterface, "PartitionInterface")
        return partitioner

    @classmethod
    def _get_postprocessor_from_config(cls, config_dict: dict[str, Any]) -> PostprocessInterfaceRaster | PostprocessInterfaceVector:
        """Helper method to instantiate and validate a postprocessor from config."""
        postprocessor = cls._instantiate_from_dict(config_dict)
        cls._validate_instance_type(postprocessor, PostprocessInterfaceRaster | PostprocessInterfaceVector, "Postprocessor")
        return postprocessor

    @classmethod
    def _validate_instance_type(cls, obj: Any, expected_type: Any, type_name: str) -> None:
        """Helper method to validate that an instantiated object matches the expected type."""
        if not isinstance(obj, expected_type):
            raise ValueError(f"Initialized object was not a {type_name}. Got type: {type(obj)}")

    @classmethod
    def _instantiate_from_dict(cls, config: dict[str, Any]) -> Any:
        """
        Recursively instantiates an object from a dictionary configuration.
        This is the core logic for handling nested objects and _module_/_callable_ calls.
        """
        if "_module_" in config and "_callable_" in config:
            # Handle instantiation via a callable (static method, class method, function)
            callable = cls._get_callable_from_module_and_path(config["_module_"], config["_callable_"])

            # Collect arguments, excluding internal keys
            call_args = {k: cls._instantiate_from_dict(v) if isinstance(v, dict) else v for k, v in config.items() if k not in ["_module_", "_callable_"]}
            return callable(**call_args)

        if "class_path" in config:
            # Handle direct class instantiation
            module_name, class_name = config["class_path"].rsplit(".", 1)
            module = importlib.import_module(module_name)
            target_class = getattr(module, class_name)

            init_args = config.get("init_args", {})

            # Recursively instantiate nested init_args
            resolved_init_args = {k: cls._instantiate_from_dict(v) if isinstance(v, dict) else v for k, v in init_args.items()}

            return target_class(**resolved_init_args)

        # If no special keys, check for nested dictionaries that still need instantiation
        resolved_value = {}
        is_complex_dict = False
        for k, v in config.items():
            if isinstance(v, dict):
                resolved_value[k] = cls._instantiate_from_dict(v)
                is_complex_dict = True
            else:
                resolved_value[k] = v
        return resolved_value if is_complex_dict else config  # Return original if no nested dicts were found

    @classmethod
    def _get_callable_from_module_and_path(cls, module_name: str, callable_path: str) -> Any:
        """Imports the specified module and then resolves the callable path within that module"""
        module = importlib.import_module(module_name)

        current_obj = module
        parts = callable_path.split(".")
        for part in parts:
            current_obj = getattr(current_obj, part)
        return current_obj

"""
This step is responsible for ingesting raw, labeled annotations,
and using them to prepare RSLearn windows with dataset label layers
for use in model training.

Currently supported input annotation formats:
    * GeoJSON FeatureCollections
"""

import json
import logging
import os
import tempfile
import uuid
from contextlib import contextmanager
from multiprocessing import Pool
from typing import cast, Iterator, TypeVar, Type

import numpy as np
from pydantic import BaseModel
from rslearn.dataset import Window
from rslearn.dataset.storage.file import FileWindowStorage
from rslearn.utils import STGeometry
from rslearn.utils.feature import Feature
from rslearn.utils.geometry import WGS84_PROJECTION
from rslearn.utils.raster_format import GeotiffRasterFormat
from rslearn.utils.vector_format import GeojsonVectorFormat
from shapely.geometry import shape as shapely_shape
from typing_extensions import override
from upath import UPath

from olmoearth_run.runner.tools.olmoearth_config.loaders.config import ConfigClassLoader
from olmoearth_run.runner.tools.olmoearth_config.loaders.labeled_data_prep import LabeledDataPrepClassLoader
from olmoearth_run.runner.tools.olmoearth_config.utils import ConfigUtils
from olmoearth_run.config import OlmoEarthSettings
from olmoearth_run.runner.models.training.annotation_features import (
    AnnotationFeature, AnnotationTaskFeature, AnnotationTaskFeatureCollection, AnnotationFeatureCollection
)
from olmoearth_run.runner.models.training.labeled_data import AnnotationTask, LabeledSTGeometry, RasterLabel, TrainingWindowLabelsTypes, \
    WindowOptions, ProcessedWindow
from olmoearth_run.runner.steps.base_step_definition import BaseStepDefinition
from olmoearth_run.runner.tools.data_splitters.data_splitter_interface import DataSplitterInterface
from olmoearth_run.runner.metrics.window_prep import WindowPrepMetrics
from olmoearth_run.runner.tools.labeled_window_preparers.labeled_window_preparer import LabeledWindowPreparer
from olmoearth_run.shared.models.fine_tuning_scratch_space import FineTuningScratchSpace
from olmoearth_run.shared.models.olmoearth_run_config import OlmoEarthRunConfig
from olmoearth_run.shared.models.api.task_args import PrepareLabeledWindowsTaskArgs
from olmoearth_run.shared.models.api.task_results import PrepareLabeledWindowsTaskResults
from olmoearth_shared.tools.gcs_tools import copy_files_from_gcs_directory, copy_files_to_gcs_directory, is_gcs_path
from olmoearth_shared.models.olmoearth_config.olmoearth_config import OlmoEarthConfig


logger = logging.getLogger(__name__)
GeojsonModel = TypeVar('GeojsonModel', bound=BaseModel)


class PrepareLabeledWindowsStepDefinition(BaseStepDefinition[PrepareLabeledWindowsTaskArgs, PrepareLabeledWindowsTaskResults]):
    @override
    def run(self, task_args: PrepareLabeledWindowsTaskArgs) -> PrepareLabeledWindowsTaskResults:
        """
        Execute the prepare labeled windows step.

        This step:
        1. Loads OlmoEarthRun configuration for window preparation
        2. Reads annotated features from GeoJSON files
        3. Applies sampling/filtering to annotation tasks
        4. Processes tasks in parallel (each worker generates and writes windows)
        5. Returns the total count of windows created
        """
        logger.info("Starting prepare labeled windows step")
        scratch_space = FineTuningScratchSpace(root_path=task_args.scratch_path)
        model_stage_paths = scratch_space.model_stage_paths

        # We will support both legacy and unified config until the latter is fully implemented to parity.
        config: OlmoEarthRunConfig | OlmoEarthConfig

        try:
            # Load OlmoEarthRun config from file
            config = ConfigClassLoader.load_olmoearth_config(scratch_space.olmoearth_config_path)
        except FileNotFoundError:
            config = ConfigClassLoader.load_olmoearth_run_config(
                model_stage_paths.olmoearth_run_config_path
            )

        # Read annotation tasks from GeoJSON files
        annotation_tasks = read_annotation_tasks(
            model_stage_paths.annotation_features_path,
            model_stage_paths.annotation_task_features_path
        )

        # Load sampler and apply filtering
        sampler = LabeledDataPrepClassLoader.load_sampler(config)
        logger.info(f"Loaded sampler: {type(sampler).__name__}")

        sampled_tasks = sampler.sample(annotation_tasks)
        logger.info(f"Sampled {len(sampled_tasks)} tasks from {len(annotation_tasks)} total tasks")

        if not sampled_tasks:
            logger.info("No tasks to process after sampling")
            return PrepareLabeledWindowsTaskResults(windows_count=0)

        # Process tasks in parallel - workers generate and write windows
        num_workers = min(len(sampled_tasks), os.cpu_count() or 4)
        logger.info(f"Starting worker pool with {num_workers} processes")

        total_tasks = len(sampled_tasks)
        tasks_completed = 0
        total_windows = 0

        with managed_dataset_path(task_args.dataset_path) as dataset_path:
            with Pool(
                processes=num_workers,
                initializer=AnnotationTaskProcessor.init_worker,
                initargs=(config, dataset_path)
            ) as pool:
                # Use imap_unordered for progress reporting (tasks complete out of order)
                for window_count in pool.imap_unordered(AnnotationTaskProcessor.process_task, sampled_tasks):
                    tasks_completed += 1
                    total_windows += window_count

                    WindowPrepMetrics.record_annotation_tasks_processed(tasks_completed)
                    WindowPrepMetrics.record_labeled_windows_prepared(window_count)

                    logger.info(
                        f"Progress: {tasks_completed}/{total_tasks} tasks complete "
                        f"({100 * tasks_completed // total_tasks}%), "
                        f"{total_windows} windows written so far"
                    )

        logger.info(
            f"Completed all {tasks_completed} tasks, "
            f"wrote {total_windows} total windows to dataset"
        )

        return PrepareLabeledWindowsTaskResults(windows_count=total_windows)


@contextmanager
def managed_dataset_path(dataset_path: str) -> Iterator[UPath]:
    """
    Context manager for dataset path handling.

    For GCS paths: Downloads dataset from GCS to a local temp directory before processing,
    then uploads the results back to GCS after processing completes.

    For local paths: Uses the path directly without any copying.

    Args:
        dataset_path: Path to the dataset

    Yields:
        The local path to use for dataset operations
    """
    if is_gcs_path(dataset_path):
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Copying dataset from GCS to local temporary directory: {dataset_path} -> {temp_dir}")
            copy_files_from_gcs_directory(
                gcs_source_dir=dataset_path,
                local_dest_dir=temp_dir,
                num_workers=OlmoEarthSettings.gcs_storage_manager_thread_count,
                worker_type="thread",
                initialize_dir_if_empty=True,
            )
            yield UPath(temp_dir)
            logger.info(f"Copying local dataset to GCS: {temp_dir} -> {dataset_path}")
            copy_files_to_gcs_directory(
                local_dir=temp_dir,
                gcs_dest_dir=dataset_path,
                num_workers=OlmoEarthSettings.gcs_storage_manager_thread_count,
                worker_type="thread",
            )
    else:
        yield UPath(dataset_path)


def read_annotation_tasks(annotation_features_path: str, annotation_task_features_path: str) -> list[AnnotationTask]:
    """
    Read raw geojson representing annotations and their grouping tasks.
    Converts to bundled AnnotationTask objects for use in LabeledWindowPreparer.
    """

    logger.info(f"Reading annotation task features from {annotation_task_features_path}")
    logger.info(f"Reading annotation features from {annotation_features_path}")

    # Read annotation task features
    tasks_feature_collection = load_and_validate_geojson_file(
        annotation_task_features_path,
        AnnotationTaskFeatureCollection,
        "Annotation task features"
    )

    # Read annotation features
    annotations_feature_collection = load_and_validate_geojson_file(
        annotation_features_path,
        AnnotationFeatureCollection,
        "Annotation features"
    )

    # Group features by task ID - no validation needed, types guarantee non-null values
    task_and_annotation_features_by_task_id: dict[uuid.UUID, tuple[AnnotationTaskFeature, list[AnnotationFeature]]] = {}

    for task_feature in tasks_feature_collection.features:
        task_id = task_feature.properties.oe_annotations_task_id
        task_and_annotation_features_by_task_id[task_id] = (task_feature, [])

    for annotation_feature in annotations_feature_collection.features:
        task_id = annotation_feature.properties.oe_annotations_task_id
        if task_id not in task_and_annotation_features_by_task_id:
            logger.warning(f"No task feature found for task ID {task_id}, skipping annotation")
            continue
        task_and_annotation_features_by_task_id[task_id][1].append(annotation_feature)

    # Convert to AnnotationTask objects and return as list
    annotation_tasks = []
    for task_id, (task_feature, annotation_features) in task_and_annotation_features_by_task_id.items():
        annotation_tasks.append(build_annotation_task(task_feature, annotation_features))

    return annotation_tasks


def load_and_validate_geojson_file(file_path: str, model_class: Type[GeojsonModel], file_description: str) -> GeojsonModel:
    """Load and validate a GeoJSON file with specific error handling."""
    try:
        with UPath(file_path).open('r') as f:
            geojson_data = json.load(f)
        return model_class.model_validate(geojson_data)
    except FileNotFoundError:
        raise ValueError(f"{file_description} file not found: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in {file_description.lower()} file '{file_path}'")
    except Exception as e:
        raise ValueError(f"Error reading {file_description.lower()} file '{file_path}'") from e


def build_annotation_task(task_feature: AnnotationTaskFeature, annotation_features: list[AnnotationFeature]) -> AnnotationTask:
    """
    Create an AnnotationTask from a task feature and its associated annotation features.
    This is the data that a LabeledWindowPreparer will receive to operate over.

    This method handles the conversion of raw GeoJSON features into processed ST geometries
    with proper temporal context, projection and labeling.

    Args:
        task_feature: The task boundary feature with temporal and spatial information
        annotation_features: List of annotation features associated with this task

    Returns:
        AnnotationTask with processed ST geometries
    """
    # Task-level object
    task_id = task_feature.properties.oe_annotations_task_id
    task_shapely_geom = shapely_shape(task_feature.geometry)
    task_time_range = task_feature.get_time_range()
    task_st_geometry = STGeometry(WGS84_PROJECTION, task_shapely_geom, task_time_range)

    # Annotation-level objects
    annotation_st_geometries = []
    for annotation_feature in annotation_features:
        try:
            shapely_geom = shapely_shape(annotation_feature.geometry)

            # NOTE: rslearn doesn't do anything with annotation-level temporal information,
            # so discard in favor of task-level
            annotation_st_geometry = STGeometry(WGS84_PROJECTION, shapely_geom, task_time_range)

            label_values = annotation_feature.properties.oe_labels

            annotation_labeled_st_geom = LabeledSTGeometry(st_geometry=annotation_st_geometry, labels=label_values)
            annotation_st_geometries.append(annotation_labeled_st_geom)

        except ValueError:
            logger.exception("Failed to convert annotation feature")
            continue

    return AnnotationTask(
        task_id=task_id,
        task_st_geometry=task_st_geometry,
        annotations=annotation_st_geometries
    )


class AnnotationTaskProcessor:
    """
    Worker state manager for parallel task processing.

    Manages per-worker state (preparer, splitter, config) and delegates
    actual processing to top-level functions. Uses a class-level singleton
    pattern where each worker process has its own instance.
    """

    # Class variable: holds the singleton instance in each worker process
    _instance = None

    def __init__(self, config: OlmoEarthRunConfig | OlmoEarthConfig, dataset_path: UPath):
        self.labeled_window_preparer = LabeledDataPrepClassLoader.load_labeled_window_preparer(config)
        self.data_splitter = LabeledDataPrepClassLoader.load_data_splitter(config)
        self.dataset_path = dataset_path
        self.config = config

    @classmethod
    def init_worker(cls, config: OlmoEarthRunConfig | OlmoEarthConfig, dataset_path: UPath) -> None:
        cls._instance = cls(config, dataset_path)

    @classmethod
    def process_task(cls, annotation_task: AnnotationTask) -> int:
        """
        Process a single annotation task using the worker's state.

        This is the entry point called by pool.imap_unordered().
        Delegates to the top-level process_annotation_task function.

        Args:
            annotation_task: Task to process

        Returns:
            Number of windows written for this task
        """
        if cls._instance is None:
            raise RuntimeError("AnnotationTaskProcessor not initialized - init_worker must be called first")

        return process_annotation_task(
            annotation_task,
            cls._instance.labeled_window_preparer,
            cls._instance.data_splitter,
            cls._instance.dataset_path,
            cls._instance.config
        )


def process_annotation_task(
    annotation_task: AnnotationTask,
    labeled_window_preparer: LabeledWindowPreparer,
    data_splitter: DataSplitterInterface,
    dataset_path: UPath,
    config: OlmoEarthRunConfig | OlmoEarthConfig
) -> int:
    """
    Process a single annotation task: generate windows and write them to the dataset.

    This function:
    1. Generates windows from the annotation task
    2. Applies data splitting to each window
    3. Writes each window immediately to the dataset

    Args:
        annotation_task: Task containing annotations to process
        labeled_window_preparer: Preparer instance for generating windows
        data_splitter: Splitter instance for assigning train/val/test splits
        dataset_path: Path to the RSLearn dataset
        config: OlmoEarthRun or OlmoEarth configuration

    Returns:
        Number of windows written for this task
    """
    # Generate windows for this task
    task_windows = labeled_window_preparer.prepare_labeled_windows(annotation_task)

    # Process each window: apply data splitting and write immediately
    windows_written = 0
    for labeled_window in task_windows:
        data_split = data_splitter.choose_split_for_window(labeled_window)

        window_options = WindowOptions(
            data_split=data_split,
            source_task_id=annotation_task.task_id
        )

        processed_window = ProcessedWindow(
            window=labeled_window,
            options=window_options
        )

        write_window_to_dataset(processed_window, dataset_path, config)
        windows_written += 1

    logger.info(
        f"Task {annotation_task.task_id}: generated and wrote {windows_written} windows"
    )

    return windows_written


def write_window_to_dataset(
    processed_window: ProcessedWindow,
    dataset_path: UPath,
    config: OlmoEarthRunConfig | OlmoEarthConfig
) -> None:
    """
    Write a single processed window to the dataset.

    Creates the RSLearn Window structure and writes:
    - Window metadata (projection, bounds, time_range, options)
    - Label layer (vector or raster depending on window type)

    Args:
        processed_window: The window with labels to write
        dataset_path: Path to the RSLearn dataset
        config: OlmoEarthRun or OlmoEarth configuration containing window_prep settings

    Raises:
        ValueError: If window_prep configuration is missing (for OlmoEarthRunConfig)
    """
    labeled_window = processed_window.window
    window_options = processed_window.options
    group = ConfigUtils.get_group_name(config)
    split_property = ConfigUtils.get_split_property(config)

    # Create window metadata from WindowOptions
    window_metadata = {
        split_property: window_options.data_split.value,
        "source_task_id": str(window_options.source_task_id)
    }

    rslearn_window = Window(
        storage=FileWindowStorage(dataset_path),
        group=group,
        name=labeled_window.name,
        projection=labeled_window.projection,
        bounds=labeled_window.bounds,
        time_range=labeled_window.time_range,
        options=window_metadata,
    )

    # Save window (creates directory structure and metadata.json)
    rslearn_window.save()

    # Write annotation features to label_layer
    write_label_layer(rslearn_window, labeled_window.labels, config)


def write_label_layer(window: Window, labels: TrainingWindowLabelsTypes, config: OlmoEarthRunConfig | OlmoEarthConfig) -> None:
    """
    Write label features to the specified layer in the RSLearn window.

    Supports two types of labels:
    1. Vector labels: List of LabeledSTGeometry objects -> written as GeoJSON
    2. Raster labels: numpy ndarray -> written as GeoTIFF

    Args:
        window: RSLearn Window object where the layer will be written
        labels: Either a list of GeoJSON features or a 2D numpy array representing labels
        config: OlmoEarthRunConfig or OlmoEarthConfig containing window prep settings
    """
    if all(isinstance(label, LabeledSTGeometry) for label in labels):
        vector_labels = cast(list[LabeledSTGeometry], labels)
        write_vector_label_layer(window, vector_labels, config)
    elif all(isinstance(label, RasterLabel) for label in labels):
        raster_labels = cast(list[RasterLabel], labels)
        write_raster_label_layer(window, raster_labels, config)
    else:
        raise ValueError(f"Unsupported labels type: {type(labels)}. Expected list or ndarray.")


def write_vector_label_layer(window: Window, labels: list[LabeledSTGeometry], config: OlmoEarthRunConfig | OlmoEarthConfig) -> None:
    """
    Write vector labels to the label layer.

    Args:
        window: RSLearn Window object
        labels: List of LabeledSTGeometry objects with STGeometry and label values
        config: OlmoEarthRunConfig or OlmoEarthConfig containing window prep settings
    """
    label_layer = ConfigUtils.get_label_layer_name(config)
    logger.debug(f"Writing {len(labels)} vector labels")

    # Convert LabeledSTGeometry objects to RSLearn Features
    rslearn_features = []
    for labeled_geom in labels:
        # Flatten label values into a single properties object, preserving key names.
        properties = {
            key: value for key, value in labeled_geom.labels.items()
            if value is not None  # must be excluded to be ignored by rslearn
        }

        rslearn_feature = Feature(labeled_geom.st_geometry, properties)
        rslearn_features.append(rslearn_feature)

    # Write features using RSLearn's vector format
    layer_dir = window.get_layer_dir(label_layer)
    GeojsonVectorFormat().encode_vector(layer_dir, rslearn_features)
    window.mark_layer_completed(label_layer)
    logger.debug(f"Successfully wrote vector features to layer '{label_layer}'")


def write_raster_label_layer(window: Window, labels: list[RasterLabel], config: OlmoEarthRunConfig | OlmoEarthConfig) -> None:
    """
    Write raster labels as GeoTIFF to the label layer.
    ALWAYS writes bands in alphabetical order of label keys.

    Args:
        window: RSLearn Window object
        labels: 2D numpy array with label values
        config: OlmoEarthRunConfig or OlmoEarthConfig containing window prep settings
    """
    label_layer = ConfigUtils.get_label_layer_name(config)

    labels.sort(key=lambda x: x.key)
    label_properties = [label.key for label in labels]
    raster_data = np.stack([label.value for label in labels])

    logger.debug(f"Writing raster labels with shape {raster_data.shape} to layer '{label_layer}'")

    # Create raster format with standard GeoTIFF settings
    geotiff_format = GeotiffRasterFormat(
        block_size=256,
        always_enable_tiling=True,
    )

    # Get raster directory for the label layer
    raster_dir = window.get_raster_dir(label_layer, label_properties)

    # Write raster data
    geotiff_format.encode_raster(
        raster_dir,
        window.projection,
        window.bounds,
        raster_data,
    )
    window.mark_layer_completed(label_layer)

    logger.debug(f"Successfully wrote raster labels to layer '{label_layer}'")

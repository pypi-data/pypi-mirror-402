import hashlib
import json
import logging
import multiprocessing
import shutil
from multiprocessing import Pool
from pathlib import Path
from tempfile import mkdtemp
from typing import cast

from geojson_pydantic import FeatureCollection, Feature, GeometryCollection
from geojson_pydantic.geometries import parse_geometry_obj
from google.cloud.storage.transfer_manager import THREAD  # type: ignore[import-untyped]
from rslearn.dataset import Window
from rslearn.dataset.storage.file import FileWindowStorage
from rslearn.dataset.storage.storage import WindowStorage
from rslearn.utils.geometry import WGS84_PROJECTION, STGeometry
from shapely import bounds
from shapely.geometry import mapping
from shapely.geometry.base import BaseGeometry
from shapely.prepared import prep, PreparedGeometry
from upath import UPath

from olmoearth_run.config import OlmoEarthSettings
from olmoearth_run.runner.exceptions import NoPartitionsCreatedError, NoWindowsCreatedError
from olmoearth_run.runner.steps.base_step_definition import BaseStepDefinition
from olmoearth_run.runner.tools.converters.feature_collection import fc_to_multipolygon
from olmoearth_run.runner.tools.olmoearth_run_config_loader import OlmoEarthRunConfigLoader
from olmoearth_run.runner.tools.partitioners.partition_interface import PartitionInterface
from olmoearth_run.shared.models.model_stage_paths import ModelStagePaths
from olmoearth_shared.api.run.prediction_geometry import (
    PredictionRequestCollection,
)
from olmoearth_run.shared.models.prediction_scratch_space import PredictionScratchSpace
from olmoearth_run.shared.models.api.task_args import CreatePartitionsTaskArgs
from olmoearth_run.shared.models.api.task_results import CreatePartitionsTaskResults
from olmoearth_shared.tools.gcs_tools import copy_files_to_gcs_directory, is_gcs_path

logger = logging.getLogger(__name__)

multiprocessing.set_start_method("forkserver", force=True)


class CreatePartitionsStepDefinition(BaseStepDefinition[CreatePartitionsTaskArgs, CreatePartitionsTaskResults]):
    _merged_request_geometry_prepared: PreparedGeometry
    window_partitioner: PartitionInterface
    scratch: PredictionScratchSpace
    dataset_path: UPath

    def run(self, task_args: CreatePartitionsTaskArgs) -> CreatePartitionsTaskResults:
        """
        Before this Step begins, OlmoEarthRun has ensured the existence of two structured working directories:

        {scratch_path}/
            prediction_request_geometry.geojson

        {model_stage_path}/
            partitions
        """
        self.scratch = PredictionScratchSpace(root_path=task_args.scratch_path)
        logger.info(f"Creating partitions. Scratch path: {self.scratch.root_path}")

        # ModelStagePaths also gives predictable directories. It might be inside of Scratch but it also might not be
        model_stage_paths = ModelStagePaths(root_path=task_args.model_stage_root_path)
        temp_dataset_path = mkdtemp()

        # Instantiate a partitioner that implements PartitionInterface by referring to the ModelStage's partitioning strategy config
        olmoearth_run_config = OlmoEarthRunConfigLoader.load_olmoearth_run_config(model_stage_paths.olmoearth_run_config_path)
        partitioner = OlmoEarthRunConfigLoader.get_partition_request_geometry_partitioner(olmoearth_run_config)
        self.window_partitioner = OlmoEarthRunConfigLoader.get_prepare_window_geometries_partitioner(olmoearth_run_config)

        # Retrieve the FeatureCollection that defines the prediction request spatiotemporal extents
        request_geometry = self.scratch.get_prediction_request_geometry()

        # Create a multipolygon from all features in the request geometry for pruning
        self._merged_request_geometry_prepared = prep(fc_to_multipolygon(request_geometry))

        logger.info(f"Generating partitions for {len(request_geometry.features)} partitions using {partitioner}.")
        # First, write partition geometries and create partition IDs (must happen sequentially due to side effects)
        partition_ids: list[str] = []
        partitions: list[PredictionRequestCollection] = []
        for idx, geometry in enumerate(partitioner.partition_request_geometry(request_geometry)):
            if not self._merged_request_geometry_prepared.intersects(fc_to_multipolygon(geometry)):
                logger.info(f"Skipping partition {idx} because it does not intersect with the request geometry.")
                continue

            partition_id = f'partition_{idx}'
            logger.debug(f"Creating partition_id {partition_id} with geometry: {geometry}")
            # This isn't explicitly required, but it provides a transient side-effect for dataset building and
            # inference result writing.  We should probably revisit this, but for now I'm restoring this behavior
            # to unblock progress.
            self.scratch.write_partition_geometry(partition_id, geometry)
            partitions.append(geometry)
            partition_ids.append(partition_id)

        # Validate that we created at least one partition
        if len(partition_ids) == 0:
            raise NoPartitionsCreatedError(
                "Partitioning created 0 partitions from the request geometry. "
                "Cannot proceed with an empty dataset."
            )

        logger.info(f"Creating windows for {len(partitions)} partitions.")
        windows = _create_windows_for_partitions(partition_ids, partitions, self.window_partitioner, request_geometry, task_args.scratch_path, temp_dataset_path)
        logger.info(f"Created {len(windows)} windows for {len(partition_ids)} partitions.")

        # Validate that we created at least one window
        if len(windows) == 0:
            raise NoWindowsCreatedError(
                f"Partitioning created 0 windows across {len(partition_ids)} partitions. "
                f"Cannot proceed with an empty dataset."
            )

        # Upload the temporary dataset directory to the final location
        logger.info(f"Copying temporary dataset from {temp_dataset_path} to final location at {task_args.dataset_path}")
        if is_gcs_path(task_args.dataset_path):
            copy_files_to_gcs_directory(temp_dataset_path, task_args.dataset_path, OlmoEarthSettings.gcs_storage_manager_thread_count, worker_type=THREAD)
        else:
            # This is a temporary solution to support local dataset paths.
            # Eventually, this type of functionality should be abstracted out into an interface with Google Cloud Storage and local filesystem implementations.
            _copy_files_to_local_directory(Path(temp_dataset_path), Path(task_args.dataset_path))
        logger.info("Finished copying dataset.")

        # Save partitions and windows, and request geometry to GeoJSON for visualization
        # Disabling for now. The format is improper GeoJSON none of the standard tools will read it.
        # It also takes forever to write this file and upload it to GCS.
        # logger.info(f"Saving {len(windows)} windows for {len(partitions)} partitions to {self.scratch.all_prediction_request_geometries_geojson} for visualization.")
        # _save_geometries_to_geojson(self.scratch, windows, partitions, request_geometry)
        # logger.info("Finished saving geometries to GeoJSON.")

        # Cleanup the temporary dataset directory
        logger.debug(f'Cleaning up temporary dataset directory: {temp_dataset_path}')
        shutil.rmtree(temp_dataset_path)

        return CreatePartitionsTaskResults(partition_ids=partition_ids)


def _create_windows_for_partitions(partition_ids: list[str], partitions: list[PredictionRequestCollection], window_partitioner: PartitionInterface,
                                   request_geometry: PredictionRequestCollection, scratch_path: str, dataset_path: str) -> list[Window]:
    # Prepare arguments for parallel window creation
    # Note: Pass request_geometry instead of prepared geometry (PreparedGeometry cannot be pickled)
    process_args = [
        (partition_id, geometry, window_partitioner, request_geometry, scratch_path, dataset_path, )
        for partition_id, geometry in zip(partition_ids, partitions)
    ]

    # Use multiprocessing to create windows in parallel by partition
    logger.info(f"Creating windows for {len(partition_ids)} partitions in parallel using {OlmoEarthSettings.NUM_WORKERS} workers")
    with Pool(processes=OlmoEarthSettings.NUM_WORKERS) as pool:
        results = pool.starmap(_create_windows_for_partition_wrapper, process_args)

    # Collect all windows from results
    windows: list[Window] = []
    for partition_id, partition_windows in results:
        windows.extend(partition_windows)

    return windows


def _copy_files_to_local_directory(source_path: Path, dest_path: Path) -> None:
    """Copy files from the source directory to the destination directory"""
    if not source_path.is_dir():
        raise ValueError(f"Source path {source_path} does not exist")
    if not dest_path.is_dir():
        raise ValueError(f"Destination path {dest_path} does not exist")

    for item in source_path.iterdir():
        dest = dest_path / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)


def _create_windows_for_partition_wrapper(
    partition_id: str,
    partition_geometry: PredictionRequestCollection,
    window_partitioner: PartitionInterface,
    merged_request_geometry: PredictionRequestCollection,
    scratch_path: str,
    dataset_path: str,
) -> tuple[str, list[Window]]:
    """
    Standalone function for creating windows for a partition.
    Used by multiprocessing to parallelize window creation across partitions.

    Args:
        partition_id: The ID of the partition
        partition_geometry: The geometry of the partition
        window_partitioner: The partitioner to use for creating window geometries
        merged_request_geometry: Request geometry for intersection testing (will be prepared in worker)
        scratch_path: Path to the scratch space
        dataset_path: Path to the dataset

    Returns:
        Tuple of (partition_id, list of Windows created)
    """
    logger.info(f"Creating windows for partition {partition_id}")
    scratch = PredictionScratchSpace(root_path=scratch_path)

    # Prepare the geometry in the worker process (PreparedGeometry cannot be pickled)
    merged_request_geometry_prepared = prep(fc_to_multipolygon(merged_request_geometry))

    windows: list[Window] = []
    # Generate and save Window objects for each window.
    for feature, st_geometry in window_partitioner.prepare_window_geometries(partition_geometry):
        logger.debug(f"Creating window for partition {partition_id} with geometry {st_geometry}")
        if not merged_request_geometry_prepared.intersects(st_geometry.to_projection(WGS84_PROJECTION).shp):
            logger.debug(f"Skipping window creation for partition {partition_id} because the window does not intersect with the request geometry.")
            continue

        storage = FileWindowStorage(UPath(dataset_path))
        window = _create_window_for_partition(partition_id, st_geometry, scratch, storage)
        window.save()
        window_root = window.storage.get_window_root(scratch.get_group(partition_id), window.name)
        scratch.write_window_request_feature(window_root, feature)
        windows.append(window)

    logger.info(f"Created {len(windows)} windows for partition {partition_id}")
    return partition_id, windows


def _create_window_for_partition(partition_id: str, st_geometry: STGeometry, scratch: PredictionScratchSpace, storage: WindowStorage) -> Window:
    """Create a Window object from a partition ID and spatiotemporal geometry"""

    # Create a consistent hash for the geometry so re-runs don't add new windows
    name = _generate_window_name(partition_id, st_geometry)
    group = scratch.get_group(partition_id)
    logger.debug(f"Creating window {name} in group {group} for partition {partition_id}")
    shape_bounds = [int(b) for b in bounds(st_geometry.shp)[0:4]]
    window = Window(
        storage=storage,
        group=group,
        name=name,
        projection=st_geometry.projection,
        bounds=(
            shape_bounds[0],
            shape_bounds[1],
            shape_bounds[2],
            shape_bounds[3],
        ),
        time_range=st_geometry.time_range,
    )
    return window


def _generate_window_name(partition_id: str, st_geometry: STGeometry) -> str:
    """Generate a unique, consistent name for a window based on its partition ID and geometry"""

    json_string = json.dumps(st_geometry.serialize(), sort_keys=True)
    hasher = hashlib.sha256()
    hasher.update(json_string.encode("utf-8"))
    return f"{partition_id}_{hasher.hexdigest()[:20]}"


def _save_geometries_to_geojson(scratch: PredictionScratchSpace, windows: list[Window], partitions: list[PredictionRequestCollection],
                                request_geometry: PredictionRequestCollection) -> None:
    """Save windows and partitions to a single GeoJSON file containing a FeatureCollection of 3 features:
        Windows and Partitions are combined into a GeometryCollection, and the request_geometry is included as-is.
    """
    windows_geom = GeometryCollection(
        type="GeometryCollection",
        geometries=[parse_geometry_obj(mapping(cast(BaseGeometry, window.get_geometry().to_projection(WGS84_PROJECTION).shp))) for window in windows],
    )

    partitions_geom = GeometryCollection(type="GeometryCollection", geometries=[])
    for partition in partitions:
        partitions_geom.geometries.extend([feature.geometry for feature in partition.features if feature.geometry is not None])

    request_geoms = GeometryCollection(
        type="GeometryCollection",
        geometries=[feature.geometry for feature in request_geometry.features if feature.geometry is not None]
    )

    combined = FeatureCollection(
        type="FeatureCollection",
        features=[
            Feature(type="Feature", geometry=partitions_geom, properties={"name": "partitions"}),
            Feature(type="Feature", geometry=windows_geom, properties={"name": "windows"}),
            Feature(type="Feature", geometry=request_geoms, properties={"name": "request_geometry"}),
        ]
    )

    scratch.write_all_prediction_request_geometries_geojson(combined)

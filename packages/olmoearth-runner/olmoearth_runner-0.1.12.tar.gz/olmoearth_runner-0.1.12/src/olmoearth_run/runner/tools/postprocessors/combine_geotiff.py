import logging
import re
import tempfile
from collections import defaultdict
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import rasterio  # type: ignore[import-untyped]
from rasterio.merge import merge  # type: ignore[import-untyped]
from rasterio.session import GSSession, DummySession  # type: ignore[import-untyped]
from shapely.geometry import Polygon, box
from upath import UPath

from olmoearth_run.runner.tools.postprocessors.grid_utils import group_polygons_by_grid
from olmoearth_run.runner.tools.postprocessors.postprocess_interface import PostprocessInterfaceRaster
from olmoearth_shared.api.run.prediction_geometry import PredictionRequestFeature
from olmoearth_shared.tools.gcs_tools import is_gcs_path, write_file_to_gcs, download_gcs_files

logger = logging.getLogger(__name__)


@dataclass
class RasterMetadata:
    """Cached metadata for a GeoTIFF file."""
    path: UPath
    crs_string: str
    geometry: Polygon  # Shapely polygon representing raster bounds in CRS coordinate space
    pixel_size_x: float  # Resolution of x dimension. (1 pixel = K units in CRS). This is meters per pixel for UTM projections.
    pixel_size_y: float  # resolution of y dimension


class CombineGeotiff(PostprocessInterfaceRaster):
    def __init__(self, max_pixels_per_dimension: int = 10000, nodata_value: int | float = 0):
        self.max_pixels_per_dimension = max_pixels_per_dimension
        self.nodata_value = nodata_value

    def process_window(self, window_request: PredictionRequestFeature, window_result_path: UPath) -> None:
        raise NotImplementedError("CombineGeotiff does not support combining windows")

    def process_partition(self, partition_window_results: list[UPath], output_dir: UPath) -> list[UPath]:
        if not partition_window_results:
            return []
        return self._combine_geotiffs(partition_window_results, output_dir)

    def process_dataset(self, all_partitions_result_paths: list[UPath], output_dir: UPath) -> list[UPath]:
        if not all_partitions_result_paths:
            return []
        return self._combine_geotiffs(all_partitions_result_paths, output_dir)

    def _combine_geotiffs(self, input_paths: list[UPath], output_directory: UPath) -> list[UPath]:
        """
        Combine multiple GeoTIFF files, grouping by CRS and using grid-based tiling
        to avoid creating extremely large output files.
        """
        logger.info(f"Combining {len(input_paths)} rasters")

        if not input_paths:
            logger.warning("No input paths provided to CombineGeotiff")
            return []

        # Group input files by CRS. Since we cannot mix CRS in output files.
        all_metadata = [self._get_raster_metadata(p) for p in input_paths]
        crs_groups = self._group_by_crs(all_metadata)
        logger.info(f"Grouped {len(input_paths)} rasters into {len(crs_groups)} CRS groups: {list(crs_groups.keys())}")

        output_files = []

        # Process each CRS group independently
        for crs_string, metadata_list in crs_groups.items():
            # Sanitize CRS string for filename (e.g., EPSG:32610 -> epsg32610)
            crs_safe = re.sub(r'[^a-zA-Z0-9]', '', crs_string)
            logger.info(f"Processing CRS group {crs_string} with {len(metadata_list)} rasters")

            # Calculate max_size in coordinate units (use first raster's pixel size as reference)
            max_size = self.max_pixels_per_dimension * metadata_list[0].pixel_size_x

            # Group to ensure that we don't end up with any single output file over max_size
            grid_groups = group_polygons_by_grid(
                metadata_list,
                max_size,
                get_geometry=lambda m: m.geometry
            )

            logger.info(f"Assigned {len(metadata_list)} rasters to {len(grid_groups)} grid cells")

            # Merge each grid group into a single output raster. Downloading the files for each cell.
            for idx, ((grid_x, grid_y), metadata_items) in enumerate(grid_groups.items()):
                # Create output filename with CRS and grid coordinates
                output_filename = f"result_{crs_safe}_{idx}.tif"

                paths = [m.path for m in metadata_items]
                logger.info(f"Merging grid cell ({grid_x}, {grid_y}) with {len(paths)} rasters -> {output_filename}")

                # Merge the rasters in this grid cell
                with managed_raster_paths(paths, output_directory) as (local_paths, local_output_dir):
                    local_output = local_output_dir / output_filename
                    self._merge_grid_cell(local_paths, local_output)
                    output_files.extend(convert_outputs([local_output], output_directory))

        logger.info(f"Combined {len(input_paths)} rasters into {len(output_files)} output files")
        return output_files

    @staticmethod
    def _get_raster_metadata(input_path: UPath) -> RasterMetadata:
        """Loads the bounds/CRS for a GeoTIFF file, reading headers-only directly from GCS if needed."""
        session = GSSession() if is_gcs_path(str(input_path)) else DummySession()
        with rasterio.Env(session=session), rasterio.open(str(input_path)) as src:
            bounds = src.bounds
            return RasterMetadata(
                path=input_path,
                crs_string=src.crs.to_string().lower() if src.crs else "unknown",
                geometry=box(bounds.left, bounds.bottom, bounds.right, bounds.top),
                pixel_size_x=abs(src.transform[0]),
                pixel_size_y=abs(src.transform[4])
            )

    @staticmethod
    def _group_by_crs(metadata_list: list[RasterMetadata]) -> dict[str, list[RasterMetadata]]:
        """
        Returns dictionary mapping CRS string (e.g., 'EPSG:32610') to list of metadata objects
        """
        crs_groups: dict[str, list[RasterMetadata]] = defaultdict(list)
        for metadata in metadata_list:
            crs_groups[metadata.crs_string].append(metadata)
        return dict(crs_groups)

    def _merge_grid_cell(self, paths: list[Path], output_path: Path) -> None:
        """Merge a list of rasters into a single output GeoTIFF."""

        if len(paths) == 1:
            # Just one file, copy it and set nodata value
            logger.info(f"Only one raster in grid cell, copying directly: {paths[0]}")
            with rasterio.open(paths[0]) as src:
                meta = src.meta.copy()
                meta.update({
                    "nodata": self.nodata_value,
                    "compress": "lzw",
                })
                with rasterio.open(output_path, "w", **meta) as dst:
                    dst.write(src.read())
            return

        # Open all input rasters with proper cleanup
        with ExitStack() as stack:
            input_rasters = [stack.enter_context(rasterio.open(path)) for path in paths]

            merged_array, transform = merge(input_rasters, nodata=self.nodata_value)
            meta = input_rasters[0].meta.copy()
            meta.update({
                "driver": "GTiff",
                "height": merged_array.shape[1],
                "width": merged_array.shape[2],
                "transform": transform,
                "compress": "lzw",
                "nodata": self.nodata_value,
            })

            with rasterio.open(output_path, "w", **meta) as destination:
                destination.write(merged_array)

        logger.debug(f"Merged {len(paths)} rasters to {output_path}")


@contextmanager
def managed_raster_paths(input_paths: list[UPath], output_directory: UPath) -> Iterator[tuple[list[Path], Path]]:
    """Provides an abstraction to ensure input/output paths are local paths."""
    with tempfile.TemporaryDirectory() as temp_dir:
        local_inputs = convert_inputs_to_local(input_paths, temp_dir)
        if is_gcs_path(str(output_directory)):
            # If the ultimate output dir is GCS, then create a temp output dir. Results will get copied later.
            local_output_dir = Path(temp_dir) / "outputs"
            local_output_dir.mkdir(exist_ok=True)
            yield local_inputs, local_output_dir
        else:
            # If the ultimate output dir is local, we can write straight there!
            yield local_inputs, Path(str(output_directory))


def convert_inputs_to_local(input_files: list[UPath], temp_dir: str) -> list[Path]:
    """Copies GCS files to local temp dir, or just skips if the files are already local. """
    is_gcs = is_gcs_path(str(input_files[0]))
    if not is_gcs:
        # Local paths, pass through
        return [Path(str(p)) for p in input_files]

    temp_path = Path(temp_dir)
    temp_inputs_dir = temp_path / "inputs"
    temp_inputs_dir.mkdir()

    # Copy each input file to temp directory
    logger.info(f"Copying {len(input_files)} input rasters from GCS to local temp directory")
    local_input_paths = download_gcs_files([str(f) for f in input_files], temp_inputs_dir)
    return local_input_paths


def convert_outputs(local_output_files: list[Path], output_dir: UPath) -> list[UPath]:
    """Copies local output files to GCS if needed, or just returns local paths."""
    is_gcs = is_gcs_path(str(output_dir))
    if not is_gcs:
        return [UPath(f) for f in local_output_files]

    # Copy outputs back to GCS
    output_files = []
    for local_file in local_output_files:
        logger.info(f"Copying {local_file} to GCS {output_dir / local_file.name}...")
        write_file_to_gcs(str(local_file), str(output_dir / local_file.name))
        output_files.append(UPath(output_dir / local_file.name))
    return output_files

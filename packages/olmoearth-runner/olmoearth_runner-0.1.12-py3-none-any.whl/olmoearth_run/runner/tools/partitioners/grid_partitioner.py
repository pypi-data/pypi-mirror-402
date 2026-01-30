import logging

import math
from typing import cast

from rslearn.utils import Projection, STGeometry
from shapely import BufferJoinStyle
from shapely.geometry import box as shapely_box, shape, mapping
from shapely.geometry.base import BaseGeometry

from olmoearth_run.runner.tools.converters.st_geometry import STGeometryConverter
from olmoearth_run.runner.tools.partitioners.partition_interface import PartitionInterface
from olmoearth_shared.api.run.prediction_geometry import PredictionRequestCollection, PredictionRequestFeature

logger = logging.getLogger(__name__)


class GridPartitioner(PartitionInterface):
    def __init__(self, grid_size: float, overlap_size: float | None = None, output_projection: Projection | None = None, use_utm: bool = False, clip: bool = False):
        """
        Partitioner that splits geometries into a grid of smaller partitions.
        :param grid_size: The size of each grid cell in the units of the projection (this is in the units of the output_projection).
        :param overlap_size: The size of the overlap between adjacent cells. again, in units of output_projection.
        :param output_projection: The projection to use for the output geometries. If None, no re-projection will take place.
        :param use_utm: If True, the partitioner will use UTM projection for the output geometries. You must still
            provide an output_projection, but only the x_resolution/y_resolution will be used.  The CRS will be
            determined by the correct UTM zone.
        :param clip: If True, the partitioner will clip the output geometries to the input geometry. Otherwise, the produced
            grids might include areas outside the input geometry.
        """
        super().__init__(output_projection, use_utm)
        self.grid_size = grid_size
        self.overlap_size = overlap_size or 0
        self.clip = clip

    def _split_shapely_to_grid(self, geom: BaseGeometry) -> list[BaseGeometry]:
        x_start = math.floor(geom.bounds[0] / self.grid_size) * self.grid_size
        y_start = math.floor(geom.bounds[1] / self.grid_size) * self.grid_size

        x_end = math.ceil(geom.bounds[2] / self.grid_size) * self.grid_size
        y_end = math.ceil(geom.bounds[3] / self.grid_size) * self.grid_size
        out_list: list[BaseGeometry] = []
        x = x_start
        while x < x_end:
            y = y_start
            while y < y_end:
                cell: BaseGeometry = shapely_box(x, y, x + self.grid_size, y + self.grid_size)
                if self.overlap_size:
                    cell = cell.buffer(self.overlap_size, join_style=BufferJoinStyle.mitre)
                if self.clip:
                    cell = geom.intersection(cell)
                out_list.append(cell)
                y += self.grid_size
            x += self.grid_size
        return out_list

    def partition_request_geometry(self, request_extents: PredictionRequestCollection) -> list[PredictionRequestCollection]:
        """Splits the input geometries into a grid of smaller partitions in lat/lng space."""
        if not request_extents.features:
            return []
        logger.info(f"Creating partitions for {len(request_extents.features)} input features.")

        partitions: list[PredictionRequestCollection] = []
        for feature in request_extents.features:
            if not feature.geometry:
                continue
            geom = shape(feature.geometry.model_dump(mode='json'))
            for grid in self._split_shapely_to_grid(geom):
                partitions.append(
                    PredictionRequestCollection(
                        type="FeatureCollection",
                        features=[PredictionRequestFeature.model_validate({
                            'type': 'Feature', 'geometry': mapping(grid), 'properties': feature.properties
                        })]
                    )
                )
        logger.info(f"Created {len(partitions)} partitions from {len(request_extents.features)} input features.")

        return partitions

    def prepare_window_geometries(self, request_extents: PredictionRequestCollection) -> list[tuple[PredictionRequestFeature, STGeometry]]:
        """Apply projection transformations and overlap to already gridded geometries"""
        partitions: list[tuple[PredictionRequestFeature, STGeometry]] = []

        for feature in request_extents.features:
            # Convert feature to STGeometry and apply projection transformations
            geometry = STGeometryConverter.from_prediction_request_feature(feature)
            working_geometry = self._update_projection(geometry)

            geom = cast(BaseGeometry, working_geometry.shp)
            grids = self._split_shapely_to_grid(geom)
            for grid in grids:
                partitions.append((feature, STGeometry(working_geometry.projection, grid, working_geometry.time_range)))

        return partitions

    def __str__(self) -> str:
        return f"GridPartitioner(grid_size={self.grid_size}, overlap_size={self.overlap_size}, output_projection={self.output_projection}, use_utm={self.use_utm}, clip={self.clip})"

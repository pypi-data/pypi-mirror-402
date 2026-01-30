from typing import assert_never, cast

from olmoearth_run.runner.tools.data_splitters.data_splitter_interface import DataSplitterInterface
from olmoearth_run.runner.tools.data_splitters.random_data_splitter import RandomDataSplitter as RandomDataSplitterImpl
from olmoearth_run.runner.tools.data_splitters.spatial_data_splitter import SpatialDataSplitter as SpatialDataSplitterImpl
from olmoearth_run.runner.tools.labeled_window_preparers.labeled_window_preparer import LabeledWindowPreparer
from olmoearth_run.runner.tools.labeled_window_preparers.point_to_raster_window_preparer import PointToRasterWindowPreparer as PointToRasterWindowPreparerImpl
from olmoearth_run.runner.tools.labeled_window_preparers.polygon_to_raster_window_preparer import PolygonToRasterWindowPreparer as PolygonToRasterWindowPreparerImpl
from olmoearth_run.runner.tools.olmoearth_config.utils import ConfigUtils, OutputFieldUtils
from olmoearth_run.runner.tools.olmoearth_run_config_loader import OlmoEarthRunConfigLoader
from olmoearth_run.runner.tools.samplers.choose_n_sampler import ChooseNSampler as ChooseNSamplerImpl
from olmoearth_run.runner.tools.samplers.noop_sampler import NoopSampler as NoopSamplerImpl
from olmoearth_run.runner.tools.samplers.sampler_interface import SamplerInterface
from olmoearth_run.shared.models.olmoearth_run_config import OlmoEarthRunConfig
from olmoearth_shared.models.olmoearth_config.labeled_data_prep.data_splitter import RandomDataSplitter, SpatialDataSplitter
from olmoearth_shared.models.olmoearth_config.labeled_data_prep.samplers import NoopSampler, ChooseNSampler
from olmoearth_shared.models.olmoearth_config.labeled_data_prep.window_preparers import PointToRasterWindowPreparer, PolygonToRasterWindowPreparer
from olmoearth_shared.models.olmoearth_config.olmoearth_config import OlmoEarthConfig


class LabeledDataPrepClassLoader:
    @staticmethod
    def load_sampler(config: OlmoEarthRunConfig | OlmoEarthConfig) -> SamplerInterface:
        """Loads an annotation/task sampler instance based on provided config (legacy or unified)"""

        if isinstance(config, OlmoEarthRunConfig):
            return OlmoEarthRunConfigLoader.get_sampler(config)

        if not config.labeled_data_prep:
            raise ValueError("labeled_data_prep configuration is required for loading sampler")

        match config.labeled_data_prep.sampler:
            case NoopSampler():
                return NoopSamplerImpl()
            case ChooseNSampler(n=n):
                return ChooseNSamplerImpl(n=n)
            case unreachable:
                assert_never(unreachable)

    @staticmethod
    def load_data_splitter(config: OlmoEarthRunConfig | OlmoEarthConfig) -> DataSplitterInterface:
        """Loads a data splitter instance based on provided config (legacy or unified)."""
        if isinstance(config, OlmoEarthRunConfig):
            return OlmoEarthRunConfigLoader.get_data_splitter(config)

        if not config.labeled_data_prep:
            raise ValueError("labeled_data_prep configuration is required for loading data splitter")

        match config.labeled_data_prep.data_splitter:
            case RandomDataSplitter(seed=seed, train_prop=train_prop, val_prop=val_prop, test_prop=test_prop):
                return RandomDataSplitterImpl(seed=seed, train_prop=train_prop, val_prop=val_prop, test_prop=test_prop)
            case SpatialDataSplitter(grid_size=grid_size, train_prop=train_prop, val_prop=val_prop, test_prop=test_prop):
                return SpatialDataSplitterImpl(grid_size=grid_size, train_prop=train_prop, val_prop=val_prop, test_prop=test_prop)
            case unreachable:
                assert_never(unreachable)

    @staticmethod
    def load_labeled_window_preparer(config: OlmoEarthRunConfig | OlmoEarthConfig) -> LabeledWindowPreparer:
        """Loads a labeled window preparer instance based on provided config (legacy or unified)."""
        if isinstance(config, OlmoEarthRunConfig):
            return OlmoEarthRunConfigLoader.get_labeled_window_preparer(config)

        if not config.labeled_data_prep:
            raise ValueError("labeled_data_prep configuration is required for loading labeled window preparer")

        match config.labeled_data_prep.window_preparer:
            case PointToRasterWindowPreparer(window_buffer=window_buffer):
                output_field = ConfigUtils.get_raster_output_field(config)
                window_resolution = ConfigUtils.get_window_resolution(config)
                dtype = OutputFieldUtils.get_dtype_for_field(output_field)
                nodata_value = OutputFieldUtils.get_nodata_for_field(output_field)
                return PointToRasterWindowPreparerImpl(
                    window_buffer=window_buffer,
                    window_resolution=window_resolution,
                    dtype=dtype.value,
                    nodata_value=cast(int, nodata_value) if nodata_value is not None else 0,
                )
            case PolygonToRasterWindowPreparer():
                output_field = ConfigUtils.get_raster_output_field(config)
                window_resolution = ConfigUtils.get_window_resolution(config)
                nodata_value = OutputFieldUtils.get_nodata_for_field(output_field)
                return PolygonToRasterWindowPreparerImpl(
                    window_resolution=window_resolution,
                    nodata_value=cast(int, nodata_value) if nodata_value is not None else 0,
                )
            case unreachable:
                assert_never(unreachable)

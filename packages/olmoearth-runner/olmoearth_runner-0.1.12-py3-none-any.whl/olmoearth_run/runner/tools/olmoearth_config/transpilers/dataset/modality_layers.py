from datetime import timedelta
from typing import assert_never

from olmoearth_run.runner.models.operational_context import DataSource, DatasetOperationalContext
from olmoearth_shared.models.olmoearth_config.data.temporality import SampledTemporality, RepeatingIntervalTemporality, Temporality
from olmoearth_shared.models.olmoearth_config.data.modalities import SpaceMode as ModalitiesSpaceMode
from olmoearth_shared.models.olmoearth_config.olmoearth_config import OlmoEarthConfig
from olmoearth_shared.models.olmoearth_config.data.modalities import Sentinel2L2A, Sentinel2L2ASortBy
from olmoearth_run.runner.tools.olmoearth_config.constants import OLMOEARTH_SENTINEL2_L2A_BANDS, STAC_EO_CLOUD_COVER, SENTINEL2_L2A
from rslearn.config import dataset


class ModalityLayers:
    @staticmethod
    def generate_modality_layers(olmoearth_config: OlmoEarthConfig, ops_context: DatasetOperationalContext) -> dict[str, dataset.LayerConfig]:
        modality_layers: dict[str, dataset.LayerConfig] = {}

        if olmoearth_config.data.modalities.sentinel2_l2a:
            modality_layers[SENTINEL2_L2A] = ModalityLayers.generate_sentinel2_l2a_layer(olmoearth_config.data.modalities.sentinel2_l2a, olmoearth_config, ops_context)

        return modality_layers

    @staticmethod
    def generate_sentinel2_l2a_layer(s2_config: Sentinel2L2A, olmoearth_config: OlmoEarthConfig, ops_context: DatasetOperationalContext) -> dataset.LayerConfig:
        temporality = olmoearth_config.data.temporality

        match ops_context.data_source:
            case DataSource.PLANETARY_COMPUTER:
                data_source_config = dataset.DataSourceConfig(
                    class_path="rslearn.data_sources.planetary_computer.Sentinel2",
                    init_args=dict(
                        harmonize=True,  # is this ever not true for us?
                        sort_by=ConfigMappers.map_s2_sort_by(s2_config.sort_by),
                        cache_dir=OperationalUtils.choose_cache_dir(ops_context),
                        timeout=OperationalUtils.choose_planetary_computer_timeout(ops_context),
                    ),
                    query_config=dataset.QueryConfig(
                        # TODO: time mode?
                        space_mode=ConfigMappers.map_space_mode(s2_config.space_mode, temporality),
                        min_matches=TemporalityUtils.find_num_matches(temporality),
                        max_matches=TemporalityUtils.find_num_matches(temporality),
                        period_duration=TemporalityUtils.generate_period_duration(temporality),
                    ),
                    duration=TemporalityUtils.generate_duration(temporality),
                    ingest=False,
                )
            case _:
                assert_never(ops_context.data_source)

        bandsets = [
            dataset.BandSetConfig(
                bands=OLMOEARTH_SENTINEL2_L2A_BANDS,
                dtype=dataset.DType.UINT16,
            )
        ]

        return dataset.LayerConfig(
            type=dataset.LayerType.RASTER,
            data_source=data_source_config,
            band_sets=bandsets,
        )


class ConfigMappers:
    """Maps simplified unified config values into rslearn settings."""
    @staticmethod
    def map_space_mode(space_mode: ModalitiesSpaceMode, temporality: Temporality) -> dataset.SpaceMode:
        match space_mode:
            case ModalitiesSpaceMode.CONTAINS:
                return dataset.SpaceMode.CONTAINS
            case ModalitiesSpaceMode.MOSAIC:
                match temporality:
                    case SampledTemporality():
                        return dataset.SpaceMode.MOSAIC
                    case RepeatingIntervalTemporality():
                        return dataset.SpaceMode.PER_PERIOD_MOSAIC
                    case _ as unreachable:
                        assert_never(unreachable)
            case _ as unreachable:
                assert_never(unreachable)

    @staticmethod
    def map_s2_sort_by(sort_by: Sentinel2L2ASortBy) -> str:
        match sort_by:
            case Sentinel2L2ASortBy.CLOUD_COVER:
                return STAC_EO_CLOUD_COVER
            case _:
                assert_never(sort_by)


class TemporalityUtils:
    @staticmethod
    def find_num_matches(temporality: Temporality) -> int:
        match temporality:
            case SampledTemporality():
                return temporality.num_samples
            case RepeatingIntervalTemporality():
                return temporality.num_periods
            case _:
                assert_never(temporality)


    @staticmethod
    def generate_period_duration(temporality: Temporality) -> timedelta:
        """Generates the period duration to be used when using a per-period mosaic."""
        match temporality:
            case SampledTemporality():
                # Period duration isn't nullable in the dataset.QueryConfig spec,
                # so we need to set this to some value even if it goes unused for this temporality.
                return timedelta(days=0)
            case RepeatingIntervalTemporality():
                return timedelta(days=temporality.period_duration_days)
            case _:
                assert_never(temporality)

    @staticmethod
    def generate_duration(temporality: Temporality) -> timedelta:
        """Generates the duration to be used when using a sampled temporality."""
        match temporality:
            case SampledTemporality():
                return timedelta(days=temporality.duration_days)
            case RepeatingIntervalTemporality():
                return timedelta(days=temporality.period_duration_days * temporality.num_periods)
            case _:
                assert_never(temporality)


class OperationalUtils:
    @staticmethod
    def choose_planetary_computer_timeout(ops_context: DatasetOperationalContext) -> str:
        """Gets the timeout to be used when using the Planetary Computer data source."""
        # Has access to ops context to make decisions about timeout
        # Return in h:m:s format (required by rslearn's jsonargparse)
        return "0:0:10"

    @staticmethod
    def choose_cache_dir(ops_context: DatasetOperationalContext) -> str:
        # Has access to ops context to make decisions about cache directory
        return "cache/planetary_computer"

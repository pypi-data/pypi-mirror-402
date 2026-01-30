from prometheus_client import Counter, Histogram
from prometheus_client.utils import INF

_DATASET_BUILDER_DURATION_HISTOGRAM_BUCKETS = (
    5.0,
    10.0,
    15.0,
    20.0,
    30.0,
    40.0,
    50.0,
    60.0,  # 1 minute
    75.0,  # 1m 15s
    90.0,  # 1m 30s
    105.0,  # 1m 45s
    120.0,  # 2 minutes
    180.0,  # 3 minutes
    240.0,  # 4 minutes
    300.0,  # 5 minutes
    360.0,  # 6 minutes
    420.0,  # 7 minutes
    480.0,  # 8 minutes
    540.0,  # 9 minutes
    600.0,  # 10 minutes
    900.0,  # 15 minutes
    1200.0,  # 20 minutes
    1500.0,  # 25 minutes
    1800.0,  # 30 minutes
    2100.0,  # 35 minutes
    2400.0,  # 40 minutes
    2700.0,  # 45 minutes
    3000.0,  # 50 minutes
    3600.0,  # 1 hour
    4200.0,  # 1h 10m
    4800.0,  # 1h 20m
    5400.0,  # 1h 30m
    6000.0,  # 1h 40m
    6600.0,  # 1h 50m
    7200.0,  # 2 hours
    9000.0,  # 2h 30m
    10800.0,  # 3 hours
    12600.0,  # 3h 30m
    14400.0,  # 4 hours
    16200.0,  # 4h 30m
    18000.0,  # 5 hours
    19800.0,  # 5h 30m
    21600.0,  # 6 hours
    23400.0,  # 6h 30m
    25200.0,  # 7 hours
    27000.0,  # 7h 30m
    28800.0,  # 8 hours
    INF,
)


# Private Prometheus metrics
_load_windows_loaded_counter = Counter(
    'runner_dataset_builder_loading_windows_loaded_total',
    'Number of windows loaded',
)

_prepare_windows_processed_counter = Counter(
    'runner_dataset_builder_prepare_windows_processed_total',
    'Number of windows processed for preparation',
)

_prepare_window_layers_handled_counter = Counter(
    'runner_dataset_builder_prepare_layers_windows_handled_total',
    'Number of window layers handled per data source, with skipped status',
    labelnames=['data_source', 'skipped'],
)

_prepare_window_layers_handle_attempts_counter = Counter(
    'runner_dataset_builder_prepare_layers_windows_handle_attempts_total',
    'Number of attempts to handle window layers per data source',
    labelnames=['data_source'],
)

_prepare_window_rejection_ratio_error_counter = Counter(
    'runner_dataset_builder_prepare_rejection_ratio_error_total',
    'Number of times window success rate fell below threshold',
)

_ingest_jobs_processed_counter = Counter(
    'runner_dataset_builder_ingest_jobs_processed_total',
    'Number of jobs processed for ingestion',
)

_ingest_geometries_ingested_counter = Counter(
    'runner_dataset_builder_ingest_geometries_ingested_total',
    'Number of geometries ingested, by data source, with outcome',
    labelnames=['data_source', 'outcome'],
)

_materialize_windows_processed_counter = Counter(
    'runner_dataset_builder_materialize_windows_processed_total',
    'Number of windows processed for materialization',
)

_materialize_window_layers_materialized_counter = Counter(
    'runner_dataset_builder_materialize_layers_windows_materialized_total',
    'Number of window layers materialized, by data source',
    labelnames=['data_source'],
)

_materialize_window_layers_materialize_attempts_counter = Counter(
    'runner_dataset_builder_materialize_layers_windows_materialize_attempts_total',
    'Number of attempts to materialize window layers, by data source',
    labelnames=['data_source'],
)

# Duration histograms
_prepare_layer_duration_histogram = Histogram(
    'runner_dataset_builder_prepare_layer_duration_seconds',
    'Duration in seconds per layer for prepare operations',
    labelnames=['data_source'],
    buckets=_DATASET_BUILDER_DURATION_HISTOGRAM_BUCKETS,
)

_prepare_duration_histogram = Histogram(
    'runner_dataset_builder_prepare_duration_seconds',
    'Duration in seconds for prepare operations',
    buckets=_DATASET_BUILDER_DURATION_HISTOGRAM_BUCKETS,
)

_ingest_layer_duration_histogram = Histogram(
    'runner_dataset_builder_ingest_layer_duration_seconds',
    'Duration in seconds per layer for ingest operations',
    labelnames=['data_source'],
    buckets=_DATASET_BUILDER_DURATION_HISTOGRAM_BUCKETS,
)

_ingest_duration_histogram = Histogram(
    'runner_dataset_builder_ingest_duration_seconds',
    'Duration in seconds for ingest operations',
    buckets=_DATASET_BUILDER_DURATION_HISTOGRAM_BUCKETS,
)

_materialize_layer_duration_histogram = Histogram(
    'runner_dataset_builder_materialize_layer_duration_seconds',
    'Duration in seconds per layer for materialize operations',
    labelnames=['data_source'],
    buckets=_DATASET_BUILDER_DURATION_HISTOGRAM_BUCKETS,
)

_materialize_duration_histogram = Histogram(
    'runner_dataset_builder_materialize_duration_seconds',
    'Duration in seconds for materialize operations',
    buckets=_DATASET_BUILDER_DURATION_HISTOGRAM_BUCKETS,
)


class DatasetBuilderMetrics:
    """Metrics for dataset building operations."""

    @staticmethod
    def record_windows_loaded(count: int) -> None:
        """Record windows loaded."""
        _load_windows_loaded_counter.inc(count)

    @staticmethod
    def record_windows_processed(count: int) -> None:
        """Record windows processed for preparation."""
        _prepare_windows_processed_counter.inc(count)

    @staticmethod
    def record_window_layers_handled(data_source: str, skipped: bool, count: int) -> None:
        """Record window layers handled per data source."""
        _prepare_window_layers_handled_counter.labels(
            data_source=data_source,
            skipped=str(skipped)
        ).inc(count)

    @staticmethod
    def record_window_layers_handle_attempts(data_source: str, count: int) -> None:
        """Record attempts to handle window layers."""
        _prepare_window_layers_handle_attempts_counter.labels(
            data_source=data_source
        ).inc(count)

    @staticmethod
    def record_window_rejection_ratio_error(count: int) -> None:
        """Record when window success rate falls below threshold."""
        _prepare_window_rejection_ratio_error_counter.inc(count)

    @staticmethod
    def record_ingest_jobs_processed(count: int) -> None:
        """Record ingestion jobs processed."""
        _ingest_jobs_processed_counter.inc(count)

    @staticmethod
    def record_geometries_ingested(data_source: str, outcome: str, count: int) -> None:
        """Record geometries ingested."""
        _ingest_geometries_ingested_counter.labels(
            data_source=data_source,
            outcome=outcome
        ).inc(count)

    @staticmethod
    def record_windows_materialized(count: int) -> None:
        """Record windows processed for materialization."""
        _materialize_windows_processed_counter.inc(count)

    @staticmethod
    def record_window_layers_materialized(data_source: str, count: int) -> None:
        """Record window layers materialized."""
        _materialize_window_layers_materialized_counter.labels(
            data_source=data_source
        ).inc(count)

    @staticmethod
    def record_window_layers_materialize_attempts(data_source: str, count: int) -> None:
        """Record attempts to materialize window layers."""
        _materialize_window_layers_materialize_attempts_counter.labels(
            data_source=data_source
        ).inc(count)

    @staticmethod
    def record_prepare_layer_duration(data_source: str, duration: float) -> None:
        """Record per-layer prepare operation duration."""
        _prepare_layer_duration_histogram.labels(data_source=data_source).observe(duration)

    @staticmethod
    def record_prepare_duration(duration: float) -> None:
        """Record overall prepare operation duration."""
        _prepare_duration_histogram.observe(duration)

    @staticmethod
    def record_ingest_layer_duration(data_source: str, duration: float) -> None:
        """Record per-layer ingest operation duration."""
        _ingest_layer_duration_histogram.labels(data_source=data_source).observe(duration)

    @staticmethod
    def record_ingest_duration(duration: float) -> None:
        """Record overall ingest operation duration."""
        _ingest_duration_histogram.observe(duration)

    @staticmethod
    def record_materialize_layer_duration(data_source: str, duration: float) -> None:
        """Record per-layer materialize operation duration."""
        _materialize_layer_duration_histogram.labels(data_source=data_source).observe(duration)

    @staticmethod
    def record_materialize_duration(duration: float) -> None:
        """Record overall materialize operation duration."""
        _materialize_duration_histogram.observe(duration)

import logging
import multiprocessing
from datetime import timedelta
from pathlib import Path
from typing import Callable, TypeVar

from rslearn.dataset import Dataset, Window
from rslearn.main import IngestHandler, MaterializeHandler, PrepareHandler
from rslearn.dataset.handler_summaries import PrepareDatasetWindowsSummary, IngestDatasetJobsSummary, IngestCounts, MaterializeDatasetWindowsSummary

from olmoearth_run.config import OlmoEarthSettings
from olmoearth_run.runner.metrics.dataset_builder import DatasetBuilderMetrics
from olmoearth_shared.tools.gcs_tools import is_gcs_path, get_gcs_directory_size_mb


logger = logging.getLogger(__name__)


RETRY_MAX_ATTEMPTS = 10
RETRY_BACKOFF = timedelta(seconds=30)


class DatasetBuilder:
    """
    Tool for building datasets by running prepare, ingest, and materialize operations on windows.
    Encapsulates the common dataset building workflow used across different step definitions.
    """

    def __init__(
        self,
        dataset: Dataset,
        retry_max_attempts: int = RETRY_MAX_ATTEMPTS,
        retry_backoff: timedelta = RETRY_BACKOFF,
        num_workers: int = OlmoEarthSettings.NUM_WORKERS,
        min_window_success_rate: float | None = None,
    ):
        """
        Initialize the DatasetBuilder.

        Args:
            dataset: The Dataset object to build
            retry_max_attempts: Maximum number of retry attempts for operations
            retry_backoff: Time to wait between retries
            num_workers: Number of worker processes to use (defaults to CPU count)
            min_window_success_rate: Minimum required ratio of non-rejected windows (prepared + skipped) to total windows.
                If None, the check is skipped.
        """
        self.dataset = dataset
        self.retry_max_attempts = retry_max_attempts
        self.retry_backoff = retry_backoff
        self.workers = num_workers
        self.min_window_success_rate = min_window_success_rate

        # Initialize internal counters state
        self._total_windows_to_prepare = 0
        self._total_jobs_to_ingest = 0
        self._total_windows_to_materialize = 0
        self._num_windows_prepared = 0
        self._num_jobs_ingested = 0
        self._num_windows_materialized = 0

        logger.debug(f"DatasetBuilder initialized with {self.workers} workers")

    def build_dataset(self, windows: list[Window]) -> None:
        """
        Build the dataset by running prepare, ingest, and materialize operations on the given windows.

        Args:
            windows: List of windows to process
        """
        if not windows:
            logger.warning("No windows provided to build dataset")
            return

        logger.info(f"Building dataset with {len(windows)} windows")
        dataset_windows = [[window] for window in windows]

        # Run the three-phase dataset building process
        self._prepare_windows(dataset_windows)
        self._ingest_windows(windows)
        self._materialize_windows(dataset_windows)

        logger.info(f"Dataset build completed successfully for {len(windows)} windows")

    def _prepare_windows(self, dataset_windows: list[list[Window]]) -> None:
        """Run the prepare phase on the dataset windows."""
        prepare_handler = PrepareHandler(
            force=False,
            retry_max_attempts=self.retry_max_attempts,
            retry_backoff=self.retry_backoff,
        )
        prepare_handler.set_dataset(self.dataset)

        self._total_windows_to_prepare = len(dataset_windows)
        self._num_windows_prepared = 0

        logger.debug(f"Preparing {self._total_windows_to_prepare} windows")

        # Accumulate rejection statistics across all summaries
        total_prepared = 0
        total_skipped = 0
        total_rejected = 0

        with multiprocessing.Pool(self.workers) as pool:
            work_items = [(prepare_handler, windows) for windows in dataset_windows]
            for prepare_summary in pool.imap_unordered(pool_worker_wrapper, work_items):
                self._num_windows_prepared += prepare_summary.total_windows_requested
                self._emit_prepare_windows_summary(prepare_summary)

                # Accumulate counts from all layer summaries
                for layer_summary in prepare_summary.layer_summaries:
                    total_prepared += layer_summary.windows_prepared
                    total_skipped += layer_summary.windows_skipped
                    total_rejected += layer_summary.windows_rejected

        logger.debug(f"Finished preparing {len(dataset_windows)} windows")

        # Check success rate if threshold is set
        if self.min_window_success_rate is not None:
            total = total_prepared + total_skipped + total_rejected
            if total == 0:
                # No windows processed, success rate is 1.0 (100%)
                success_rate = 1.0
            else:
                success_rate = (total_prepared + total_skipped) / total

            if success_rate < self.min_window_success_rate:
                DatasetBuilderMetrics.record_window_rejection_ratio_error(1)
                raise ValueError(
                    f"Window success rate {success_rate:.2%} is below threshold {self.min_window_success_rate:.2%}. "
                    f"Rejected: {total_rejected}, Prepared: {total_prepared}, Skipped: {total_skipped}"
                )

    def _ingest_windows(self, windows: list[Window]) -> None:
        """Run the ingest phase on the windows."""
        ingest_handler = IngestHandler(
            retry_max_attempts=self.retry_max_attempts,
            retry_backoff=self.retry_backoff,
        )
        ingest_handler.set_dataset(self.dataset)

        # Get jobs for ingestion
        jobs = ingest_handler.get_jobs(windows, self.workers)
        self._total_jobs_to_ingest = len(jobs)
        self._num_jobs_ingested = 0

        logger.debug(f"Starting ingestion for {len(jobs)} job windows")
        with multiprocessing.Pool(self.workers) as pool:
            work_items = [(ingest_handler, [job]) for job in jobs]
            for ingest_summary in pool.imap_unordered(pool_worker_wrapper, work_items):
                self._num_jobs_ingested += ingest_summary.num_jobs
                self._emit_ingest_jobs_summary(ingest_summary)
        logger.debug(f"Finished ingestion for {len(jobs)} windows")

    def _materialize_windows(self, dataset_windows: list[list[Window]]) -> None:
        """Run the materialize phase on the dataset windows."""
        materialize_handler = MaterializeHandler(
            retry_max_attempts=self.retry_max_attempts,
            retry_backoff=self.retry_backoff,
        )
        materialize_handler.set_dataset(self.dataset)

        self._total_windows_to_materialize = len(dataset_windows)
        self._num_windows_materialized = 0

        logger.debug(f"Materializing {self._total_windows_to_materialize} windows")
        with multiprocessing.Pool(self.workers) as pool:
            work_items = [(materialize_handler, windows) for windows in dataset_windows]
            for materialize_summary in pool.imap_unordered(pool_worker_wrapper, work_items):
                if isinstance(materialize_summary, MaterializeDatasetWindowsSummary):
                    self._num_windows_materialized += materialize_summary.total_windows_requested
                    self._emit_materialize_windows_summary(materialize_summary)
        logger.debug(f"Finished materializing {len(dataset_windows)} windows")

    def _emit_prepare_windows_summary(self, prepare_summary: PrepareDatasetWindowsSummary) -> None:
        """Emit metrics for the prepare windows summary."""
        DatasetBuilderMetrics.record_windows_processed(prepare_summary.total_windows_requested)
        DatasetBuilderMetrics.record_prepare_duration(prepare_summary.duration_seconds)

        if self._total_windows_to_prepare == 0:
            percent_complete = 100.0
        else:
            percent_complete = self._num_windows_prepared / self._total_windows_to_prepare * 100
        logger.info(f"Prepare percent complete: {percent_complete}")

        for layer_summary in prepare_summary.layer_summaries:
            data_source_name = layer_summary.data_source_name

            DatasetBuilderMetrics.record_prepare_layer_duration(data_source_name, layer_summary.duration_seconds)
            DatasetBuilderMetrics.record_window_layers_handled(data_source_name, skipped=False, count=layer_summary.windows_prepared)
            DatasetBuilderMetrics.record_window_layers_handled(data_source_name, skipped=True, count=layer_summary.windows_skipped)
            DatasetBuilderMetrics.record_window_layers_handle_attempts(data_source_name, count=layer_summary.get_items_attempts)

    def _emit_ingest_jobs_summary(self, ingest_summary: IngestDatasetJobsSummary) -> None:
        """Emit metrics for the ingest jobs summary."""
        DatasetBuilderMetrics.record_ingest_jobs_processed(ingest_summary.num_jobs)
        DatasetBuilderMetrics.record_ingest_duration(ingest_summary.duration_seconds)

        if self._total_jobs_to_ingest == 0:
            percent_complete = 100.0
        else:
            percent_complete = self._num_jobs_ingested / self._total_jobs_to_ingest * 100
        logger.info(f"Ingest percent complete: {percent_complete}")

        for layer_summary in ingest_summary.layer_summaries:
            data_source_name = layer_summary.data_source_name
            DatasetBuilderMetrics.record_ingest_layer_duration(data_source_name, layer_summary.duration_seconds)
            if isinstance(layer_summary.ingest_counts, IngestCounts):
                DatasetBuilderMetrics.record_geometries_ingested(data_source_name, outcome="success", count=layer_summary.ingest_counts.geometries_ingested)
            else:
                DatasetBuilderMetrics.record_geometries_ingested(data_source_name, outcome="unknown", count=layer_summary.ingest_counts.geometries_attempted)

    def _emit_materialize_windows_summary(self, materialize_summary: MaterializeDatasetWindowsSummary) -> None:
        """Emit metrics for the materialize windows summary."""
        DatasetBuilderMetrics.record_windows_materialized(materialize_summary.total_windows_requested)
        DatasetBuilderMetrics.record_materialize_duration(materialize_summary.duration_seconds)

        if self._total_windows_to_materialize == 0:
            percent_complete = 100.0
        else:
            percent_complete = self._num_windows_materialized / self._total_windows_to_materialize * 100
        logger.info(f"Materialize percent complete: {percent_complete}")

        for layer_summary in materialize_summary.layer_summaries:
            data_source_name = layer_summary.data_source_name
            DatasetBuilderMetrics.record_materialize_layer_duration(data_source_name, layer_summary.duration_seconds)
            DatasetBuilderMetrics.record_window_layers_materialized(data_source_name, count=layer_summary.num_windows_materialized)
            # Record skipped windows (total requested - materialized)
            skipped_count = layer_summary.total_windows_requested - layer_summary.num_windows_materialized
            if skipped_count > 0:
                DatasetBuilderMetrics.record_window_layers_materialized(data_source_name, count=skipped_count)
            DatasetBuilderMetrics.record_window_layers_materialize_attempts(data_source_name, count=layer_summary.materialize_attempts)

    def get_partition_size_mb(self, partition_dir: str) -> float:
        """Calculate total size of partition directory in megabytes (local or GCS)."""
        if is_gcs_path(partition_dir):
            total_mb = get_gcs_directory_size_mb(partition_dir)
        else:
            total_mb = self._get_local_directory_size_mb(partition_dir)

        logger.info(f"Partition {partition_dir} size: {total_mb:.2f} MB")
        return total_mb

    def _get_local_directory_size_mb(self, directory: str) -> float:
        """Calculate total size of local directory in megabytes."""
        path = Path(directory)

        if not path.exists() or not path.is_dir():
            logger.warning(f"Invalid local directory: {directory}")
            return 0.0

        total_bytes = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        return total_bytes / (1024 * 1024)


WorkItemT = TypeVar("WorkItemT")
ResultT = TypeVar("ResultT")


def pool_worker_wrapper(args: tuple[Callable[[WorkItemT], ResultT], WorkItemT]) -> ResultT:
    """
    Guard against `sys.exit()` calls in worker processes.

    `multiprocessing.Pool.imap_unordered` hangs forever when a worker process calls
    `sys.exit()`, rather than raising an exception to the parent process. This wrapper
    catches the exit and raises a `RuntimeError`, which will propagate.

    This particularly targets rslearn's use of `jsonargparse`, which calls `sys.exit()`
    on misconfiguration errors.

    For the multiyear discussion on this python issue, see:
    https://bugs.python.org/issue42849
    https://bugs.python.org/issue38084
    """
    handler, work_item = args
    try:
        return handler(work_item)
    except SystemExit as e:
        raise RuntimeError(f"Worker process called sys.exit({e.code}).") from e

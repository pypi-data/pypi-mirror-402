from prometheus_client import Counter


# Private Prometheus metrics
_annotation_tasks_processed_counter = Counter(
    'runner_window_prep_annotation_tasks_processed_total',
    'Number of annotation tasks processed',
)

_labeled_windows_prepared_counter = Counter(
    'runner_window_prep_labeled_windows_prepared_total',
    'Number of windows prepared with labels',
)


class WindowPrepMetrics:
    """Metrics for window preparation operations."""

    @staticmethod
    def record_annotation_tasks_processed(count: int) -> None:
        """Record annotation tasks processed."""
        _annotation_tasks_processed_counter.inc(count)

    @staticmethod
    def record_labeled_windows_prepared(count: int) -> None:
        """Record labeled windows prepared."""
        _labeled_windows_prepared_counter.inc(count)

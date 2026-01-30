"""
Prometheus telemetry setup for Python applications.
"""

import logging
import shutil
from collections.abc import Callable
from pathlib import Path

from prometheus_client import REGISTRY, CollectorRegistry, make_asgi_app, multiprocess, start_http_server

logger = logging.getLogger(__name__)


def _get_registry(multiproc_dir: str | None = None) -> CollectorRegistry:
    """
    Get the appropriate Prometheus registry for the current environment.

    Automatically detects whether to use multiprocess mode based on multiproc_dir:
    - If set: Returns a registry with MultiProcessCollector for aggregating metrics from multiple processes
    - If not set: Returns the default single-process registry

    """
    if multiproc_dir is not None:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        return registry

    return REGISTRY


def initialize_multiproc_dir(multiproc_dir: str | None = None) -> None:
    """
    Clean up and recreate the multiprocess directory.

    This should be called ONCE at application startup, before any workers/processes are spawned.
    Do NOT call this in worker processes as it will delete metrics from other workers.
    """
    if multiproc_dir is not None:
        multiproc_path = Path(multiproc_dir)
        if multiproc_path.exists():
            shutil.rmtree(multiproc_path)
        multiproc_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Cleaned up multiprocess metrics directory: {multiproc_path}")


def make_metrics_app(multiproc_dir: str | None = None) -> Callable:
    """
    Create an ASGI metrics app that can be mounted in FastAPI at an arbitrary path.

    Note: In multiprocess mode, this should be called by each worker process. The multiproc directory
    should be initialized once at startup (e.g., in Gunicorn's on_starting hook) before workers spawn.
    """
    registry = _get_registry(multiproc_dir)
    return make_asgi_app(registry=registry)


_metrics_server_initialized = False


def make_standalone_metrics_server(multiproc_dir: str | None = None, metrics_server_port: int = 9090) -> None:
    """
    Initialize Prometheus and start standalone metrics server at the root path.

    In multiprocess mode, this cleans up the multiproc directory before starting the server.
    This should be called once in the main process before any child processes are spawned.
    """

    global _metrics_server_initialized

    if _metrics_server_initialized:
        logger.warning("Prometheus metrics server already initialized. Skipping initialization.")
        return

    initialize_multiproc_dir(multiproc_dir)
    registry = _get_registry(multiproc_dir)
    start_http_server(port=metrics_server_port, addr='0.0.0.0', registry=registry)
    _metrics_server_initialized = True

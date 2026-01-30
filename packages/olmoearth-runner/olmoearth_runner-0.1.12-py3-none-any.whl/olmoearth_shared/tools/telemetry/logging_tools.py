"""Structured logging configuration with Google Cloud JSON formatting."""
import json
import logging
import sys
from datetime import UTC, datetime
from os import environ
from typing import Any


class GoogleCloudJsonFormatter(logging.Formatter):
    """
    Custom JSON formatter that formats log records according to Google Cloud Logging structure.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "thread": record.thread,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add any extra fields from the log record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                          'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
                          'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'message']:
                log_entry[key] = value

        return json.dumps(log_entry)

HUMAN_LOG_FORMAT = '%(asctime)s %(process)d %(name)s %(levelname)s: %(message)s'
USE_HUMAN_LOG_FORMAT = environ.get('USE_HUMAN_FORMAT', 'false').lower() == 'true'


def get_log_level_from_env() -> int:
    """
    Parse LOG_LEVEL environment variable and return the corresponding logging level.

    Returns:
        logging level constant (default: logging.INFO)
    """
    log_level_str = environ.get("LOG_LEVEL", "INFO").upper()
    return logging._nameToLevel.get(log_level_str, logging.INFO)


def configure_logging(log_level: int | None = None) -> None:
    """
    Configure logging for the entire olmoearth-run application with Google Cloud JSON formatting.

    Args:
        log_level: The logging level to use. If None, reads from LOG_LEVEL env var (default: INFO)
    """
    if log_level is None:
        log_level = get_log_level_from_env()
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Use Google Cloud JSON formatter
    formatter: logging.Formatter = GoogleCloudJsonFormatter()
    if USE_HUMAN_LOG_FORMAT:
        formatter = logging.Formatter(HUMAN_LOG_FORMAT)
    console_handler.setFormatter(formatter)

    # Get/set the root loggers for olmoearth_run (et al.)
    for logger_name in ["alembic", "gunicorn", "gunicorn.access", "gunicorn.error", "olmoearth_run", "rq.worker", "rslearn", "uvicorn"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)

        # Remove any existing handlers to avoid duplicates
        logger.handlers.clear()

        # Add our handler
        logger.addHandler(console_handler)

        # Prevent propagation to avoid duplicate logs
        logger.propagate = False

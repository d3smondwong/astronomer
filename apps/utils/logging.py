"""
Logging configuration module for the Astronomer project.
Handles log file creation and setup with both file and console output.
"""

import logging
import os
from contextvars import ContextVar
from datetime import datetime

# Per-request log context. Set per request (e.g. from incoming X-* headers) so every
# log line emitted while handling it can be traced across modules — and, via the same
# headers, across the Next.js → FastAPI hop. All default to "-" when absent (e.g. a
# guest has no uid; a direct/non-HTTP invocation has none of these).
#   request_id — correlation id for this single request (browser → Next → FastAPI → LLM)
#   profile_id — the profile being created/viewed (the user's URL anchor)
#   uid        — Firebase account id ("-" for guests)
#   chart_key  — deterministic birth-input hash; the cross-path natal↔insights join key
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
profile_id_var: ContextVar[str] = ContextVar("profile_id", default="-")
uid_var: ContextVar[str] = ContextVar("uid", default="-")
chart_key_var: ContextVar[str] = ContextVar("chart_key", default="-")

_LOG_FORMAT = (
    "%(asctime)s [%(levelname)s] [req:%(request_id)s] [pid:%(profile_id)s] "
    "[uid:%(uid)s] [chart:%(chart_key)s] [%(filename)s:%(lineno)d] %(message)s"
)


class LogContextFilter(logging.Filter):
    """Stamps every log record with the current request context from the contextvars."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.profile_id = profile_id_var.get()
        record.uid = uid_var.get()
        record.chart_key = chart_key_var.get()
        return True


def configure_logging(log_level=logging.INFO, logs_base_dir="logs"):
    """
    Configure logging with timestamped log directory structure.

    Creates logs in: logs/YYYY-MM-DD/HH-MM-SS/app.log
    Outputs to both file and console (stream).

    Args:
        log_level: Logging level (default: logging.INFO)
        logs_base_dir: Base directory for logs (default: "logs")

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create log directory structure: logs/YYYY-MM-DD/HH-MM-SS/
    now = datetime.now()
    log_dir = os.path.join(
        logs_base_dir, now.strftime("%Y-%m-%d"), now.strftime("%H-%M-%S")
    )
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "app.log")

    # Configure logging with file handler
    # Clear any existing handlers to prevent duplicates
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    log_context_filter = LogContextFilter()

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    file_handler.addFilter(log_context_filter)

    # Stream handler (console output / stdout — captured by Cloud Logging on Cloud Run)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    stream_handler.addFilter(log_context_filter)

    # Set root logger level and add handlers
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    root_logger.info(f"Logging initialized - logs directory: {log_dir}")
    return root_logger


def get_logger(name):
    """
    Get a logger instance with the given name.

    Args:
        name: Module name (typically __name__)

    Returns:
        logging.Logger: Logger instance for the module
    """
    return logging.getLogger(name)

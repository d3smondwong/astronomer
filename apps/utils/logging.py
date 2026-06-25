"""
Logging configuration module for the Astronomer project.
Handles log file creation and setup with both file and console output.
"""

import json
import logging
import os
import sys
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


# Python level name -> Cloud Logging severity (https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#LogSeverity)
_GCP_SEVERITY = {
    "DEBUG": "DEBUG",
    "INFO": "INFO",
    "WARNING": "WARNING",
    "ERROR": "ERROR",
    "CRITICAL": "CRITICAL",
}


class GcpJsonFormatter(logging.Formatter):
    """Format records as single-line JSON for Cloud Logging (Cloud Run stdout).

    Emits the GCP special fields (``severity``, ``message``, sourceLocation) plus the
    request-context fields as top-level keys, so each becomes a queryable
    ``jsonPayload.<field>`` — e.g. ``jsonPayload.chart_key="9f3a…"`` for a support
    lookup, or ``severity>=ERROR`` for the backend-error alert. Relies on
    ``LogContextFilter`` having already stamped the context onto the record.
    """

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if record.exc_info:
            # Append the traceback so the stack is visible in the log entry (and picked
            # up by Error Reporting). formatException is cached on the record by stdlib.
            message = f"{message}\n{self.formatException(record.exc_info)}"

        payload = {
            "severity": _GCP_SEVERITY.get(record.levelname, "DEFAULT"),
            "message": message,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "profile_id": getattr(record, "profile_id", "-"),
            "uid": getattr(record, "uid", "-"),
            "chart_key": getattr(record, "chart_key", "-"),
            # GCP special field — surfaces file/line/function in the log entry UI.
            "logging.googleapis.com/sourceLocation": {
                "file": record.filename,
                "line": str(record.lineno),
                "function": record.funcName,
            },
        }
        # ensure_ascii=False so Chinese in BaZi log messages stays readable, not \uXXXX.
        return json.dumps(payload, ensure_ascii=False)


def _use_json_logs() -> bool:
    """Whether the console/stream handler should emit JSON (vs human-readable text).

    JSON in production (so Cloud Logging parses severity + fields), text locally (so the
    dev console stays readable). Auto-detects Cloud Run via the ``K_SERVICE`` env var,
    overridable with ``LOG_FORMAT=json|text``.
    """
    fmt = os.environ.get("LOG_FORMAT", "").strip().lower()
    if fmt == "json":
        return True
    if fmt == "text":
        return False
    return bool(os.environ.get("K_SERVICE"))  # set by the Cloud Run runtime


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

    # File handler — always human-readable text (local app.log, for dev/debug).
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    file_handler.addFilter(log_context_filter)

    # Stream handler → stdout, captured by Cloud Logging on Cloud Run. JSON in production
    # (parsed severity + queryable jsonPayload fields), text locally (readable console).
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(
        GcpJsonFormatter() if _use_json_logs() else logging.Formatter(_LOG_FORMAT)
    )
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

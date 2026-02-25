"""
Logging configuration module for the Astronomer project.
Handles log file creation and setup with both file and console output.
"""

import logging
import os
from datetime import datetime


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

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"
        )
    )

    # Stream handler (console output)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"
        )
    )

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

"""
Logging Configuration - Centralized Logging Setup

Enterprise-grade logging configuration for Runbooks.

Design Pattern:
- Console handler (stderr): WARNING default (clean business output), DEBUG with --verbose
- File handler: Always DEBUG to /tmp/runbooks-debug.log
- Suppresses boto3/botocore noise
- Integration with OutputController
- Business mode: Clean formatter without timestamps
"""

import logging
import sys
from pathlib import Path


def configure_logging(verbose: bool = False) -> None:
    """
    Configure Python logging based on verbose flag.

    Args:
        verbose: Enable DEBUG level console output with timestamps

    Behavior:
        - Console (stderr): WARNING (default, clean output) or DEBUG (--verbose)
        - File (/tmp/runbooks-debug.log): Always DEBUG
        - Suppresses boto3/botocore to WARNING level
        - Format:
            - Business mode: Clean message-only format
            - Verbose mode: timestamp - level - module - message

    Usage:
        from runbooks.common.logging_config import configure_logging
        configure_logging(verbose=True)
    """
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove existing handlers to prevent duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG if verbose else logging.WARNING)

    # Formatter: verbose mode shows timestamps, business mode is clean
    if verbose:
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # Business mode: Clean output, no timestamps
        console_formatter = logging.Formatter("%(message)s")

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (/tmp/runbooks-debug.log)
    log_file = Path("/tmp/runbooks-debug.log")
    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Suppress boto3/botocore noise
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Log configuration completion
    logger = logging.getLogger(__name__)
    logger.debug(
        f"Logging configured: verbose={verbose}, console_level={'DEBUG' if verbose else 'WARNING'}, file={log_file}"
    )

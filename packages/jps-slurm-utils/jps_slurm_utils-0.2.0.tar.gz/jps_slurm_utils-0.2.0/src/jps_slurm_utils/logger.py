"""Logging setup for jps-slurm-job-audit."""

import logging
from pathlib import Path
from typing import Optional


def setup_logger(
    logfile: Path, verbose: bool = False, quiet: bool = False
) -> logging.Logger:
    """
    Set up logging for the audit tool.

    Args:
        logfile: Path to log file
        verbose: Enable verbose/debug logging
        quiet: Suppress console output

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("jps_slurm_audit")

    # Set log level
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Clear existing handlers
    logger.handlers.clear()

    # File handler (always)
    file_handler = logging.FileHandler(logfile)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler (unless quiet)
    if not quiet:
        console_handler = logging.StreamHandler()
        if verbose:
            console_handler.setLevel(logging.DEBUG)
        else:
            console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    logger.propagate = False
    return logger

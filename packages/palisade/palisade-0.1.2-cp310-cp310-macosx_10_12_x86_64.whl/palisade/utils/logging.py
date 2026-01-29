"""Logging configuration for the scanner."""

import logging


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging for the scanner.

    Args:
    ----
        verbose: Whether to enable debug logging

    Returns:
    -------
        Configured logger instance
    """
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)

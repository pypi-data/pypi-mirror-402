"""
Rhizo logging configuration.

Provides structured logging with environment-based configuration.
Default level is WARNING (quiet), configurable via RHIZO_LOG_LEVEL.

Usage:
    from rhizo.logging import get_logger
    logger = get_logger(__name__)
    logger.debug("Debug message")
    logger.warning("Warning message")

Environment Variables:
    RHIZO_LOG_LEVEL: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                     Default: WARNING
"""

import logging
import os

# Configure the rhizo logger hierarchy
_log_level_str = os.environ.get("RHIZO_LOG_LEVEL", "WARNING").upper()
_log_level = getattr(logging, _log_level_str, logging.WARNING)

# Create the root rhizo logger
_rhizo_logger = logging.getLogger("rhizo")
_rhizo_logger.setLevel(_log_level)

# Add a handler only if none exists (avoid duplicate handlers)
if not _rhizo_logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    _rhizo_logger.addHandler(_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a rhizo module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance with rhizo prefix

    Example:
        logger = get_logger(__name__)
        logger.debug("Loading table %s", table_name)
    """
    # Strip 'rhizo.' prefix if present to avoid duplication
    if name.startswith("rhizo."):
        name = name[6:]
    return logging.getLogger(f"rhizo.{name}")

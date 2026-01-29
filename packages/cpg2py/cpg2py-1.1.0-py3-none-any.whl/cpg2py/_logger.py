"""
Logging configuration for cpg2py package.
"""

import logging
import sys
from typing import Optional

_logger: Optional[logging.Logger] = None


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Returns a logger instance for the specified module.

    Args:
        name: Module name (defaults to 'cpg2py')

    Returns:
        Configured logger instance
    """
    global _logger

    if _logger is None:
        _logger = logging.getLogger("cpg2py")
        _logger.setLevel(logging.WARNING)

        if not _logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setLevel(logging.WARNING)

            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            _logger.addHandler(handler)

    if name:
        return _logger.getChild(name)
    return _logger


def set_log_level(level: int) -> None:
    """
    Sets the logging level for the cpg2py logger.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR)
    """
    logger = get_logger()
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)

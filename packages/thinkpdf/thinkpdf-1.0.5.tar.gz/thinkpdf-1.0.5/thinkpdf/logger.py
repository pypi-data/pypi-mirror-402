"""Logging configuration for thinkpdf."""

import logging
import os
import sys

logger = logging.getLogger("thinkpdf")

_level = os.environ.get("THINKPDF_LOG_LEVEL", "INFO").upper()
logger.setLevel(getattr(logging, _level, logging.INFO))

if not logger.handlers:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setLevel(logging.DEBUG)
    _formatter = logging.Formatter(
        "[%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)


def get_logger(name: str = "thinkpdf") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


__all__ = ["logger", "get_logger"]

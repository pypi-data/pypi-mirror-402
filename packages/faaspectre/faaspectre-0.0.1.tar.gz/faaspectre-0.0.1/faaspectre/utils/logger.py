"""Logger utility for Telemetric Reporter."""

import logging
import sys
import json
import os
from logging import Logger


class CloudLoggingFormatter(logging.Formatter):
    """Produces messages compatible with Google Cloud logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for Google Cloud logging."""
        s = super().format(record)
        return json.dumps(
            {
                "message": s,
                "severity": record.levelname,
                "timestamp": {"seconds": int(record.created), "nanos": 0},
            }
        )


def get_logger(name: str = None) -> Logger:
    """Get a logger instance with Google Cloud logging format.

    Args:
        name: Name of logger, displayed on its log. If None, look up APP_NAME env variable.

    Returns:
        Logger: Python standard logger
    """
    logger_name = name
    if name is None:
        logger_name = os.environ.get("APP_NAME", None)
    logger = logging.getLogger(logger_name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler(sys.stdout)
        formatter = CloudLoggingFormatter(fmt="[%(name)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    return logger

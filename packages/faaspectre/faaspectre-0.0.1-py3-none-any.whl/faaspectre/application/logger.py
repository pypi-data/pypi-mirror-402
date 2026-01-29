"""Telemetric logger with correlation context management."""

from contextlib import contextmanager
from typing import Optional
from logging import Logger

from ..utils.logger import get_logger
from ..utils.singleton import Singleton


class TelemetricLogger(metaclass=Singleton):
    """Singleton logger for telemetric library with context management.

    Provides correlated logging for FaaS environments.
    """

    def __init__(self):
        """Initialize TelemetricLogger."""
        self._logger: Optional[Logger] = None

    @property
    def logger(self) -> Logger:
        """Get logger instance (lazy initialization)."""
        if self._logger is None:
            self._logger = get_logger("faaspectre.telemetric")
        return self._logger

    @contextmanager
    def execution_context(self, correlation_id: str, job_id: str):
        """Context manager for execution logging with correlation.

        Args:
            correlation_id: Correlation ID for distributed tracing
            job_id: Job ID for execution tracking

        Yields:
            Logger instance with correlation context
        """
        self.info(
            "Execution started",
            correlation_id=correlation_id,
            job_id=job_id,
        )
        try:
            yield self.logger
        except Exception as e:
            self.error(
                f"Execution failed: {e}",
                correlation_id=correlation_id,
                job_id=job_id,
            )
            raise
        finally:
            self.info(
                "Execution completed",
                correlation_id=correlation_id,
                job_id=job_id,
            )

    def debug(self, message: str, **kwargs):
        """Log debug message with optional correlation context.

        Args:
            message: Log message
            **kwargs: Additional context (correlation_id, job_id, etc.)
        """
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """Log info message with optional correlation context.

        Args:
            message: Log message
            **kwargs: Additional context (correlation_id, job_id, etc.)
        """
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with optional correlation context.

        Args:
            message: Log message
            **kwargs: Additional context (correlation_id, job_id, etc.)
        """
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """Log error message with optional correlation context.

        Args:
            message: Log message
            **kwargs: Additional context (correlation_id, job_id, etc.)
        """
        self.logger.error(message, extra=kwargs, exc_info=True)


# Singleton instance
telemetric_logger = TelemetricLogger()

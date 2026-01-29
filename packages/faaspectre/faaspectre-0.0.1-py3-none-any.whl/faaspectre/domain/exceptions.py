"""Exception hierarchy for Telemetric Reporter."""


class TelemetricError(Exception):
    """Base exception for all telemetric errors with correlation context."""

    def __init__(self, message: str, correlation_id: str = None, job_id: str = None):
        """Initialize TelemetricError.

        Args:
            message: Error message
            correlation_id: Optional correlation ID for tracing
            job_id: Optional job ID for tracing
        """
        self.correlation_id = correlation_id
        self.job_id = job_id
        super().__init__(message)


class ConfigurationError(TelemetricError):
    """Configuration is invalid or missing."""

    pass


class ValidationError(TelemetricError):
    """Domain model validation failed."""

    pass


class StorageError(TelemetricError):
    """General storage operation failure."""

    pass


class AtomicWriteError(StorageError):
    """Atomic batch write operation failed."""

    pass


class InstrumentationError(TelemetricError):
    """Instrumentation (memory/timing) operation failed."""

    pass

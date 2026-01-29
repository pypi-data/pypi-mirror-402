"""
Telemetric Reporter - FaaS Job Execution Metrics Library

This module implements the JobExecutionReporter wrapper/library that enforces:
- Auto-instrumentation (timing, memory)
- Exception handling
- Atomic persistence (batch writes to pipeline_logs and pipeline_data)
- Data sanitization (dates to ISO 8601, metrics to floats)

Usage:
    >>> from faaspectre import create_job_execution_reporter, ExecutionContext
    >>> 
    >>> context = ExecutionContext.from_workflow_payload(workflow_payload)
    >>> with create_job_execution_reporter(context, "ANALYZE_SENTIMENT") as reporter:
    >>>     result = my_worker_function(**kwargs)
    >>>     reporter.save_execution_payload(result)
"""

from typing import Optional

# Domain models
from .domain.models import ExecutionContext, ExecutionMetrics, ExecutionPayload
from .domain.status import PipelineStatus
from .domain.exceptions import (
    TelemetricError,
    ConfigurationError,
    ValidationError,
    StorageError,
    AtomicWriteError,
    InstrumentationError,
)

# Application ports
from .application.ports.metric_storage import MetricStorage
from .application.ports.instrumentation import InstrumentationPort
from .application.ports.serializer import MetricSerializer

# Application config
from .application.config import TelemetricConfig

# Application use case
from .application.use_case.job_execution_reporter import JobExecutionReporter

# Utils
from .utils.memory_tracker import track_memory

# Infrastructure adapters
from .infrastructure.adapters.storage.firestore_metric_storage import FirestoreMetricStorage
from .infrastructure.adapters.instrumentation.psutil_instrumentation import PsutilInstrumentation
from .infrastructure.adapters.serializer.firestore_serializer import FirestoreMetricSerializer

__all__ = [
    # Domain models
    "ExecutionContext",
    "ExecutionMetrics",
    "ExecutionPayload",
    "PipelineStatus",
    # Exceptions
    "TelemetricError",
    "ConfigurationError",
    "ValidationError",
    "StorageError",
    "AtomicWriteError",
    "InstrumentationError",
    # Ports
    "MetricStorage",
    "InstrumentationPort",
    "MetricSerializer",
    # Config
    "TelemetricConfig",
    # Use case
    "JobExecutionReporter",
    # Adapters
    "FirestoreMetricStorage",
    "PsutilInstrumentation",
    "FirestoreMetricSerializer",
    # Utils
    "track_memory",
    # Factory
    "create_job_execution_reporter",
]


def _create_storage_adapter(config: TelemetricConfig) -> MetricStorage:
    """Create storage adapter based on config.

    Args:
        config: TelemetricConfig with storage backend selection

    Returns:
        MetricStorage adapter instance

    Raises:
        ConfigurationError: If storage_backend is invalid or not implemented
    """
    if config.storage_backend == "firestore":
        serializer = FirestoreMetricSerializer()
        return FirestoreMetricStorage(config, serializer=serializer)
    elif config.storage_backend == "bigquery":
        # Future: BigQueryMetricStorage
        raise ConfigurationError("BigQuery storage not yet implemented")
    elif config.storage_backend == "postgres":
        # Future: PostgresMetricStorage
        raise ConfigurationError("PostgreSQL storage not yet implemented")
    else:
        raise ConfigurationError(f"Unknown storage backend: {config.storage_backend}")


def create_job_execution_reporter(
    context: ExecutionContext,
    step_name: str,
    config: Optional[TelemetricConfig] = None,
    storage: Optional[MetricStorage] = None,
    instrumentation: Optional[InstrumentationPort] = None,
) -> JobExecutionReporter:
    """Factory function to create JobExecutionReporter with sensible defaults.

    This is the composition root - it can import from all layers to wire dependencies.

    Args:
        context: ExecutionContext from workflow
        step_name: Human-readable step name (e.g., "ANALYZE_SENTIMENT")
        config: Optional TelemetricConfig (defaults to from_env())
        storage: Optional MetricStorage (defaults to config-based adapter)
        instrumentation: Optional InstrumentationPort (defaults to PsutilInstrumentation)

    Returns:
        JobExecutionReporter instance ready to use

    Raises:
        ConfigurationError: If configuration is invalid
        TelemetricError: If initialization fails
    """
    try:
        config = config or TelemetricConfig.from_env()
        config.validate()  # Raises ConfigurationError if invalid
    except ConfigurationError as e:
        # Add context if available
        if hasattr(context, "correlation_id"):
            e.correlation_id = context.correlation_id
            e.job_id = context.job_id
        raise

    try:
        if storage is None:
            storage = _create_storage_adapter(config)
        if instrumentation is None:
            instrumentation = PsutilInstrumentation()
        return JobExecutionReporter(context, step_name, storage, instrumentation)
    except Exception as e:
        # Wrap in TelemetricError with context
        raise TelemetricError(
            f"Failed to initialize JobExecutionReporter: {e}",
            correlation_id=context.correlation_id if hasattr(context, "correlation_id") else None,
            job_id=context.job_id if hasattr(context, "job_id") else None,
        ) from e

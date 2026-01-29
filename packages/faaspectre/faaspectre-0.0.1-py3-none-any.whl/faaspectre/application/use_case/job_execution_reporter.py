"""JobExecutionReporter use case - orchestrates execution flow."""

from typing import Optional, Dict, Any
from datetime import datetime, timezone

from ...domain.models import ExecutionContext, ExecutionMetrics, ExecutionPayload
from ...domain.status import PipelineStatus
from ...domain.exceptions import (
    TelemetricError,
    ValidationError,
    StorageError,
    AtomicWriteError,
    InstrumentationError,
)
from ...application.ports.metric_storage import MetricStorage
from ...application.ports.instrumentation import InstrumentationPort
from ...application.logger import telemetric_logger
from ...utils.datetime_utils import to_iso8601_utc
from ...utils.error_formatter import format_error_summary


class JobExecutionReporter:
    """JobExecutionReporter - orchestrates execution flow with auto-instrumentation.

    Context manager that provides:
    - Auto-instrumentation (timing, memory)
    - Exception handling
    - Atomic persistence (batch writes to pipeline_logs and pipeline_data)
    - Data sanitization (dates to ISO 8601, metrics to floats)
    """

    def __init__(
        self,
        context: ExecutionContext,
        step_name: str,
        storage: MetricStorage,
        instrumentation: InstrumentationPort,
    ):
        """Initialize JobExecutionReporter.

        Args:
            context: ExecutionContext from workflow
            step_name: Human-readable step name (e.g., "ANALYZE_SENTIMENT")
            storage: MetricStorage port (dependency injection)
            instrumentation: InstrumentationPort port (dependency injection)

        Raises:
            TelemetricError: If initialization fails
        """
        self.context = context
        self.step_name = step_name
        self.storage = storage
        self.instrumentation = instrumentation
        self.doc_id = context.job_id
        self._timing_tracker = instrumentation.create_timing_tracker()
        self._execution_payload: Optional[Dict[str, Any]] = None
        self._initial_memory_mb: Optional[float] = None

    def __enter__(self) -> "JobExecutionReporter":
        """Context manager entry - capture start metrics.

        Returns:
            JobExecutionReporter instance

        Raises:
            InstrumentationError: If instrumentation fails (logged as warning, continues)
        """
        # Use logger context manager with correlation_id/job_id
        with telemetric_logger.execution_context(
            self.context.correlation_id, self.context.job_id
        ):
            # Try to capture start_time_epoch
            try:
                self._timing_tracker.start()
            except Exception as e:
                telemetric_logger.warning(
                    f"Instrumentation error (start timing): {e}",
                    correlation_id=self.context.correlation_id,
                    job_id=self.context.job_id,
                )
                # Continue without timing

            # Try to capture initial_memory_mb
            try:
                self._initial_memory_mb = self.instrumentation.get_current_memory_mb()
            except InstrumentationError as e:
                telemetric_logger.warning(
                    f"Instrumentation error (initial memory): {e}",
                    correlation_id=self.context.correlation_id,
                    job_id=self.context.job_id,
                )
                # Continue without memory tracking

            telemetric_logger.info(
                f"Execution started for step: {self.step_name}",
                correlation_id=self.context.correlation_id,
                job_id=self.context.job_id,
            )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit - handle completion/errors and persist.

        Args:
            exc_type: Exception type (None if no exception)
            exc_val: Exception value
            exc_tb: Exception traceback

        Returns:
            False (don't suppress exceptions - let orchestrator handle)
        """
        with telemetric_logger.execution_context(
            self.context.correlation_id, self.context.job_id
        ):
            # Determine status and error_summary
            status = PipelineStatus.SUCCESS.value
            error_summary: Optional[str] = None

            if exc_type is not None:
                # Business logic error occurred
                status = PipelineStatus.FAILED.value
                error_summary = format_error_summary(exc_val)
                telemetric_logger.error(
                    f"Execution failed: {error_summary}",
                    correlation_id=self.context.correlation_id,
                    job_id=self.context.job_id,
                )

            # Try to capture end_time_epoch
            end_time_epoch: Optional[float] = None
            try:
                end_time_epoch = self._timing_tracker.stop()
            except Exception as e:
                telemetric_logger.warning(
                    f"Instrumentation error (end timing): {e}",
                    correlation_id=self.context.correlation_id,
                    job_id=self.context.job_id,
                )

            # Try to capture peak_memory_mb
            peak_memory_mb: Optional[float] = None
            try:
                peak_memory_mb = self.instrumentation.get_peak_memory_mb()
            except InstrumentationError as e:
                telemetric_logger.warning(
                    f"Instrumentation error (peak memory): {e}",
                    correlation_id=self.context.correlation_id,
                    job_id=self.context.job_id,
                )

            # Calculate duration_ms
            duration_ms: Optional[float] = None
            try:
                if self._timing_tracker.start_time is not None and end_time_epoch is not None:
                    duration_ms = self._timing_tracker.duration_ms()
            except Exception:
                # Duration calculation failed, leave as None
                pass

            # Get start_time_epoch from tracker
            start_time_epoch: Optional[float] = self._timing_tracker.start_time

            # Create ExecutionMetrics object
            try:
                metrics = ExecutionMetrics(
                    doc_id=self.doc_id,
                    correlation_id=self.context.correlation_id,
                    job_id=self.context.job_id,
                    prev_job_id=self.context.prev_job_id,
                    step_name=self.step_name,
                    triggered_by=self.context.triggered_by,
                    created_at=to_iso8601_utc(datetime.now(timezone.utc)),
                    start_time_epoch=start_time_epoch if start_time_epoch else 0.0,
                    end_time_epoch=end_time_epoch,
                    duration_ms=duration_ms,
                    memory_mb=peak_memory_mb,
                    status=status,
                    error_summary=error_summary,
                )
            except ValidationError as e:
                telemetric_logger.error(
                    f"Validation error creating ExecutionMetrics: {e}",
                    correlation_id=self.context.correlation_id,
                    job_id=self.context.job_id,
                )
                # Re-raise validation errors (programming error, fix code)
                raise

            # Create ExecutionPayload if data was saved
            payload: Optional[ExecutionPayload] = None
            if self._execution_payload is not None:
                try:
                    payload = ExecutionPayload(
                        doc_id=self.doc_id,
                        correlation_id=self.context.correlation_id,
                        step_name=self.step_name,
                        created_at=to_iso8601_utc(datetime.now(timezone.utc)),
                        payload=self._execution_payload,
                    )
                except ValidationError as e:
                    telemetric_logger.error(
                        f"Validation error creating ExecutionPayload: {e}",
                        correlation_id=self.context.correlation_id,
                        job_id=self.context.job_id,
                    )
                    # Re-raise validation errors
                    raise

            # Atomic persistence
            try:
                self.storage.save_atomic(metrics, payload)
                telemetric_logger.info(
                    "Execution metrics saved successfully",
                    correlation_id=self.context.correlation_id,
                    job_id=self.context.job_id,
                )
            except StorageError as e:
                telemetric_logger.error(
                    f"Storage error: {e}",
                    correlation_id=self.context.correlation_id,
                    job_id=self.context.job_id,
                )
                # Re-raise for orchestrator retry
                raise
            except AtomicWriteError as e:
                telemetric_logger.error(
                    f"Atomic write error: {e}",
                    correlation_id=self.context.correlation_id,
                    job_id=self.context.job_id,
                )
                # Re-raise for orchestrator retry
                raise

        # Return False to not suppress exceptions
        return False

    def save_execution_payload(self, data: Dict[str, Any]) -> None:
        """Store execution payload for atomic write in __exit__.

        Args:
            data: Flexible payload dictionary (no strict schema)

        Raises:
            ValidationError: If data structure is invalid
        """
        if not isinstance(data, dict):
            raise ValidationError(
                f"Execution payload must be a dictionary, got {type(data).__name__}",
                correlation_id=self.context.correlation_id,
                job_id=self.context.job_id,
            )
        self._execution_payload = data

    def sample_memory(self) -> float:
        """Sample current memory and update peak tracking.

        Can be called during execution to ensure peak memory is captured.
        This method calls get_peak_memory_mb() which automatically updates
        the peak if current memory is higher.

        Returns:
            Current memory usage in MB

        Example:
            >>> with create_job_execution_reporter(context, "PROCESS_DATA") as reporter:
            >>>     data = load_large_dataset()
            >>>     reporter.sample_memory()  # Capture peak after loading
            >>>     result = process_data(data)
        """
        try:
            # get_peak_memory_mb() will update peak if current is higher
            peak = self.instrumentation.get_peak_memory_mb()
            return peak
        except InstrumentationError as e:
            telemetric_logger.warning(
                f"Instrumentation error (memory sampling): {e}",
                correlation_id=self.context.correlation_id,
                job_id=self.context.job_id,
            )
            return 0.0

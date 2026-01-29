"""Tests for JobExecutionReporter use case."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

from faaspectre.application.use_case.job_execution_reporter import JobExecutionReporter
from faaspectre.domain.models import ExecutionContext, ExecutionMetrics, ExecutionPayload
from faaspectre.domain.status import PipelineStatus
from faaspectre.domain.exceptions import (
    ValidationError,
    StorageError,
    AtomicWriteError,
    InstrumentationError,
)
from faaspectre.application.ports.metric_storage import MetricStorage
from faaspectre.application.ports.instrumentation import InstrumentationPort, TimingTracker


# Stub implementations for ports
class StubMetricStorage(MetricStorage):
    """Stub implementation of MetricStorage for testing."""

    def __init__(self):
        self.saved_metrics = None
        self.saved_payload = None
        self.save_atomic_called = False

    def save_execution_metrics(self, metrics: ExecutionMetrics) -> None:
        """Stub implementation."""
        self.saved_metrics = metrics

    def save_execution_payload(self, payload: ExecutionPayload) -> None:
        """Stub implementation."""
        self.saved_payload = payload

    def save_atomic(self, metrics: ExecutionMetrics, payload=None) -> None:
        """Stub implementation."""
        self.save_atomic_called = True
        self.saved_metrics = metrics
        self.saved_payload = payload


class StubInstrumentationPort(InstrumentationPort):
    """Stub implementation of InstrumentationPort for testing."""

    def __init__(self):
        self.current_memory_mb = 100.0
        self.peak_memory_mb = 150.0
        self.timing_tracker = TimingTracker()
        self.get_current_memory_called = False
        self.get_peak_memory_called = False

    def get_current_memory_mb(self) -> float:
        """Stub implementation."""
        self.get_current_memory_called = True
        return self.current_memory_mb

    def get_peak_memory_mb(self) -> float:
        """Stub implementation that updates peak if current is higher."""
        self.get_peak_memory_called = True
        # Update peak if current is higher (mimics real behavior)
        if self.peak_memory_mb is None:
            self.peak_memory_mb = self.get_current_memory_mb()
        else:
            current = self.get_current_memory_mb()
            if current > self.peak_memory_mb:
                self.peak_memory_mb = current
        return self.peak_memory_mb

    def create_timing_tracker(self) -> TimingTracker:
        """Stub implementation."""
        return self.timing_tracker


# Fixtures
@pytest.fixture
def mock_storage():
    """Create a mock MetricStorage."""
    return StubMetricStorage()


@pytest.fixture
def mock_instrumentation():
    """Create a mock InstrumentationPort."""
    return StubInstrumentationPort()


@pytest.fixture
def valid_context(valid_correlation_id, valid_job_id):
    """Create a valid ExecutionContext for testing."""
    return ExecutionContext(
        correlation_id=valid_correlation_id,
        job_id=valid_job_id,
        step_name="TEST_STEP",
        triggered_by="ETL_WORKFLOW",
        prev_job_id=None,
    )


class TestJobExecutionReporterInit:
    """Tests for JobExecutionReporter.__init__()."""

    def test_init_success(self, valid_context, mock_storage, mock_instrumentation):
        """TR-001: Verify successful initialization with valid dependencies."""
        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="ANALYZE_SENTIMENT",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        assert reporter.context == valid_context
        assert reporter.step_name == "ANALYZE_SENTIMENT"
        assert reporter.storage == mock_storage
        assert reporter.instrumentation == mock_instrumentation
        assert reporter.doc_id == valid_context.job_id
        assert reporter._execution_payload is None
        assert reporter._initial_memory_mb is None

    def test_init_timing_tracker_created(self, valid_context, mock_storage, mock_instrumentation):
        """Verify create_timing_tracker() called on instrumentation."""
        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        assert reporter._timing_tracker == mock_instrumentation.timing_tracker

    def test_init_state_initialized(self, valid_context, mock_storage, mock_instrumentation):
        """Verify _execution_payload and _initial_memory_mb initialized to None."""
        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        assert reporter._execution_payload is None
        assert reporter._initial_memory_mb is None


class TestJobExecutionReporterEnter:
    """Tests for JobExecutionReporter.__enter__()."""

    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_enter_success(self, mock_logger, valid_context, mock_storage, mock_instrumentation):
        """TR-002: Successful entry with timing and memory tracking."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        result = reporter.__enter__()

        assert result == reporter
        assert reporter._timing_tracker.start_time is not None
        assert reporter._initial_memory_mb == mock_instrumentation.current_memory_mb
        mock_logger.execution_context.assert_called_once()
        mock_logger.info.assert_called_once()

    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_enter_timing_tracker_started(self, mock_logger, valid_context, mock_storage, mock_instrumentation):
        """Verify timing_tracker.start() called."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        assert reporter._timing_tracker.start_time is None
        reporter.__enter__()
        assert reporter._timing_tracker.start_time is not None

    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_enter_initial_memory_captured(self, mock_logger, valid_context, mock_storage, mock_instrumentation):
        """Verify get_current_memory_mb() called."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        reporter.__enter__()

        assert mock_instrumentation.get_current_memory_called
        assert reporter._initial_memory_mb == mock_instrumentation.current_memory_mb

    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_enter_logger_context_used(self, mock_logger, valid_context, mock_storage, mock_instrumentation):
        """Verify telemetric_logger.execution_context() context manager used."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        reporter.__enter__()

        mock_logger.execution_context.assert_called_once_with(
            valid_context.correlation_id,
            valid_context.job_id,
        )

    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_enter_timing_error_handled(self, mock_logger, valid_context, mock_storage, mock_instrumentation):
        """Verify timing errors are logged as warnings but don't fail."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)

        # Make timing_tracker.start() raise an exception
        mock_instrumentation.timing_tracker.start = Mock(side_effect=Exception("Timing error"))

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        # Should not raise exception
        reporter.__enter__()

        mock_logger.warning.assert_called()
        assert any("start timing" in str(call) for call in mock_logger.warning.call_args_list)

    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_enter_memory_error_handled(self, mock_logger, valid_context, mock_storage, mock_instrumentation):
        """Verify InstrumentationError on memory tracking is logged as warning."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)

        # Make get_current_memory_mb() raise InstrumentationError
        mock_instrumentation.get_current_memory_mb = Mock(side_effect=InstrumentationError("Memory error"))

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        # Should not raise exception
        reporter.__enter__()

        mock_logger.warning.assert_called()
        assert any("initial memory" in str(call) for call in mock_logger.warning.call_args_list)

    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_enter_returns_self(self, mock_logger, valid_context, mock_storage, mock_instrumentation):
        """Verify __enter__ returns self."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        result = reporter.__enter__()
        assert result == reporter


class TestJobExecutionReporterExit:
    """Tests for JobExecutionReporter.__exit__()."""

    @patch("faaspectre.application.use_case.job_execution_reporter.to_iso8601_utc")
    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_exit_success_no_exception(
        self, mock_logger, mock_to_iso8601, valid_context, mock_storage, mock_instrumentation
    ):
        """TR-003: Successful exit with no business logic error."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)
        mock_to_iso8601.return_value = "2026-01-16T10:00:00.000Z"

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        # Start timing tracker
        reporter._timing_tracker.start()
        reporter._timing_tracker.stop()

        # Exit with no exception
        result = reporter.__exit__(None, None, None)

        assert result is False  # Don't suppress exceptions
        assert mock_storage.save_atomic_called
        assert mock_storage.saved_metrics is not None
        assert mock_storage.saved_metrics.status == PipelineStatus.SUCCESS.value
        assert mock_storage.saved_metrics.error_summary is None

    @patch("faaspectre.application.use_case.job_execution_reporter.to_iso8601_utc")
    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_exit_success_metrics_created(
        self, mock_logger, mock_to_iso8601, valid_context, mock_storage, mock_instrumentation
    ):
        """Verify ExecutionMetrics created with correct status='SUCCESS'."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)
        mock_to_iso8601.return_value = "2026-01-16T10:00:00.000Z"

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="ANALYZE_SENTIMENT",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        reporter._timing_tracker.start()
        reporter._timing_tracker.stop()
        reporter.__exit__(None, None, None)

        metrics = mock_storage.saved_metrics
        assert metrics.status == PipelineStatus.SUCCESS.value
        assert metrics.step_name == "ANALYZE_SENTIMENT"
        assert metrics.correlation_id == valid_context.correlation_id
        assert metrics.job_id == valid_context.job_id

    @patch("faaspectre.application.use_case.job_execution_reporter.to_iso8601_utc")
    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_exit_success_end_time_captured(
        self, mock_logger, mock_to_iso8601, valid_context, mock_storage, mock_instrumentation
    ):
        """Verify timing_tracker.stop() called and end_time captured."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)
        mock_to_iso8601.return_value = "2026-01-16T10:00:00.000Z"

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        reporter._timing_tracker.start()
        reporter.__exit__(None, None, None)

        # __exit__ calls stop() internally, so end_time_epoch should be set
        assert mock_storage.saved_metrics.end_time_epoch is not None
        assert isinstance(mock_storage.saved_metrics.end_time_epoch, float)

    @patch("faaspectre.application.use_case.job_execution_reporter.to_iso8601_utc")
    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_exit_success_peak_memory_captured(
        self, mock_logger, mock_to_iso8601, valid_context, mock_storage, mock_instrumentation
    ):
        """Verify get_peak_memory_mb() called."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)
        mock_to_iso8601.return_value = "2026-01-16T10:00:00.000Z"

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        reporter._timing_tracker.start()
        reporter._timing_tracker.stop()
        reporter.__exit__(None, None, None)

        assert mock_instrumentation.get_peak_memory_called
        assert mock_storage.saved_metrics.memory_mb == mock_instrumentation.peak_memory_mb

    @patch("faaspectre.application.use_case.job_execution_reporter.to_iso8601_utc")
    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_exit_success_duration_calculated(
        self, mock_logger, mock_to_iso8601, valid_context, mock_storage, mock_instrumentation
    ):
        """Verify duration_ms calculated from timing tracker."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)
        mock_to_iso8601.return_value = "2026-01-16T10:00:00.000Z"

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        reporter._timing_tracker.start()
        reporter.__exit__(None, None, None)

        # __exit__ calculates duration internally, so duration_ms should be set
        assert mock_storage.saved_metrics.duration_ms is not None
        assert isinstance(mock_storage.saved_metrics.duration_ms, float)
        assert mock_storage.saved_metrics.duration_ms >= 0

    @patch("faaspectre.application.use_case.job_execution_reporter.to_iso8601_utc")
    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_exit_success_no_payload(
        self, mock_logger, mock_to_iso8601, valid_context, mock_storage, mock_instrumentation
    ):
        """Verify no payload created when save_execution_payload() not called."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)
        mock_to_iso8601.return_value = "2026-01-16T10:00:00.000Z"

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        reporter._timing_tracker.start()
        reporter._timing_tracker.stop()
        reporter.__exit__(None, None, None)

        assert mock_storage.saved_payload is None

    @patch("faaspectre.application.use_case.job_execution_reporter.to_iso8601_utc")
    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_exit_success_with_payload(
        self, mock_logger, mock_to_iso8601, valid_context, mock_storage, mock_instrumentation
    ):
        """Verify ExecutionPayload created when _execution_payload set."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)
        mock_to_iso8601.return_value = "2026-01-16T10:00:00.000Z"

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        payload_data = {"result": "success", "count": 100}
        reporter.save_execution_payload(payload_data)

        reporter._timing_tracker.start()
        reporter._timing_tracker.stop()
        reporter.__exit__(None, None, None)

        assert mock_storage.saved_payload is not None
        assert mock_storage.saved_payload.payload == payload_data
        assert mock_storage.saved_payload.correlation_id == valid_context.correlation_id

    @patch("faaspectre.application.use_case.job_execution_reporter.to_iso8601_utc")
    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_exit_success_atomic_save(
        self, mock_logger, mock_to_iso8601, valid_context, mock_storage, mock_instrumentation
    ):
        """Verify storage.save_atomic(metrics, payload) called."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)
        mock_to_iso8601.return_value = "2026-01-16T10:00:00.000Z"

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        reporter._timing_tracker.start()
        reporter._timing_tracker.stop()
        reporter.__exit__(None, None, None)

        assert mock_storage.save_atomic_called
        assert mock_storage.saved_metrics is not None

    @patch("faaspectre.application.use_case.job_execution_reporter.to_iso8601_utc")
    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_exit_returns_false(
        self, mock_logger, mock_to_iso8601, valid_context, mock_storage, mock_instrumentation
    ):
        """Verify returns False (don't suppress exceptions)."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)
        mock_to_iso8601.return_value = "2026-01-16T10:00:00.000Z"

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        reporter._timing_tracker.start()
        reporter._timing_tracker.stop()
        result = reporter.__exit__(None, None, None)

        assert result is False

    @patch("faaspectre.application.use_case.job_execution_reporter.format_error_summary")
    @patch("faaspectre.application.use_case.job_execution_reporter.to_iso8601_utc")
    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_exit_with_business_exception(
        self, mock_logger, mock_to_iso8601, mock_format_error, valid_context, mock_storage, mock_instrumentation
    ):
        """TR-004: Exit when business logic raises exception."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)
        mock_to_iso8601.return_value = "2026-01-16T10:00:00.000Z"
        mock_format_error.return_value = "ValueError: Test error"

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        reporter._timing_tracker.start()
        reporter._timing_tracker.stop()

        test_exception = ValueError("Test error")
        result = reporter.__exit__(ValueError, test_exception, None)

        assert result is False  # Re-raise exception
        assert mock_storage.saved_metrics.status == PipelineStatus.FAILED.value
        assert mock_storage.saved_metrics.error_summary == "ValueError: Test error"
        mock_format_error.assert_called_once_with(test_exception)
        mock_logger.error.assert_called()

    @patch("faaspectre.application.use_case.job_execution_reporter.format_error_summary")
    @patch("faaspectre.application.use_case.job_execution_reporter.to_iso8601_utc")
    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_exit_error_status_failed(
        self, mock_logger, mock_to_iso8601, mock_format_error, valid_context, mock_storage, mock_instrumentation
    ):
        """Verify status='FAILED' when exception occurs."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)
        mock_to_iso8601.return_value = "2026-01-16T10:00:00.000Z"
        mock_format_error.return_value = "Error summary"

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        reporter._timing_tracker.start()
        reporter._timing_tracker.stop()
        reporter.__exit__(ValueError, ValueError("Error"), None)

        assert mock_storage.saved_metrics.status == PipelineStatus.FAILED.value

    @patch("faaspectre.application.use_case.job_execution_reporter.format_error_summary")
    @patch("faaspectre.application.use_case.job_execution_reporter.to_iso8601_utc")
    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_exit_error_summary_formatted(
        self, mock_logger, mock_to_iso8601, mock_format_error, valid_context, mock_storage, mock_instrumentation
    ):
        """Verify format_error_summary() called with exception."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)
        mock_to_iso8601.return_value = "2026-01-16T10:00:00.000Z"
        mock_format_error.return_value = "Formatted error"

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        reporter._timing_tracker.start()
        reporter._timing_tracker.stop()

        test_exception = RuntimeError("Test")
        reporter.__exit__(RuntimeError, test_exception, None)

        mock_format_error.assert_called_once_with(test_exception)

    @patch("faaspectre.application.use_case.job_execution_reporter.format_error_summary")
    @patch("faaspectre.application.use_case.job_execution_reporter.to_iso8601_utc")
    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_exit_error_re_raised(
        self, mock_logger, mock_to_iso8601, mock_format_error, valid_context, mock_storage, mock_instrumentation
    ):
        """Verify exception is re-raised (not suppressed)."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)
        mock_to_iso8601.return_value = "2026-01-16T10:00:00.000Z"
        mock_format_error.return_value = "Error"

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        reporter._timing_tracker.start()
        reporter._timing_tracker.stop()

        # __exit__ should return False (don't suppress)
        result = reporter.__exit__(ValueError, ValueError("Error"), None)
        assert result is False

    @patch("faaspectre.application.use_case.job_execution_reporter.to_iso8601_utc")
    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_exit_timing_error_handled(
        self, mock_logger, mock_to_iso8601, valid_context, mock_storage, mock_instrumentation
    ):
        """Verify timing stop errors are logged as warnings."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)
        mock_to_iso8601.return_value = "2026-01-16T10:00:00.000Z"

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        reporter._timing_tracker.start()
        # Make stop() raise an exception
        reporter._timing_tracker.stop = Mock(side_effect=Exception("Stop error"))

        reporter.__exit__(None, None, None)

        mock_logger.warning.assert_called()
        assert any("end timing" in str(call) for call in mock_logger.warning.call_args_list)

    @patch("faaspectre.application.use_case.job_execution_reporter.to_iso8601_utc")
    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_exit_memory_error_handled(
        self, mock_logger, mock_to_iso8601, valid_context, mock_storage, mock_instrumentation
    ):
        """Verify peak memory errors are logged as warnings."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)
        mock_to_iso8601.return_value = "2026-01-16T10:00:00.000Z"

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        reporter._timing_tracker.start()
        reporter._timing_tracker.stop()

        # Make get_peak_memory_mb() raise InstrumentationError
        mock_instrumentation.get_peak_memory_mb = Mock(side_effect=InstrumentationError("Peak memory error"))

        reporter.__exit__(None, None, None)

        mock_logger.warning.assert_called()
        assert any("peak memory" in str(call) for call in mock_logger.warning.call_args_list)

    @patch("faaspectre.application.use_case.job_execution_reporter.to_iso8601_utc")
    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_exit_storage_error_re_raised(
        self, mock_logger, mock_to_iso8601, valid_context, mock_storage, mock_instrumentation
    ):
        """Verify StorageError from save_atomic() is re-raised."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)
        mock_to_iso8601.return_value = "2026-01-16T10:00:00.000Z"

        storage_error = StorageError("Storage failed", correlation_id="test", job_id="test")
        mock_storage.save_atomic = Mock(side_effect=storage_error)

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        reporter._timing_tracker.start()
        reporter._timing_tracker.stop()

        with pytest.raises(StorageError):
            reporter.__exit__(None, None, None)

    @patch("faaspectre.application.use_case.job_execution_reporter.to_iso8601_utc")
    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_exit_atomic_write_error_re_raised(
        self, mock_logger, mock_to_iso8601, valid_context, mock_storage, mock_instrumentation
    ):
        """Verify AtomicWriteError from save_atomic() is re-raised."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)
        mock_to_iso8601.return_value = "2026-01-16T10:00:00.000Z"

        atomic_error = AtomicWriteError("Atomic write failed", correlation_id="test", job_id="test")
        mock_storage.save_atomic = Mock(side_effect=atomic_error)

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        reporter._timing_tracker.start()
        reporter._timing_tracker.stop()

        with pytest.raises(AtomicWriteError):
            reporter.__exit__(None, None, None)


class TestJobExecutionReporterSavePayload:
    """Tests for JobExecutionReporter.save_execution_payload()."""

    def test_save_execution_payload_success(self, valid_context, mock_storage, mock_instrumentation):
        """TR-005: Successfully store payload dict."""
        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        payload_data = {"result": "success", "count": 100}
        reporter.save_execution_payload(payload_data)

        assert reporter._execution_payload == payload_data

    def test_save_execution_payload_invalid_type(self, valid_context, mock_storage, mock_instrumentation):
        """Verify ValidationError raised for non-dict input."""
        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        with pytest.raises(ValidationError, match="must be a dictionary"):
            reporter.save_execution_payload("not a dict")

        with pytest.raises(ValidationError, match="must be a dictionary"):
            reporter.save_execution_payload(123)

        with pytest.raises(ValidationError, match="must be a dictionary"):
            reporter.save_execution_payload(None)

    def test_save_execution_payload_overwrites_previous(self, valid_context, mock_storage, mock_instrumentation):
        """Verify multiple calls overwrite previous payload."""
        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        payload1 = {"result": "first"}
        payload2 = {"result": "second"}

        reporter.save_execution_payload(payload1)
        assert reporter._execution_payload == payload1

        reporter.save_execution_payload(payload2)
        assert reporter._execution_payload == payload2


class TestJobExecutionReporterSampleMemory:
    """Tests for JobExecutionReporter.sample_memory()."""

    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_sample_memory_success(self, mock_logger, valid_context, mock_storage, mock_instrumentation):
        """TR-006: Successfully sample memory and update peak."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        # Set initial peak memory
        mock_instrumentation.peak_memory_mb = 100.0
        mock_instrumentation.current_memory_mb = 150.0  # Higher than peak

        # Sample memory - should update peak
        peak = reporter.sample_memory()

        assert peak == 150.0  # Returns updated peak
        assert mock_instrumentation.get_peak_memory_called
        assert mock_instrumentation.peak_memory_mb == 150.0  # Peak was updated

    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_sample_memory_updates_peak(self, mock_logger, valid_context, mock_storage, mock_instrumentation):
        """Verify sample_memory() updates peak when current is higher."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        # Initial peak is 100 MB
        mock_instrumentation.peak_memory_mb = 100.0
        mock_instrumentation.current_memory_mb = 200.0  # Much higher

        reporter.sample_memory()

        # get_peak_memory_mb() should have been called, which updates peak
        assert mock_instrumentation.get_peak_memory_called
        # The peak should be updated to 200.0 (handled by instrumentation)

    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_sample_memory_handles_error(self, mock_logger, valid_context, mock_storage, mock_instrumentation):
        """Verify sample_memory() handles InstrumentationError gracefully."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        # Make get_peak_memory_mb() raise InstrumentationError
        mock_instrumentation.get_peak_memory_mb = Mock(side_effect=InstrumentationError("Memory error"))

        # Should not raise exception, but return 0.0 and log warning
        result = reporter.sample_memory()

        assert result == 0.0
        mock_logger.warning.assert_called()
        assert any("memory sampling" in str(call) for call in mock_logger.warning.call_args_list)

    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_sample_memory_multiple_calls(self, mock_logger, valid_context, mock_storage, mock_instrumentation):
        """Verify multiple calls to sample_memory() work correctly."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)

        reporter = JobExecutionReporter(
            context=valid_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        # First call
        mock_instrumentation.peak_memory_mb = 100.0
        mock_instrumentation.current_memory_mb = 150.0
        result1 = reporter.sample_memory()
        assert result1 == 150.0
        assert mock_instrumentation.peak_memory_mb == 150.0  # Peak updated

        # Second call with higher memory
        mock_instrumentation.current_memory_mb = 200.0
        result2 = reporter.sample_memory()
        assert result2 == 200.0
        assert mock_instrumentation.peak_memory_mb == 200.0  # Peak updated again

        # Third call with lower memory (peak should not decrease)
        mock_instrumentation.current_memory_mb = 120.0
        result3 = reporter.sample_memory()
        assert result3 == 200.0  # Peak remains at 200.0 (not decreased)
        assert mock_instrumentation.peak_memory_mb == 200.0

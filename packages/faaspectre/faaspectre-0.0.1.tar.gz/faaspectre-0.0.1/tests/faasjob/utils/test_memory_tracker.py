"""Tests for memory_tracker decorator."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from faaspectre.utils.memory_tracker import track_memory
from faaspectre.application.use_case.job_execution_reporter import JobExecutionReporter
from faaspectre.application.ports.metric_storage import MetricStorage
from faaspectre.application.ports.instrumentation import InstrumentationPort, TimingTracker
from faaspectre.domain.exceptions import InstrumentationError


# Stub implementations for ports
class StubMetricStorage(MetricStorage):
    """Stub implementation of MetricStorage for testing."""

    def __init__(self):
        self.saved_metrics = None
        self.saved_payload = None
        self.save_atomic_called = False

    def save_execution_metrics(self, metrics):
        """Stub implementation."""
        self.saved_metrics = metrics

    def save_execution_payload(self, payload):
        """Stub implementation."""
        self.saved_payload = payload

    def save_atomic(self, metrics, payload=None):
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


class TestTrackMemoryDecorator:
    """Tests for track_memory decorator."""

    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_track_memory_success(self, mock_logger, valid_execution_context, mock_storage, mock_instrumentation):
        """MT-001: Decorator samples memory before and after function execution."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)

        reporter = JobExecutionReporter(
            context=valid_execution_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        # Track calls to sample_memory
        sample_calls = []
        original_sample = reporter.sample_memory

        def tracked_sample():
            result = original_sample()
            sample_calls.append("sampled")
            return result

        reporter.sample_memory = tracked_sample

        @track_memory(reporter)
        def test_function():
            return "result"

        result = test_function()

        assert result == "result"
        assert len(sample_calls) == 2  # Before and after

    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_track_memory_with_args(self, mock_logger, valid_execution_context, mock_storage, mock_instrumentation):
        """Verify decorator preserves function arguments."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)

        reporter = JobExecutionReporter(
            context=valid_execution_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        sample_calls = []
        original_sample = reporter.sample_memory

        def tracked_sample():
            result = original_sample()
            sample_calls.append("sampled")
            return result

        reporter.sample_memory = tracked_sample

        @track_memory(reporter)
        def test_function(arg1, arg2, kwarg1=None):
            return f"{arg1}-{arg2}-{kwarg1}"

        result = test_function("a", "b", kwarg1="c")

        assert result == "a-b-c"
        assert len(sample_calls) == 2

    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_track_memory_with_exception(self, mock_logger, valid_execution_context, mock_storage, mock_instrumentation):
        """MT-002: Decorator samples memory even when function raises exception."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)

        reporter = JobExecutionReporter(
            context=valid_execution_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        sample_calls = []
        original_sample = reporter.sample_memory

        def tracked_sample():
            result = original_sample()
            sample_calls.append("sampled")
            return result

        reporter.sample_memory = tracked_sample

        @track_memory(reporter)
        def test_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            test_function()

        # Should sample before and after (even on error)
        assert len(sample_calls) == 2

    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_track_memory_preserves_function_metadata(self, mock_logger, valid_execution_context, mock_storage, mock_instrumentation):
        """Verify decorator preserves function name and docstring."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)

        reporter = JobExecutionReporter(
            context=valid_execution_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        @track_memory(reporter)
        def test_function():
            """Test function docstring."""
            return "result"

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test function docstring."

    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_track_memory_multiple_functions(self, mock_logger, valid_execution_context, mock_storage, mock_instrumentation):
        """Verify decorator works with multiple functions."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)

        reporter = JobExecutionReporter(
            context=valid_execution_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        sample_calls = []
        original_sample = reporter.sample_memory

        def tracked_sample():
            result = original_sample()
            sample_calls.append("sampled")
            return result

        reporter.sample_memory = tracked_sample

        @track_memory(reporter)
        def function1():
            return "result1"

        @track_memory(reporter)
        def function2():
            return "result2"

        result1 = function1()
        result2 = function2()

        assert result1 == "result1"
        assert result2 == "result2"
        assert len(sample_calls) == 4  # 2 per function

    @patch("faaspectre.application.use_case.job_execution_reporter.telemetric_logger")
    def test_track_memory_handles_sampling_error(self, mock_logger, valid_execution_context, mock_storage, mock_instrumentation):
        """Verify decorator handles InstrumentationError during sampling."""
        mock_logger.execution_context.return_value.__enter__ = Mock(return_value=None)
        mock_logger.execution_context.return_value.__exit__ = Mock(return_value=None)

        reporter = JobExecutionReporter(
            context=valid_execution_context,
            step_name="TEST_STEP",
            storage=mock_storage,
            instrumentation=mock_instrumentation,
        )

        # Make sample_memory raise an error (but it should handle it internally)
        mock_instrumentation.get_peak_memory_mb = Mock(side_effect=InstrumentationError("Memory error"))

        @track_memory(reporter)
        def test_function():
            return "result"

        # Should still work (sample_memory handles errors internally)
        result = test_function()

        assert result == "result"
        mock_logger.warning.assert_called()

"""Tests for TelemetricLogger."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from faaspectre.application.logger import TelemetricLogger, telemetric_logger


class TestTelemetricLoggerSingleton:
    """Tests for TelemetricLogger singleton pattern."""

    def test_singleton_instance(self):
        """LOG-001: Verify TelemetricLogger is singleton (same instance returned)."""
        logger1 = TelemetricLogger()
        logger2 = TelemetricLogger()

        assert logger1 is logger2
        assert logger1 is telemetric_logger

    @patch("faaspectre.application.logger.get_logger")
    def test_singleton_lazy_initialization(self, mock_get_logger):
        """Verify logger is lazily initialized on first access."""
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance

        # Clear singleton instance for this test
        TelemetricLogger._instances = {}

        logger = TelemetricLogger()
        assert logger._logger is None  # Not initialized yet

        # Access logger property (triggers initialization)
        logger_instance = logger.logger

        mock_get_logger.assert_called_once_with("faaspectre.telemetric")
        assert logger_instance == mock_logger_instance
        assert logger._logger == mock_logger_instance


class TestTelemetricLoggerExecutionContext:
    """Tests for TelemetricLogger.execution_context() context manager."""

    @patch("faaspectre.application.logger.get_logger")
    def test_execution_context_success(self, mock_get_logger):
        """LOG-002: Successful execution context manager usage."""
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance

        # Clear singleton instance for this test
        TelemetricLogger._instances = {}

        logger = TelemetricLogger()

        with logger.execution_context("correlation-123", "job-456") as yielded_logger:
            assert yielded_logger == mock_logger_instance

        # Verify info was called for start and completion
        assert mock_logger_instance.info.call_count >= 2

    @patch("faaspectre.application.logger.get_logger")
    def test_execution_context_logs_start(self, mock_get_logger):
        """Verify 'Execution started' logged on entry."""
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance

        # Clear singleton instance for this test
        TelemetricLogger._instances = {}

        logger = TelemetricLogger()

        with logger.execution_context("correlation-123", "job-456"):
            pass

        # Check that info was called with "Execution started"
        calls = [str(call) for call in mock_logger_instance.info.call_args_list]
        assert any("Execution started" in str(call) for call in mock_logger_instance.info.call_args_list)

    @patch("faaspectre.application.logger.get_logger")
    def test_execution_context_logs_end(self, mock_get_logger):
        """Verify 'Execution completed' logged on exit."""
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance

        # Clear singleton instance for this test
        TelemetricLogger._instances = {}

        logger = TelemetricLogger()

        with logger.execution_context("correlation-123", "job-456"):
            pass

        # Check that info was called with "Execution completed"
        calls = [str(call) for call in mock_logger_instance.info.call_args_list]
        assert any("Execution completed" in str(call) for call in mock_logger_instance.info.call_args_list)

    @patch("faaspectre.application.logger.get_logger")
    def test_execution_context_with_exception(self, mock_get_logger):
        """LOG-003: Handle exception within context (logs error, re-raises)."""
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance

        # Clear singleton instance for this test
        TelemetricLogger._instances = {}

        logger = TelemetricLogger()

        test_exception = ValueError("Test error")

        with pytest.raises(ValueError):
            with logger.execution_context("correlation-123", "job-456"):
                raise test_exception

        # Verify error was logged
        mock_logger_instance.error.assert_called()
        # Verify completion was still logged in finally
        assert any("Execution completed" in str(call) for call in mock_logger_instance.info.call_args_list)

    @patch("faaspectre.application.logger.get_logger")
    def test_execution_context_yields_logger(self, mock_get_logger):
        """Verify logger instance yielded from context manager."""
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance

        # Clear singleton instance for this test
        TelemetricLogger._instances = {}

        logger = TelemetricLogger()

        with logger.execution_context("correlation-123", "job-456") as yielded_logger:
            assert yielded_logger == mock_logger_instance


class TestTelemetricLoggerLogLevels:
    """Tests for TelemetricLogger log level methods."""

    @patch("faaspectre.application.logger.get_logger")
    def test_debug_logging(self, mock_get_logger):
        """LOG-004: Verify debug() calls logger.debug()."""
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance

        # Clear singleton instance for this test
        TelemetricLogger._instances = {}

        logger = TelemetricLogger()
        logger.debug("Debug message", correlation_id="test", job_id="test")

        mock_logger_instance.debug.assert_called_once_with("Debug message", extra={"correlation_id": "test", "job_id": "test"})

    @patch("faaspectre.application.logger.get_logger")
    def test_info_logging(self, mock_get_logger):
        """Verify info() calls logger.info()."""
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance

        # Clear singleton instance for this test
        TelemetricLogger._instances = {}

        logger = TelemetricLogger()
        logger.info("Info message", correlation_id="test")

        mock_logger_instance.info.assert_called_once_with("Info message", extra={"correlation_id": "test"})

    @patch("faaspectre.application.logger.get_logger")
    def test_warning_logging(self, mock_get_logger):
        """Verify warning() calls logger.warning()."""
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance

        # Clear singleton instance for this test
        TelemetricLogger._instances = {}

        logger = TelemetricLogger()
        logger.warning("Warning message", job_id="test")

        mock_logger_instance.warning.assert_called_once_with("Warning message", extra={"job_id": "test"})

    @patch("faaspectre.application.logger.get_logger")
    def test_error_logging(self, mock_get_logger):
        """Verify error() calls logger.error() with exc_info=True."""
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance

        # Clear singleton instance for this test
        TelemetricLogger._instances = {}

        logger = TelemetricLogger()
        logger.error("Error message", correlation_id="test")

        mock_logger_instance.error.assert_called_once_with(
            "Error message",
            extra={"correlation_id": "test"},
            exc_info=True,
        )

    @patch("faaspectre.application.logger.get_logger")
    def test_log_levels_extra_kwargs(self, mock_get_logger):
        """Verify extra kwargs passed to logger methods."""
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance

        # Clear singleton instance for this test
        TelemetricLogger._instances = {}

        logger = TelemetricLogger()
        logger.info("Message", correlation_id="test", job_id="test", extra_field="extra")

        mock_logger_instance.info.assert_called_once_with(
            "Message",
            extra={"correlation_id": "test", "job_id": "test", "extra_field": "extra"},
        )

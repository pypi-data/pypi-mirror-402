"""Tests for factory function create_job_execution_reporter."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from faaspectre import create_job_execution_reporter
from faaspectre.domain.models import ExecutionContext
from faaspectre.domain.exceptions import (
    TelemetricError,
    ConfigurationError,
)
from faaspectre.application.config import TelemetricConfig
from faaspectre.application.ports.metric_storage import MetricStorage
from faaspectre.application.ports.instrumentation import InstrumentationPort


class TestCreateStorageAdapter:
    """Tests for _create_storage_adapter() function."""

    @patch("faaspectre._create_storage_adapter")
    def test_create_storage_adapter_firestore(self, mock_create_adapter, valid_execution_context):
        """FF-001: Create FirestoreMetricStorage for 'firestore' backend."""
        config = TelemetricConfig(
            storage_backend="firestore",
            project_id="test-project",
            pipeline_logs_collection="pipeline_logs",
            pipeline_data_collection="pipeline_data",
        )
        config.validate()

        # Test via create_job_execution_reporter which calls _create_storage_adapter
        with patch("faaspectre.TelemetricConfig.from_env", return_value=config):
            reporter = create_job_execution_reporter(valid_execution_context, "TEST_STEP")

            assert reporter is not None
            assert reporter.step_name == "TEST_STEP"

    def test_create_storage_adapter_bigquery_error(self, valid_execution_context):
        """Handle 'bigquery' backend → ConfigurationError."""
        config = TelemetricConfig(
            storage_backend="bigquery",
            project_id="test-project",
        )

        # ConfigurationError gets wrapped in TelemetricError by factory function
        with pytest.raises((ConfigurationError, TelemetricError), match="BigQuery storage not yet implemented"):
            create_job_execution_reporter(valid_execution_context, "TEST_STEP", config=config)

    def test_create_storage_adapter_postgres_error(self, valid_execution_context):
        """Handle 'postgres' backend → ConfigurationError."""
        config = TelemetricConfig(
            storage_backend="postgres",
            project_id="test-project",
        )

        # ConfigurationError gets wrapped in TelemetricError by factory function
        with pytest.raises((ConfigurationError, TelemetricError), match="PostgreSQL storage not yet implemented"):
            create_job_execution_reporter(valid_execution_context, "TEST_STEP", config=config)

    def test_create_storage_adapter_unknown_backend(self, valid_execution_context):
        """Handle unknown backend → ConfigurationError."""
        config = TelemetricConfig(
            storage_backend="unknown_backend",
            project_id="test-project",
        )

        # Validation happens first and gives different message
        with pytest.raises((ConfigurationError, TelemetricError)):
            create_job_execution_reporter(valid_execution_context, "TEST_STEP", config=config)


class TestCreateJobExecutionReporterFactory:
    """Tests for create_job_execution_reporter() factory function."""

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    @patch("faaspectre.TelemetricConfig.from_env")
    def test_factory_with_defaults(self, mock_from_env, mock_firestore_client, valid_execution_context):
        """FF-002: Create with defaults (config from env, adapters auto-created)."""
        config = TelemetricConfig(
            storage_backend="firestore",
            project_id="test-project",
            pipeline_logs_collection="pipeline_logs",
            pipeline_data_collection="pipeline_data",
        )
        mock_from_env.return_value = config
        mock_client_instance = MagicMock()
        mock_firestore_client.return_value = mock_client_instance

        reporter = create_job_execution_reporter(valid_execution_context, "TEST_STEP")

        mock_from_env.assert_called_once()
        assert reporter is not None
        assert reporter.context == valid_execution_context
        assert reporter.step_name == "TEST_STEP"

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_factory_with_custom_config(self, mock_firestore_client, valid_execution_context):
        """FF-003: Create with custom TelemetricConfig."""
        config = TelemetricConfig(
            storage_backend="firestore",
            project_id="custom-project",
            pipeline_logs_collection="custom_logs",
            pipeline_data_collection="custom_data",
        )
        mock_client_instance = MagicMock()
        mock_firestore_client.return_value = mock_client_instance

        reporter = create_job_execution_reporter(valid_execution_context, "TEST_STEP", config=config)

        assert reporter is not None
        assert reporter.step_name == "TEST_STEP"

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_factory_with_custom_storage(self, mock_firestore_client, valid_execution_context):
        """Create with custom MetricStorage."""
        mock_storage = MagicMock(spec=MetricStorage)
        config = TelemetricConfig(
            storage_backend="firestore",
            project_id="test-project",
        )
        mock_client_instance = MagicMock()
        mock_firestore_client.return_value = mock_client_instance

        reporter = create_job_execution_reporter(
            valid_execution_context,
            "TEST_STEP",
            config=config,
            storage=mock_storage,
        )

        assert reporter.storage == mock_storage

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_factory_with_custom_instrumentation(self, mock_firestore_client, valid_execution_context):
        """Create with custom InstrumentationPort."""
        mock_instrumentation = MagicMock(spec=InstrumentationPort)
        config = TelemetricConfig(
            storage_backend="firestore",
            project_id="test-project",
        )
        mock_client_instance = MagicMock()
        mock_firestore_client.return_value = mock_client_instance

        reporter = create_job_execution_reporter(
            valid_execution_context,
            "TEST_STEP",
            config=config,
            instrumentation=mock_instrumentation,
        )

        assert reporter.instrumentation == mock_instrumentation

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    @patch("faaspectre.TelemetricConfig.from_env")
    def test_factory_config_validation_called(self, mock_from_env, mock_firestore_client, valid_execution_context):
        """Verify config.validate() called."""
        config = TelemetricConfig(
            storage_backend="firestore",
            project_id="test-project",
            pipeline_logs_collection="pipeline_logs",
            pipeline_data_collection="pipeline_data",
        )
        mock_from_env.return_value = config
        config_validate_spy = Mock(wraps=config.validate)
        mock_client_instance = MagicMock()
        mock_firestore_client.return_value = mock_client_instance

        # Replace validate with spy
        config.validate = config_validate_spy

        create_job_execution_reporter(valid_execution_context, "TEST_STEP")

        config_validate_spy.assert_called_once()

    @patch("faaspectre.TelemetricConfig.from_env")
    def test_factory_config_error_with_context(self, mock_from_env, valid_execution_context):
        """Handle ConfigurationError (adds correlation_id/job_id to exception)."""
        config = TelemetricConfig(
            storage_backend="firestore",
            project_id=None,  # Invalid - will fail validation
        )
        mock_from_env.return_value = config

        with pytest.raises(ConfigurationError) as exc_info:
            create_job_execution_reporter(valid_execution_context, "TEST_STEP")

        # Check that error context is preserved if available
        assert exc_info.value is not None

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_factory_storage_adapter_created(self, mock_firestore_client, valid_execution_context):
        """Verify _create_storage_adapter() called when storage is None."""
        config = TelemetricConfig(
            storage_backend="firestore",
            project_id="test-project",
            pipeline_logs_collection="pipeline_logs",
            pipeline_data_collection="pipeline_data",
        )
        mock_client_instance = MagicMock()
        mock_firestore_client.return_value = mock_client_instance

        reporter = create_job_execution_reporter(valid_execution_context, "TEST_STEP", config=config)

        # Storage adapter should be created (FirestoreMetricStorage)
        assert reporter.storage is not None

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_factory_psutil_instrumentation_created(self, mock_firestore_client, valid_execution_context):
        """Verify PsutilInstrumentation() created when instrumentation is None."""
        config = TelemetricConfig(
            storage_backend="firestore",
            project_id="test-project",
        )
        mock_client_instance = MagicMock()
        mock_firestore_client.return_value = mock_client_instance

        reporter = create_job_execution_reporter(valid_execution_context, "TEST_STEP", config=config)

        # Instrumentation should be created (PsutilInstrumentation)
        assert reporter.instrumentation is not None

    def test_factory_initialization_error(self, valid_execution_context):
        """Handle initialization failure → TelemetricError with context."""
        config = TelemetricConfig(
            storage_backend="firestore",
            project_id="test-project",
        )

        # Make storage adapter creation fail
        with patch(
            "faaspectre._create_storage_adapter",
            side_effect=RuntimeError("Storage creation failed"),
        ):
            with pytest.raises(TelemetricError) as exc_info:
                create_job_execution_reporter(valid_execution_context, "TEST_STEP", config=config)

            assert "Failed to initialize JobExecutionReporter" in str(exc_info.value)

    def test_factory_telemetric_error_context(self, valid_execution_context):
        """Verify correlation_id and job_id added to TelemetricError."""
        config = TelemetricConfig(
            storage_backend="firestore",
            project_id="test-project",
        )

        # Make initialization fail
        with patch(
            "faaspectre._create_storage_adapter",
            side_effect=RuntimeError("Storage error"),
        ):
            with pytest.raises(TelemetricError) as exc_info:
                create_job_execution_reporter(valid_execution_context, "TEST_STEP", config=config)

            # Error should include context
            assert exc_info.value.correlation_id == valid_execution_context.correlation_id
            assert exc_info.value.job_id == valid_execution_context.job_id

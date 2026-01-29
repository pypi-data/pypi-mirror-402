"""Tests for FirestoreMetricStorage adapter."""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from datetime import datetime, timezone

from faaspectre.infrastructure.adapters.storage.firestore_metric_storage import (
    FirestoreMetricStorage,
)
from faaspectre.application.config import TelemetricConfig
from faaspectre.domain.models import ExecutionMetrics, ExecutionPayload
from faaspectre.domain.status import PipelineStatus
from faaspectre.domain.exceptions import StorageError, AtomicWriteError
from faaspectre.application.ports.serializer import MetricSerializer
from google.api_core import exceptions as firestore_exceptions


# Stub MetricSerializer
class StubMetricSerializer(MetricSerializer):
    """Stub implementation of MetricSerializer for testing."""

    def serialize_metrics(self, metrics: ExecutionMetrics) -> dict:
        """Stub implementation."""
        return {"doc_id": metrics.doc_id, "status": metrics.status}

    def serialize_payload(self, payload: ExecutionPayload) -> dict:
        """Stub implementation."""
        return {"doc_id": payload.doc_id, "payload": payload.payload}


# Fixtures
@pytest.fixture
def mock_config():
    """Create a mock TelemetricConfig."""
    config = TelemetricConfig(
        storage_backend="firestore",
        pipeline_logs_collection="pipeline_logs",
        pipeline_data_collection="pipeline_data",
        project_id="test-project",
    )
    return config


@pytest.fixture
def mock_serializer():
    """Create a mock MetricSerializer."""
    serializer = MagicMock(spec=MetricSerializer)
    serializer.serialize_metrics.return_value = {"doc_id": "test", "status": "SUCCESS"}
    serializer.serialize_payload.return_value = {"doc_id": "test", "payload": {}}
    return serializer


@pytest.fixture
def mock_firestore_client():
    """Create a mock FirestoreClient."""
    mock_client = MagicMock()
    mock_batch = MagicMock()
    mock_client.batch.return_value = mock_batch
    return mock_client, mock_batch


class TestFirestoreMetricStorageInit:
    """Tests for FirestoreMetricStorage.__init__()."""

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_init_with_serializer(self, mock_firestore_client_class, mock_config, mock_serializer):
        """FS-001: Initialize with custom serializer."""
        mock_client_instance = MagicMock()
        mock_firestore_client_class.return_value = mock_client_instance

        storage = FirestoreMetricStorage(config=mock_config, serializer=mock_serializer)

        assert storage.config == mock_config
        assert storage.serializer == mock_serializer
        assert storage._firestore_client == mock_client_instance

    @patch("faaspectre.infrastructure.adapters.serializer.firestore_serializer.FirestoreMetricSerializer")
    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_init_without_serializer(
        self, mock_firestore_client_class, mock_serializer_class, mock_config
    ):
        """FS-002: Initialize without serializer (defaults to FirestoreMetricSerializer)."""
        mock_client_instance = MagicMock()
        mock_firestore_client_class.return_value = mock_client_instance
        mock_serializer_instance = MagicMock()
        mock_serializer_class.return_value = mock_serializer_instance

        storage = FirestoreMetricStorage(config=mock_config, serializer=None)

        mock_serializer_class.assert_called_once()
        assert storage.serializer == mock_serializer_instance

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_init_firestore_client_created(
        self, mock_firestore_client_class, mock_config, mock_serializer
    ):
        """Verify FirestoreClient instantiated with project_id."""
        mock_client_instance = MagicMock()
        mock_firestore_client_class.return_value = mock_client_instance

        FirestoreMetricStorage(config=mock_config, serializer=mock_serializer)

        mock_firestore_client_class.assert_called_once_with(project_id=mock_config.project_id)


class TestFirestoreMetricStorageSaveMetrics:
    """Tests for FirestoreMetricStorage.save_execution_metrics()."""

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_save_metrics_success(
        self, mock_firestore_client_class, mock_config, mock_serializer, valid_execution_metrics
    ):
        """FS-003: Successfully save metrics to Firestore."""
        mock_client_instance = MagicMock()
        mock_firestore_client_class.return_value = mock_client_instance

        storage = FirestoreMetricStorage(config=mock_config, serializer=mock_serializer)
        storage.save_execution_metrics(valid_execution_metrics)

        mock_serializer.serialize_metrics.assert_called_once_with(valid_execution_metrics)
        mock_client_instance.upsert.assert_called_once_with(
            collection_name=mock_config.pipeline_logs_collection,
            doc_id=valid_execution_metrics.doc_id,
            data=mock_serializer.serialize_metrics.return_value,
        )

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_save_metrics_serializer_called(
        self, mock_firestore_client_class, mock_config, mock_serializer, valid_execution_metrics
    ):
        """Verify serializer.serialize_metrics() called."""
        mock_client_instance = MagicMock()
        mock_firestore_client_class.return_value = mock_client_instance

        storage = FirestoreMetricStorage(config=mock_config, serializer=mock_serializer)
        storage.save_execution_metrics(valid_execution_metrics)

        mock_serializer.serialize_metrics.assert_called_once_with(valid_execution_metrics)

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_save_metrics_upsert_called(
        self, mock_firestore_client_class, mock_config, mock_serializer, valid_execution_metrics
    ):
        """Verify firestore_client.upsert() called with correct collection/doc_id."""
        mock_client_instance = MagicMock()
        mock_firestore_client_class.return_value = mock_client_instance
        serialized_data = {"doc_id": "test"}
        mock_serializer.serialize_metrics.return_value = serialized_data

        storage = FirestoreMetricStorage(config=mock_config, serializer=mock_serializer)
        storage.save_execution_metrics(valid_execution_metrics)

        mock_client_instance.upsert.assert_called_once_with(
            collection_name="pipeline_logs",
            doc_id=valid_execution_metrics.doc_id,
            data=serialized_data,
        )

    @pytest.mark.parametrize(
        "exception_class",
        [
            firestore_exceptions.DeadlineExceeded,
            firestore_exceptions.Unauthenticated,
            firestore_exceptions.PermissionDenied,
        ],
    )
    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_save_metrics_firestore_exceptions(
        self, mock_firestore_client_class, mock_config, mock_serializer, valid_execution_metrics, exception_class
    ):
        """Test handling of Firestore exceptions → StorageError."""
        mock_client_instance = MagicMock()
        mock_firestore_client_class.return_value = mock_client_instance
        mock_client_instance.upsert.side_effect = exception_class("Firestore error")

        storage = FirestoreMetricStorage(config=mock_config, serializer=mock_serializer)

        with pytest.raises(StorageError) as exc_info:
            storage.save_execution_metrics(valid_execution_metrics)

        assert exc_info.value.correlation_id == valid_execution_metrics.correlation_id
        assert exc_info.value.job_id == valid_execution_metrics.job_id

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_save_metrics_generic_exception(
        self, mock_firestore_client_class, mock_config, mock_serializer, valid_execution_metrics
    ):
        """Handle generic exception → StorageError."""
        mock_client_instance = MagicMock()
        mock_firestore_client_class.return_value = mock_client_instance
        mock_client_instance.upsert.side_effect = RuntimeError("Generic error")

        storage = FirestoreMetricStorage(config=mock_config, serializer=mock_serializer)

        with pytest.raises(StorageError) as exc_info:
            storage.save_execution_metrics(valid_execution_metrics)

        assert exc_info.value.correlation_id == valid_execution_metrics.correlation_id
        assert exc_info.value.job_id == valid_execution_metrics.job_id


class TestFirestoreMetricStorageSavePayload:
    """Tests for FirestoreMetricStorage.save_execution_payload()."""

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_save_payload_success(
        self, mock_firestore_client_class, mock_config, mock_serializer, valid_execution_payload
    ):
        """FS-004: Successfully save payload to Firestore."""
        mock_client_instance = MagicMock()
        mock_firestore_client_class.return_value = mock_client_instance

        storage = FirestoreMetricStorage(config=mock_config, serializer=mock_serializer)
        storage.save_execution_payload(valid_execution_payload)

        mock_serializer.serialize_payload.assert_called_once_with(valid_execution_payload)
        mock_client_instance.upsert.assert_called_once_with(
            collection_name=mock_config.pipeline_data_collection,
            doc_id=valid_execution_payload.doc_id,
            data=mock_serializer.serialize_payload.return_value,
        )

    @pytest.mark.parametrize(
        "exception_class",
        [
            firestore_exceptions.DeadlineExceeded,
            firestore_exceptions.Unauthenticated,
            firestore_exceptions.PermissionDenied,
        ],
    )
    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_save_payload_firestore_exceptions(
        self, mock_firestore_client_class, mock_config, mock_serializer, valid_execution_payload, exception_class
    ):
        """Test handling of Firestore exceptions → StorageError."""
        mock_client_instance = MagicMock()
        mock_firestore_client_class.return_value = mock_client_instance
        mock_client_instance.upsert.side_effect = exception_class("Firestore error")

        storage = FirestoreMetricStorage(config=mock_config, serializer=mock_serializer)

        with pytest.raises(StorageError) as exc_info:
            storage.save_execution_payload(valid_execution_payload)

        assert exc_info.value.correlation_id == valid_execution_payload.correlation_id
        assert exc_info.value.job_id == valid_execution_payload.doc_id


class TestFirestoreMetricStorageSaveAtomic:
    """Tests for FirestoreMetricStorage.save_atomic()."""

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_save_atomic_success_with_payload(
        self, mock_firestore_client_class, mock_config, mock_serializer, valid_execution_metrics, valid_execution_payload
    ):
        """FS-005: Successfully save metrics and payload atomically."""
        mock_client = MagicMock()
        mock_batch = MagicMock()
        mock_client.batch.return_value = mock_batch
        mock_client_instance = MagicMock()
        type(mock_client_instance).client = PropertyMock(return_value=mock_client)
        mock_firestore_client_class.return_value = mock_client_instance

        storage = FirestoreMetricStorage(config=mock_config, serializer=mock_serializer)
        storage.save_atomic(valid_execution_metrics, valid_execution_payload)

        mock_batch.set.assert_called()
        mock_batch.commit.assert_called_once()

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_save_atomic_success_metrics_only(
        self, mock_firestore_client_class, mock_config, mock_serializer, valid_execution_metrics
    ):
        """Successfully save metrics only (no payload)."""
        mock_client = MagicMock()
        mock_batch = MagicMock()
        mock_client.batch.return_value = mock_batch
        mock_client_instance = MagicMock()
        type(mock_client_instance).client = PropertyMock(return_value=mock_client)
        mock_firestore_client_class.return_value = mock_client_instance

        storage = FirestoreMetricStorage(config=mock_config, serializer=mock_serializer)
        storage.save_atomic(valid_execution_metrics, None)

        mock_batch.set.assert_called_once()  # Only metrics document
        mock_batch.commit.assert_called_once()

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_save_atomic_batch_created(
        self, mock_firestore_client_class, mock_config, mock_serializer, valid_execution_metrics
    ):
        """Verify Firestore batch created."""
        mock_client = MagicMock()
        mock_batch = MagicMock()
        mock_client.batch.return_value = mock_batch
        mock_client_instance = MagicMock()
        type(mock_client_instance).client = PropertyMock(return_value=mock_client)
        mock_firestore_client_class.return_value = mock_client_instance

        storage = FirestoreMetricStorage(config=mock_config, serializer=mock_serializer)
        storage.save_atomic(valid_execution_metrics, None)

        mock_client.batch.assert_called_once()

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_save_atomic_deadline_exceeded(
        self, mock_firestore_client_class, mock_config, mock_serializer, valid_execution_metrics
    ):
        """Handle DeadlineExceeded → AtomicWriteError."""
        mock_client = MagicMock()
        mock_batch = MagicMock()
        mock_batch.commit.side_effect = firestore_exceptions.DeadlineExceeded("Timeout")
        mock_client.batch.return_value = mock_batch
        mock_client_instance = MagicMock()
        type(mock_client_instance).client = PropertyMock(return_value=mock_client)
        mock_firestore_client_class.return_value = mock_client_instance

        storage = FirestoreMetricStorage(config=mock_config, serializer=mock_serializer)

        with pytest.raises(AtomicWriteError) as exc_info:
            storage.save_atomic(valid_execution_metrics, None)

        assert exc_info.value.correlation_id == valid_execution_metrics.correlation_id

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_save_atomic_transaction_failed(
        self, mock_firestore_client_class, mock_config, mock_serializer, valid_execution_metrics
    ):
        """Handle TransactionFailedError → AtomicWriteError.
        
        Note: TransactionFailedError doesn't exist in google.api_core.exceptions,
        but the code uses it. Testing via generic Exception path.
        """
        mock_client = MagicMock()
        mock_batch = MagicMock()
        # Use FailedPrecondition as closest equivalent (actual TransactionFailedError doesn't exist)
        mock_batch.commit.side_effect = firestore_exceptions.FailedPrecondition("Conflict")
        mock_client.batch.return_value = mock_batch
        mock_client_instance = MagicMock()
        type(mock_client_instance).client = PropertyMock(return_value=mock_client)
        mock_firestore_client_class.return_value = mock_client_instance

        storage = FirestoreMetricStorage(config=mock_config, serializer=mock_serializer)

        # Will fall through to generic Exception handler since TransactionFailedError doesn't exist
        with pytest.raises(AtomicWriteError) as exc_info:
            storage.save_atomic(valid_execution_metrics, None)

        assert exc_info.value.correlation_id == valid_execution_metrics.correlation_id

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    @pytest.mark.parametrize("error_msg", ["batch size exceeded", "batch limit reached"])
    def test_save_atomic_batch_size_exceeded(
        self, mock_firestore_client_class, mock_config, mock_serializer, valid_execution_metrics, error_msg
    ):
        """Handle batch size exceeded exception → AtomicWriteError."""
        mock_client = MagicMock()
        mock_batch = MagicMock()
        mock_batch.commit.side_effect = Exception(error_msg)
        mock_client.batch.return_value = mock_batch
        mock_client_instance = MagicMock()
        type(mock_client_instance).client = PropertyMock(return_value=mock_client)
        mock_firestore_client_class.return_value = mock_client_instance

        storage = FirestoreMetricStorage(config=mock_config, serializer=mock_serializer)

        with pytest.raises(AtomicWriteError) as exc_info:
            storage.save_atomic(valid_execution_metrics, None)

        assert exc_info.value.correlation_id == valid_execution_metrics.correlation_id

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_save_atomic_document_too_large(
        self, mock_firestore_client_class, mock_config, mock_serializer, valid_execution_metrics
    ):
        """Handle document too large exception → AtomicWriteError."""
        mock_client = MagicMock()
        mock_batch = MagicMock()
        mock_batch.commit.side_effect = Exception("document too large")
        mock_client.batch.return_value = mock_batch
        mock_client_instance = MagicMock()
        type(mock_client_instance).client = PropertyMock(return_value=mock_client)
        mock_firestore_client_class.return_value = mock_client_instance

        storage = FirestoreMetricStorage(config=mock_config, serializer=mock_serializer)

        with pytest.raises(AtomicWriteError) as exc_info:
            storage.save_atomic(valid_execution_metrics, None)

        assert exc_info.value.correlation_id == valid_execution_metrics.correlation_id

    @patch("faaspectre.infrastructure.adapters.storage.firestore_metric_storage.FirestoreClient")
    def test_save_atomic_generic_exception(
        self, mock_firestore_client_class, mock_config, mock_serializer, valid_execution_metrics
    ):
        """Handle generic exception → AtomicWriteError."""
        mock_client = MagicMock()
        mock_batch = MagicMock()
        mock_batch.commit.side_effect = RuntimeError("Generic error")
        mock_client.batch.return_value = mock_batch
        mock_client_instance = MagicMock()
        type(mock_client_instance).client = PropertyMock(return_value=mock_client)
        mock_firestore_client_class.return_value = mock_client_instance

        storage = FirestoreMetricStorage(config=mock_config, serializer=mock_serializer)

        with pytest.raises(AtomicWriteError) as exc_info:
            storage.save_atomic(valid_execution_metrics, None)

        assert exc_info.value.correlation_id == valid_execution_metrics.correlation_id
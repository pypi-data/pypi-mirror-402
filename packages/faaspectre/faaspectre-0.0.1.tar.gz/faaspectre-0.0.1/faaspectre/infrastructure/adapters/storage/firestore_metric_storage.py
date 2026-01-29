"""Firestore storage adapter for metric persistence."""

from typing import Optional

from google.api_core import exceptions as firestore_exceptions

from ....application.ports.metric_storage import MetricStorage
from ....application.ports.serializer import MetricSerializer
from ....application.config import TelemetricConfig
from ....domain.models import ExecutionMetrics, ExecutionPayload
from ....domain.exceptions import StorageError, AtomicWriteError
from ...utils.firestore_client import FirestoreClient


class FirestoreMetricStorage(MetricStorage):
    """Firestore implementation of MetricStorage port.

    Uses FirestoreMetricSerializer to convert domain models to Firestore format.
    """

    def __init__(
        self,
        config: TelemetricConfig,
        serializer: Optional[MetricSerializer] = None,
    ):
        """Initialize FirestoreMetricStorage.

        Args:
            config: TelemetricConfig with Firestore settings
            serializer: Optional MetricSerializer (defaults to FirestoreMetricSerializer)
        """
        self.config = config
        if serializer is None:
            from ..serializer.firestore_serializer import FirestoreMetricSerializer

            serializer = FirestoreMetricSerializer()
        self.serializer = serializer
        self._firestore_client = FirestoreClient(project_id=config.project_id)

    def save_execution_metrics(self, metrics: ExecutionMetrics) -> None:
        """Save execution metrics to Firestore.

        Args:
            metrics: ExecutionMetrics to save

        Raises:
            StorageError: On storage operation failure
        """
        try:
            serialized = self.serializer.serialize_metrics(metrics)
            self._firestore_client.upsert(
                collection_name=self.config.pipeline_logs_collection,
                doc_id=metrics.doc_id,
                data=serialized,
            )
        except firestore_exceptions.DeadlineExceeded as e:
            raise StorageError(
                f"Firestore operation timed out: {e}",
                correlation_id=metrics.correlation_id,
                job_id=metrics.job_id,
            ) from e
        except firestore_exceptions.Unauthenticated as e:
            raise StorageError(
                f"Firestore authentication failed: {e}",
                correlation_id=metrics.correlation_id,
                job_id=metrics.job_id,
            ) from e
        except firestore_exceptions.PermissionDenied as e:
            raise StorageError(
                f"Firestore permission denied: {e}",
                correlation_id=metrics.correlation_id,
                job_id=metrics.job_id,
            ) from e
        except Exception as e:
            raise StorageError(
                f"Firestore operation failed: {e}",
                correlation_id=metrics.correlation_id,
                job_id=metrics.job_id,
            ) from e

    def save_execution_payload(self, payload: ExecutionPayload) -> None:
        """Save execution payload to Firestore.

        Args:
            payload: ExecutionPayload to save

        Raises:
            StorageError: On storage operation failure
        """
        try:
            serialized = self.serializer.serialize_payload(payload)
            self._firestore_client.upsert(
                collection_name=self.config.pipeline_data_collection,
                doc_id=payload.doc_id,
                data=serialized,
            )
        except firestore_exceptions.DeadlineExceeded as e:
            raise StorageError(
                f"Firestore operation timed out: {e}",
                correlation_id=payload.correlation_id,
                job_id=payload.doc_id,
            ) from e
        except firestore_exceptions.Unauthenticated as e:
            raise StorageError(
                f"Firestore authentication failed: {e}",
                correlation_id=payload.correlation_id,
                job_id=payload.doc_id,
            ) from e
        except firestore_exceptions.PermissionDenied as e:
            raise StorageError(
                f"Firestore permission denied: {e}",
                correlation_id=payload.correlation_id,
                job_id=payload.doc_id,
            ) from e
        except Exception as e:
            raise StorageError(
                f"Firestore operation failed: {e}",
                correlation_id=payload.correlation_id,
                job_id=payload.doc_id,
            ) from e

    def save_atomic(
        self, metrics: ExecutionMetrics, payload: Optional[ExecutionPayload] = None
    ) -> None:
        """Save metrics and payload atomically using Firestore batch.

        Args:
            metrics: ExecutionMetrics to save
            payload: Optional ExecutionPayload to save

        Raises:
            AtomicWriteError: On atomic write failure
        """
        try:
            # Serialize both
            metrics_data = self.serializer.serialize_metrics(metrics)
            payload_data = (
                self.serializer.serialize_payload(payload) if payload else None
            )

            # Use Firestore batch for atomic writes
            batch = self._firestore_client.client.batch()

            # Add metrics document
            metrics_ref = (
                self._firestore_client.client.collection(
                    self.config.pipeline_logs_collection
                )
                .document(metrics.doc_id)
            )
            batch.set(metrics_ref, metrics_data)

            # Add payload document if provided
            if payload_data:
                payload_ref = (
                    self._firestore_client.client.collection(
                        self.config.pipeline_data_collection
                    )
                    .document(payload.doc_id)
                )
                batch.set(payload_ref, payload_data)

            # Commit batch (atomic operation)
            batch.commit()

        except firestore_exceptions.DeadlineExceeded as e:
            raise AtomicWriteError(
                f"Firestore batch operation timed out: {e}",
                correlation_id=metrics.correlation_id,
                job_id=metrics.job_id,
            ) from e
        except Exception as e:
            # Check for batch size exceeded or document too large
            error_msg = str(e).lower()
            if "batch" in error_msg and ("size" in error_msg or "limit" in error_msg):
                raise AtomicWriteError(
                    f"Firestore batch size exceeded: {e}",
                    correlation_id=metrics.correlation_id,
                    job_id=metrics.job_id,
                ) from e
            if "document" in error_msg and "large" in error_msg:
                raise AtomicWriteError(
                    f"Firestore document too large: {e}",
                    correlation_id=metrics.correlation_id,
                    job_id=metrics.job_id,
                ) from e
            raise AtomicWriteError(
                f"Firestore atomic write failed: {e}",
                correlation_id=metrics.correlation_id,
                job_id=metrics.job_id,
            ) from e

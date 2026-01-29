"""Storage port for backend-agnostic metric persistence."""

from abc import ABC, abstractmethod
from typing import Optional

from ...domain.models import ExecutionMetrics, ExecutionPayload
from ...domain.exceptions import StorageError, AtomicWriteError


class MetricStorage(ABC):
    """Abstract base class for metric storage operations.

    Defines contract for all storage backends (Firestore, BigQuery, PostgreSQL, etc.).
    """

    @abstractmethod
    def save_execution_metrics(self, metrics: ExecutionMetrics) -> None:
        """Save execution metrics to storage.

        Args:
            metrics: ExecutionMetrics to save

        Raises:
            StorageError: On storage operation failure (network, auth, permission, timeout)
        """
        pass

    @abstractmethod
    def save_execution_payload(self, payload: ExecutionPayload) -> None:
        """Save execution payload to storage.

        Args:
            payload: ExecutionPayload to save

        Raises:
            StorageError: On storage operation failure
        """
        pass

    @abstractmethod
    def save_atomic(
        self, metrics: ExecutionMetrics, payload: Optional[ExecutionPayload] = None
    ) -> None:
        """Save metrics and payload atomically (batch/transaction).

        Args:
            metrics: ExecutionMetrics to save
            payload: Optional ExecutionPayload to save

        Raises:
            AtomicWriteError: On atomic write failure (partial write, transaction conflict, batch size exceeded)
        """
        pass

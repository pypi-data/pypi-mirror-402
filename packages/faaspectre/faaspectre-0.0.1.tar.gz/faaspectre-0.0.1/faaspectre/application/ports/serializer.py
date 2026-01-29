"""Serialization port for backend-agnostic data conversion."""

from abc import ABC, abstractmethod
from typing import Dict, Any

from ...domain.models import ExecutionMetrics, ExecutionPayload


class MetricSerializer(ABC):
    """Abstract base class for metric serialization.

    Converts domain models to backend-specific dictionary format.
    """

    @abstractmethod
    def serialize_metrics(self, metrics: ExecutionMetrics) -> Dict[str, Any]:
        """Serialize ExecutionMetrics to backend-specific dictionary format.

        Args:
            metrics: ExecutionMetrics domain model

        Returns:
            Dictionary ready for backend storage

        Raises:
            ValidationError: If serialization fails due to invalid data
        """
        pass

    @abstractmethod
    def serialize_payload(self, payload: ExecutionPayload) -> Dict[str, Any]:
        """Serialize ExecutionPayload to backend-specific dictionary format.

        Args:
            payload: ExecutionPayload domain model

        Returns:
            Dictionary ready for backend storage

        Raises:
            ValidationError: If serialization fails due to invalid data
        """
        pass

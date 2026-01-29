"""Firestore serialization adapter."""

from typing import Dict, Any

from ....application.ports.serializer import MetricSerializer
from ....domain.models import ExecutionMetrics, ExecutionPayload
from ....domain.exceptions import ValidationError


class FirestoreMetricSerializer(MetricSerializer):
    """Firestore-specific serialization adapter.

    Converts domain models to Firestore-compatible dictionary format.
    """
    
    # Reserved fields that cannot be overridden by payload
    RESERVED_FIELDS = {"doc_id", "correlation_id", "step_name", "created_at"}

    def serialize_metrics(self, metrics: ExecutionMetrics) -> Dict[str, Any]:
        """Serialize ExecutionMetrics to Firestore-compatible dict.

        Args:
            metrics: ExecutionMetrics domain model

        Returns:
            Dictionary ready for Firestore document.set()

        Raises:
            ValidationError: If serialization fails due to invalid data
        """
        try:
            result = {
                "doc_id": metrics.doc_id,
                "correlation_id": metrics.correlation_id,
                "job_id": metrics.job_id,
                "prev_job_id": metrics.prev_job_id,
                "step_name": metrics.step_name,
                "triggered_by": metrics.triggered_by,
                "created_at": metrics.created_at,  # Already ISO 8601 string
                "start_time_epoch": float(metrics.start_time_epoch),
                "status": metrics.status,
            }

            # Add optional fields (Firestore allows None)
            if metrics.end_time_epoch is not None:
                result["end_time_epoch"] = float(metrics.end_time_epoch)
            if metrics.duration_ms is not None:
                result["duration_ms"] = float(metrics.duration_ms)
            if metrics.memory_mb is not None:
                result["memory_mb"] = float(metrics.memory_mb)
            if metrics.error_summary is not None:
                result["error_summary"] = str(metrics.error_summary)

            return result
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"Failed to serialize ExecutionMetrics: {e}",
                correlation_id=metrics.correlation_id,
                job_id=metrics.job_id,
            ) from e

    def serialize_payload(self, payload: ExecutionPayload) -> Dict[str, Any]:
        """Serialize ExecutionPayload to Firestore-compatible dict.

        Flattens the payload structure by merging payload fields into the top level
        for better querying across partitions. Includes step_name and created_at for filtering.

        Note: Nested dicts in payload are preserved (Firestore supports nested structures),
        but queries on nested fields require dot notation (e.g., "nested.deep.value").

        Args:
            payload: ExecutionPayload domain model

        Returns:
            Dictionary ready for Firestore document.set() with flattened structure

        Raises:
            ValidationError: If serialization fails due to invalid data or reserved field conflicts
        """
        try:
            # Check for reserved field conflicts in payload
            if payload.payload:
                conflicting_fields = self.RESERVED_FIELDS.intersection(payload.payload.keys())
                if conflicting_fields:
                    raise ValidationError(
                        f"Payload cannot override reserved fields: {sorted(conflicting_fields)}. "
                        f"Reserved fields are: {sorted(self.RESERVED_FIELDS)}",
                        correlation_id=payload.correlation_id,
                        job_id=payload.doc_id,
                    )
            
            # Start with metadata fields
            result = {
                "doc_id": payload.doc_id,
                "correlation_id": payload.correlation_id,
                "step_name": payload.step_name,
                "created_at": payload.created_at,  # Already ISO 8601 string
            }
            
            # Flatten payload: merge payload fields into top level
            # This allows querying across partitions by step_name, created_at, and payload fields
            # Note: Nested dicts are preserved (Firestore supports nested structures)
            # but queries on nested fields require dot notation (e.g., "nested.deep.value")
            if payload.payload:
                result.update(payload.payload)
            
            return result
        except ValidationError:
            # Re-raise ValidationError as-is
            raise
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"Failed to serialize ExecutionPayload: {e}",
                correlation_id=payload.correlation_id,
                job_id=payload.doc_id,
            ) from e

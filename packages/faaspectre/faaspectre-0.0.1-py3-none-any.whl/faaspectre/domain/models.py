"""Domain models for Telemetric Reporter."""

from typing import Optional, Any, Dict
from dataclasses import dataclass, field
from datetime import datetime

from .status import PipelineStatus
from .exceptions import ValidationError
from .validators import (
    validate_uuid_v4,
    validate_iso8601_utc,
    validate_time_ordering,
)


@dataclass
class ExecutionContext:
    """Execution context from workflow payload.

    Contains correlation_id, job_id, and workflow metadata.
    """

    correlation_id: str
    job_id: str
    step_name: str
    triggered_by: str
    prev_job_id: Optional[str] = None

    def __post_init__(self):
        """Validate ExecutionContext after initialization."""
        if not validate_uuid_v4(self.correlation_id):
            raise ValidationError(
                f"Invalid correlation_id format (must be UUID-v4): {self.correlation_id}",
                correlation_id=self.correlation_id,
                job_id=self.job_id,
            )

    @classmethod
    def from_workflow_payload(cls, payload: Dict[str, Any]) -> "ExecutionContext":
        """Create ExecutionContext from workflow payload dictionary.

        Args:
            payload: Workflow payload dictionary with correlation_id, job_id, etc.

        Returns:
            ExecutionContext instance

        Raises:
            ValidationError: If required fields are missing or invalid
        """
        correlation_id = payload.get("correlation_id")
        job_id = payload.get("job_id")
        step_name = payload.get("step_name")
        triggered_by = payload.get("triggered_by")
        prev_job_id = payload.get("prev_job_id")

        if not correlation_id:
            raise ValidationError("Missing required field: correlation_id")
        if not job_id:
            raise ValidationError("Missing required field: job_id")
        if not step_name:
            raise ValidationError("Missing required field: step_name")
        if not triggered_by:
            raise ValidationError("Missing required field: triggered_by")

        return cls(
            correlation_id=correlation_id,
            job_id=job_id,
            step_name=step_name,
            triggered_by=triggered_by,
            prev_job_id=prev_job_id,
        )


@dataclass
class ExecutionMetrics:
    """Execution metrics for pipeline_logs collection.

    Represents operational metrics for dashboard insights.
    """

    doc_id: str
    correlation_id: str
    job_id: str
    step_name: str
    triggered_by: str
    created_at: str  # ISO 8601 UTC string
    start_time_epoch: float
    status: str  # PipelineStatus enum value
    prev_job_id: Optional[str] = None
    end_time_epoch: Optional[float] = None
    duration_ms: Optional[float] = None
    memory_mb: Optional[float] = None
    error_summary: Optional[str] = None

    def __post_init__(self):
        """Validate ExecutionMetrics after initialization."""
        # Validate status
        valid_statuses = [s.value for s in PipelineStatus]
        if self.status not in valid_statuses:
            raise ValidationError(
                f"Invalid status: {self.status}. Must be one of {valid_statuses}",
                correlation_id=self.correlation_id,
                job_id=self.job_id,
            )

        # Validate correlation_id format
        if not validate_uuid_v4(self.correlation_id):
            raise ValidationError(
                f"Invalid correlation_id format (must be UUID-v4): {self.correlation_id}",
                correlation_id=self.correlation_id,
                job_id=self.job_id,
            )

        # Validate created_at format
        if not validate_iso8601_utc(self.created_at):
            raise ValidationError(
                f"Invalid created_at format (must be ISO 8601 UTC): {self.created_at}",
                correlation_id=self.correlation_id,
                job_id=self.job_id,
            )

        # Validate time ordering
        if not validate_time_ordering(self.start_time_epoch, self.end_time_epoch):
            raise ValidationError(
                f"Invalid time ordering: end_time_epoch ({self.end_time_epoch}) must be >= start_time_epoch ({self.start_time_epoch})",
                correlation_id=self.correlation_id,
                job_id=self.job_id,
            )


@dataclass
class ExecutionPayload:
    """Execution payload for pipeline_data collection.

    Contains flexible payload structure for detailed audit trails.
    Fields are flattened at the top level for querying across partitions.
    """

    doc_id: str
    correlation_id: str
    step_name: str
    created_at: str  # ISO 8601 UTC string
    payload: Dict[str, Any]

    def __post_init__(self):
        """Validate ExecutionPayload after initialization."""
        # Validate correlation_id format
        if not validate_uuid_v4(self.correlation_id):
            raise ValidationError(
                f"Invalid correlation_id format (must be UUID-v4): {self.correlation_id}",
                correlation_id=self.correlation_id,
                job_id=self.doc_id,
            )
        
        # Validate created_at format
        if not validate_iso8601_utc(self.created_at):
            raise ValidationError(
                f"Invalid created_at format (must be ISO 8601 UTC): {self.created_at}",
                correlation_id=self.correlation_id,
                job_id=self.doc_id,
            )
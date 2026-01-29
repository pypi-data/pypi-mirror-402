"""Tests for domain models."""

import pytest
import uuid
from datetime import datetime, timezone

from faaspectre.domain.models import (
    ExecutionContext,
    ExecutionMetrics,
    ExecutionPayload,
)
from faaspectre.domain.status import PipelineStatus
from faaspectre.domain.exceptions import ValidationError


class TestExecutionContext:
    """Tests for ExecutionContext model."""

    def test_valid_creation(self, valid_execution_context):
        """TC-001: Valid ExecutionContext Creation."""
        assert valid_execution_context.correlation_id is not None
        assert valid_execution_context.job_id is not None
        assert valid_execution_context.step_name == "TEST_STEP"
        assert valid_execution_context.triggered_by == "ETL_WORKFLOW"

    def test_from_workflow_payload(self, valid_workflow_payload):
        """TC-002: Create ExecutionContext from workflow payload."""
        context = ExecutionContext.from_workflow_payload(valid_workflow_payload)
        assert context.correlation_id == valid_workflow_payload["correlation_id"]
        assert context.job_id == valid_workflow_payload["job_id"]
        assert context.step_name == valid_workflow_payload["step_name"]

    def test_from_workflow_payload_missing_fields(self):
        """TC-003: Missing required fields raises ValidationError."""
        incomplete_payload = {"correlation_id": str(uuid.uuid4())}
        with pytest.raises(ValidationError, match="Missing required field"):
            ExecutionContext.from_workflow_payload(incomplete_payload)

    def test_invalid_correlation_id(self):
        """TC-004: Invalid correlation_id raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid correlation_id format"):
            ExecutionContext(
                correlation_id="not-a-uuid",
                job_id="job-123",
                step_name="TEST",
                triggered_by="ETL_WORKFLOW",
            )

    def test_optional_prev_job_id(self, valid_correlation_id, valid_job_id):
        """TC-005: Optional prev_job_id as None."""
        context = ExecutionContext(
            correlation_id=valid_correlation_id,
            job_id=valid_job_id,
            step_name="TEST_STEP",
            triggered_by="ETL_WORKFLOW",
            prev_job_id=None,
        )
        assert context.prev_job_id is None


class TestExecutionMetrics:
    """Tests for ExecutionMetrics model."""

    def test_valid_creation(self, valid_execution_metrics):
        """EM-001: Valid ExecutionMetrics Creation."""
        assert valid_execution_metrics.doc_id is not None
        assert valid_execution_metrics.status == PipelineStatus.SUCCESS.value

    def test_invalid_status(self, valid_correlation_id, valid_job_id):
        """EM-002: Invalid status raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid status"):
            ExecutionMetrics(
                doc_id=valid_job_id,
                correlation_id=valid_correlation_id,
                job_id=valid_job_id,
                step_name="TEST",
                triggered_by="ETL_WORKFLOW",
                created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                start_time_epoch=1000.0,
                status="INVALID_STATUS",
            )

    def test_time_ordering_validation(self, valid_correlation_id, valid_job_id):
        """EM-003: Time ordering validation."""
        with pytest.raises(ValidationError, match="time ordering"):
            ExecutionMetrics(
                doc_id=valid_job_id,
                correlation_id=valid_correlation_id,
                job_id=valid_job_id,
                step_name="TEST",
                triggered_by="ETL_WORKFLOW",
                created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                start_time_epoch=1000.0,
                end_time_epoch=500.0,  # End before start
                status=PipelineStatus.SUCCESS.value,
            )

    def test_invalid_correlation_id(self, valid_job_id):
        """EM-004: Invalid correlation_id raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid correlation_id format"):
            ExecutionMetrics(
                doc_id=valid_job_id,
                correlation_id="not-a-uuid",
                job_id=valid_job_id,
                step_name="TEST",
                triggered_by="ETL_WORKFLOW",
                created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                start_time_epoch=1000.0,
                status=PipelineStatus.SUCCESS.value,
            )

    def test_invalid_iso8601_date(self, valid_correlation_id, valid_job_id):
        """EM-005: Invalid ISO 8601 date format."""
        with pytest.raises(ValidationError, match="Invalid created_at format"):
            ExecutionMetrics(
                doc_id=valid_job_id,
                correlation_id=valid_correlation_id,
                job_id=valid_job_id,
                step_name="TEST",
                triggered_by="ETL_WORKFLOW",
                created_at="2026-01-16",  # Missing time component
                start_time_epoch=1000.0,
                status=PipelineStatus.SUCCESS.value,
            )

    def test_optional_fields_none(self, valid_correlation_id, valid_job_id):
        """EM-006: Optional fields as None."""
        metrics = ExecutionMetrics(
            doc_id=valid_job_id,
            correlation_id=valid_correlation_id,
            job_id=valid_job_id,
            step_name="TEST",
            triggered_by="ETL_WORKFLOW",
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            start_time_epoch=1000.0,
            end_time_epoch=None,
            duration_ms=None,
            memory_mb=None,
            error_summary=None,
            status=PipelineStatus.PENDING.value,
        )
        assert metrics.end_time_epoch is None
        assert metrics.duration_ms is None
        assert metrics.memory_mb is None

    def test_no_serialization_methods(self, valid_execution_metrics):
        """EM-007: Domain model storage-agnostic - no serialization methods."""
        assert not hasattr(valid_execution_metrics, "to_firestore_dict")
        assert not hasattr(valid_execution_metrics, "to_bigquery_row")


class TestExecutionPayload:
    """Tests for ExecutionPayload model."""

    def test_valid_creation(self, valid_execution_payload):
        """EP-001: Valid ExecutionPayload Creation."""
        assert valid_execution_payload.doc_id is not None
        assert valid_execution_payload.payload is not None

    def test_invalid_correlation_id(self, valid_job_id):
        """EP-002: Invalid correlation_id raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid correlation_id format"):
            ExecutionPayload(
                doc_id=valid_job_id,
                correlation_id="invalid",
                payload={"key": "value"},
            )

    def test_flexible_payload_structure(self, valid_correlation_id, valid_job_id):
        """EP-003: Flexible payload structure."""
        # Simple dict
        payload1 = ExecutionPayload(
            doc_id=valid_job_id,
            correlation_id=valid_correlation_id,
            payload={"key": "value"},
        )
        assert payload1.payload == {"key": "value"}

        # Nested dict
        payload2 = ExecutionPayload(
            doc_id=valid_job_id,
            correlation_id=valid_correlation_id,
            payload={"nested": {"deep": "value"}},
        )
        assert payload2.payload["nested"]["deep"] == "value"

        # List in payload
        payload3 = ExecutionPayload(
            doc_id=valid_job_id,
            correlation_id=valid_correlation_id,
            payload={"items": [1, 2, 3]},
        )
        assert payload3.payload["items"] == [1, 2, 3]

    def test_no_serialization_methods(self, valid_execution_payload):
        """EP-004: Domain model storage-agnostic - no serialization methods."""
        assert not hasattr(valid_execution_payload, "to_firestore_dict")
        assert not hasattr(valid_execution_payload, "to_bigquery_row")

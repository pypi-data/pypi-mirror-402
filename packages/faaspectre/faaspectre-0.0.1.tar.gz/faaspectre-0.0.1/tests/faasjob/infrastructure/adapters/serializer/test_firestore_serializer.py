"""Tests for infrastructure serializers."""

import pytest
from datetime import datetime, timezone

from faaspectre.infrastructure.adapters.serializer.firestore_serializer import (
    FirestoreMetricSerializer,
)
from faaspectre.domain.models import ExecutionMetrics, ExecutionPayload
from faaspectre.domain.status import PipelineStatus


class TestFirestoreMetricSerializer:
    """Tests for FirestoreMetricSerializer."""

    @pytest.fixture
    def serializer(self):
        """Create serializer instance."""
        return FirestoreMetricSerializer()

    def test_serialize_metrics(self, serializer, valid_execution_metrics):
        """Test serialization of ExecutionMetrics."""
        result = serializer.serialize_metrics(valid_execution_metrics)

        assert isinstance(result, dict)
        assert result["doc_id"] == valid_execution_metrics.doc_id
        assert result["correlation_id"] == valid_execution_metrics.correlation_id
        assert result["status"] == valid_execution_metrics.status
        assert isinstance(result["start_time_epoch"], float)
        assert isinstance(result["end_time_epoch"], float)
        assert isinstance(result["duration_ms"], float)
        assert isinstance(result["memory_mb"], float)

    def test_serialize_metrics_with_none_values(self, serializer, valid_correlation_id, valid_job_id):
        """Test serialization with None optional values."""
        metrics = ExecutionMetrics(
            doc_id=valid_job_id,
            correlation_id=valid_correlation_id,
            job_id=valid_job_id,
            step_name="TEST",
            triggered_by="ETL_WORKFLOW",
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            start_time_epoch=1000.0,
            status=PipelineStatus.PENDING.value,
            end_time_epoch=None,
            duration_ms=None,
            memory_mb=None,
        )

        result = serializer.serialize_metrics(metrics)
        assert "end_time_epoch" not in result
        assert "duration_ms" not in result
        assert "memory_mb" not in result

    def test_serialize_payload(self, serializer, valid_execution_payload):
        """Test serialization of ExecutionPayload with flattened structure."""
        result = serializer.serialize_payload(valid_execution_payload)

        assert isinstance(result, dict)
        # Check reserved fields are present
        assert result["doc_id"] == valid_execution_payload.doc_id
        assert result["correlation_id"] == valid_execution_payload.correlation_id
        assert result["step_name"] == valid_execution_payload.step_name
        assert result["created_at"] == valid_execution_payload.created_at
        # Check payload fields are flattened at top level
        assert result["result"] == "success"
        assert result["count"] == 100
        # Check payload is NOT nested
        assert "payload" not in result

    def test_serialize_payload_flattening(self, serializer, valid_correlation_id, valid_job_id):
        """Test that payload fields are flattened to top level."""
        payload = ExecutionPayload(
            doc_id=valid_job_id,
            correlation_id=valid_correlation_id,
            step_name="TEST_STEP",
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            payload={
                "profile_id": "6725157603682583557",
                "socialnetwork": "tiktok",
                "nested": {"deep": {"value": 123}},
            },
        )

        result = serializer.serialize_payload(payload)
        
        # Reserved fields at top level
        assert result["doc_id"] == valid_job_id
        assert result["correlation_id"] == valid_correlation_id
        assert result["step_name"] == "TEST_STEP"
        assert "created_at" in result
        
        # Payload fields flattened at top level
        assert result["profile_id"] == "6725157603682583557"
        assert result["socialnetwork"] == "tiktok"
        assert result["nested"] == {"deep": {"value": 123}}
        
        # No nested "payload" key
        assert "payload" not in result

    def test_serialize_payload_reserved_field_conflict_doc_id(
        self, serializer, valid_correlation_id, valid_job_id
    ):
        """Test that payload cannot override doc_id reserved field."""
        from faaspectre.domain.exceptions import ValidationError

        payload = ExecutionPayload(
            doc_id=valid_job_id,
            correlation_id=valid_correlation_id,
            step_name="TEST_STEP",
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            payload={"doc_id": "attempted_override"},
        )

        with pytest.raises(ValidationError) as exc_info:
            serializer.serialize_payload(payload)

        assert "doc_id" in str(exc_info.value)
        assert "reserved fields" in str(exc_info.value).lower()

    def test_serialize_payload_reserved_field_conflict_correlation_id(
        self, serializer, valid_correlation_id, valid_job_id
    ):
        """Test that payload cannot override correlation_id reserved field."""
        from faaspectre.domain.exceptions import ValidationError

        payload = ExecutionPayload(
            doc_id=valid_job_id,
            correlation_id=valid_correlation_id,
            step_name="TEST_STEP",
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            payload={"correlation_id": "attempted_override"},
        )

        with pytest.raises(ValidationError) as exc_info:
            serializer.serialize_payload(payload)

        assert "correlation_id" in str(exc_info.value)
        assert "reserved fields" in str(exc_info.value).lower()

    def test_serialize_payload_reserved_field_conflict_step_name(
        self, serializer, valid_correlation_id, valid_job_id
    ):
        """Test that payload cannot override step_name reserved field."""
        from faaspectre.domain.exceptions import ValidationError

        payload = ExecutionPayload(
            doc_id=valid_job_id,
            correlation_id=valid_correlation_id,
            step_name="TEST_STEP",
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            payload={"step_name": "attempted_override"},
        )

        with pytest.raises(ValidationError) as exc_info:
            serializer.serialize_payload(payload)

        assert "step_name" in str(exc_info.value)
        assert "reserved fields" in str(exc_info.value).lower()

    def test_serialize_payload_reserved_field_conflict_created_at(
        self, serializer, valid_correlation_id, valid_job_id
    ):
        """Test that payload cannot override created_at reserved field."""
        from faaspectre.domain.exceptions import ValidationError

        payload = ExecutionPayload(
            doc_id=valid_job_id,
            correlation_id=valid_correlation_id,
            step_name="TEST_STEP",
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            payload={"created_at": "2026-01-01T00:00:00Z"},
        )

        with pytest.raises(ValidationError) as exc_info:
            serializer.serialize_payload(payload)

        assert "created_at" in str(exc_info.value)
        assert "reserved fields" in str(exc_info.value).lower()

    def test_serialize_payload_reserved_field_conflict_multiple(
        self, serializer, valid_correlation_id, valid_job_id
    ):
        """Test that payload cannot override multiple reserved fields."""
        from faaspectre.domain.exceptions import ValidationError

        payload = ExecutionPayload(
            doc_id=valid_job_id,
            correlation_id=valid_correlation_id,
            step_name="TEST_STEP",
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            payload={
                "doc_id": "override1",
                "step_name": "override2",
                "created_at": "override3",
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            serializer.serialize_payload(payload)

        error_msg = str(exc_info.value).lower()
        assert "reserved fields" in error_msg
        assert "doc_id" in str(exc_info.value) or "doc_id" in error_msg
        assert "step_name" in str(exc_info.value) or "step_name" in error_msg
        assert "created_at" in str(exc_info.value) or "created_at" in error_msg

    def test_serialize_payload_empty_payload(self, serializer, valid_correlation_id, valid_job_id):
        """Test serialization with empty payload."""
        payload = ExecutionPayload(
            doc_id=valid_job_id,
            correlation_id=valid_correlation_id,
            step_name="TEST_STEP",
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            payload={},
        )

        result = serializer.serialize_payload(payload)
        
        # Only reserved fields should be present
        assert result["doc_id"] == valid_job_id
        assert result["correlation_id"] == valid_correlation_id
        assert result["step_name"] == "TEST_STEP"
        assert "created_at" in result
        assert len(result) == 4  # Only 4 reserved fields

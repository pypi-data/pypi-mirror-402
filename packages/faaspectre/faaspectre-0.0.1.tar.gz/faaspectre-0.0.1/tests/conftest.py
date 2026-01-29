"""Pytest configuration and fixtures."""

import pytest
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from faaspectre.domain.models import ExecutionContext, ExecutionMetrics, ExecutionPayload
from faaspectre.domain.status import PipelineStatus


@pytest.fixture
def valid_correlation_id() -> str:
    """Generate a valid UUID-v4 correlation ID."""
    return str(uuid.uuid4())


@pytest.fixture
def valid_job_id() -> str:
    """Generate a valid job ID."""
    return f"job-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def valid_execution_context(valid_correlation_id: str, valid_job_id: str) -> ExecutionContext:
    """Create a valid ExecutionContext."""
    return ExecutionContext(
        correlation_id=valid_correlation_id,
        job_id=valid_job_id,
        step_name="TEST_STEP",
        triggered_by="ETL_WORKFLOW",
        prev_job_id=None,
    )


@pytest.fixture
def valid_workflow_payload(valid_correlation_id: str, valid_job_id: str) -> Dict[str, Any]:
    """Create a valid workflow payload dictionary."""
    return {
        "correlation_id": valid_correlation_id,
        "job_id": valid_job_id,
        "step_name": "TEST_STEP",
        "triggered_by": "ETL_WORKFLOW",
        "prev_job_id": None,
    }


@pytest.fixture
def valid_execution_metrics(valid_correlation_id: str, valid_job_id: str) -> ExecutionMetrics:
    """Create valid ExecutionMetrics."""
    return ExecutionMetrics(
        doc_id=valid_job_id,
        correlation_id=valid_correlation_id,
        job_id=valid_job_id,
        step_name="TEST_STEP",
        triggered_by="ETL_WORKFLOW",
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        start_time_epoch=1000.0,
        end_time_epoch=2000.0,
        duration_ms=1000.0,
        memory_mb=128.0,
        status=PipelineStatus.SUCCESS.value,
        error_summary=None,
    )


@pytest.fixture
def valid_execution_payload(valid_correlation_id: str, valid_job_id: str) -> ExecutionPayload:
    """Create valid ExecutionPayload."""
    return ExecutionPayload(
        doc_id=valid_job_id,
        correlation_id=valid_correlation_id,
        step_name="TEST_STEP",
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        payload={"result": "success", "count": 100},
    )

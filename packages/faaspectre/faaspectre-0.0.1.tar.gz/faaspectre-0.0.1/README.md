# Telemetric Reporter - FaaS Job Execution Metrics Library

A Python library for Google Cloud Functions that provides automatic instrumentation, exception handling, and atomic persistence of execution metrics and payloads to Firestore.

## Features

- **Auto-Instrumentation**: Automatic timing and memory tracking
- **Exception Handling**: Comprehensive error handling with correlation context
- **Atomic Persistence**: Batch writes to `pipeline_logs` and `pipeline_data` Firestore collections
- **Data Sanitization**: Automatic conversion of dates to ISO 8601 UTC and metrics to floats
- **Hexagonal Architecture**: Swappable storage backends via ports and adapters
- **Correlation Tracking**: Distributed tracing via `correlation_id` and `job_id`

## Installation

```bash
pip install faaspectre
```

## Quick Start

```python
from faaspectre import create_job_execution_reporter, ExecutionContext

# Create context from workflow payload
context = ExecutionContext.from_workflow_payload(workflow_payload)

# Use factory function with defaults
with create_job_execution_reporter(context, "ANALYZE_SENTIMENT") as reporter:
    # Your business logic here
    result = my_worker_function(**kwargs)
    
    # Save execution payload (optional)
    reporter.save_execution_payload(result)
```

## Configuration

### Environment Variables

The library uses environment variables for configuration:

- `TELEMETRIC_STORAGE_BACKEND`: Storage backend (`firestore` | `bigquery` | `postgres`). Default: `firestore`
- `PIPELINE_LOGS_COLLECTION`: Firestore collection name for metrics. Default: `pipeline_logs`
- `PIPELINE_DATA_COLLECTION`: Firestore collection name for payloads. Default: `pipeline_data`
- `GC_PROJECT_ID`: Google Cloud project ID (required for Firestore)

### Custom Configuration

```python
from faaspectre import TelemetricConfig, create_job_execution_reporter

# Create custom config
config = TelemetricConfig(
    storage_backend="firestore",
    pipeline_logs_collection="my_logs",
    pipeline_data_collection="my_data",
    project_id="my-project-id"
)

# Use with factory function
with create_job_execution_reporter(context, "STEP_NAME", config=config) as reporter:
    # Your code here
    pass
```

## Architecture

The library follows **Hexagonal Architecture (Ports & Adapters)** pattern:

- **Domain Layer**: Business models and rules (`ExecutionContext`, `ExecutionMetrics`, `ExecutionPayload`)
- **Application Layer**: Use cases and ports (interfaces)
- **Infrastructure Layer**: Adapters (Firestore, Psutil implementations)

This design allows easy swapping of storage backends without changing application code.

## Usage Examples

### Basic Usage

```python
from faaspectre import create_job_execution_reporter, ExecutionContext

def my_worker_function(context: ExecutionContext, **kwargs):
    """Your business logic here."""
    # Process data
    result = {"processed": True, "count": 100}
    return result

# In your Cloud Function
def cloud_function_handler(request):
    context = ExecutionContext.from_workflow_payload(request.json)
    
    with create_job_execution_reporter(context, "PROCESS_DATA") as reporter:
        result = my_worker_function(context, **request.json)
        reporter.save_execution_payload(result)
    
    return result
```

### Custom Storage and Instrumentation

```python
from faaspectre import (
    create_job_execution_reporter,
    FirestoreMetricStorage,
    PsutilInstrumentation,
    TelemetricConfig
)

config = TelemetricConfig.from_env()
storage = FirestoreMetricStorage(config)
instrumentation = PsutilInstrumentation()

with create_job_execution_reporter(
    context, 
    "STEP_NAME",
    storage=storage,
    instrumentation=instrumentation
) as reporter:
    # Your code here
    pass
```

### Error Handling

The library automatically handles exceptions and saves them with `FAILED` status:

```python
with create_job_execution_reporter(context, "STEP_NAME") as reporter:
    try:
        # Your code that might raise exceptions
        result = risky_operation()
        reporter.save_execution_payload(result)
    except Exception:
        # Exception is automatically logged and saved with FAILED status
        # Exception is re-raised for orchestrator retry
        raise
```

## Data Models

### ExecutionContext

Context from workflow payload:

```python
@dataclass
class ExecutionContext:
    correlation_id: str  # UUID-v4, Global Trace ID
    job_id: str  # Unique ID for this execution
    step_name: str  # Human-readable stage name
    triggered_by: str  # Source: "ETL_WORKFLOW" | "USER:email"
    prev_job_id: Optional[str]  # Parent job_id if not start of chain
```

### ExecutionMetrics

Metrics saved to `pipeline_logs` collection:

```python
@dataclass
class ExecutionMetrics:
    doc_id: str  # Matches Firestore Document ID
    correlation_id: str  # UUID-v4
    job_id: str
    step_name: str
    triggered_by: str
    created_at: str  # ISO 8601 UTC
    start_time_epoch: float
    status: str  # "PENDING" | "SUCCESS" | "FAILED"
    end_time_epoch: Optional[float]
    duration_ms: Optional[float]
    memory_mb: Optional[float]
    error_summary: Optional[str]
```

### ExecutionPayload

Payload saved to `pipeline_data` collection:

```python
@dataclass
class ExecutionPayload:
    doc_id: str  # Matches Log ID
    correlation_id: str  # UUID-v4
    payload: Dict[str, Any]  # Flexible structure
```

## Firestore Collections

### pipeline_logs

Operational metrics for dashboard insights:

- Document ID: `job_id`
- Fields: `correlation_id`, `job_id`, `step_name`, `status`, `start_time_epoch`, `end_time_epoch`, `duration_ms`, `memory_mb`, `error_summary`, etc.

### pipeline_data

Business data for detailed audit trails:

- Document ID: `job_id` (matches `pipeline_logs` doc_id)
- Fields: `correlation_id`, `payload` (flexible structure)

## Error Handling Strategy

The library follows a **log-and-re-raise** pattern:

1. **Business Logic Errors**: Logged → Saved with `FAILED` status → Re-raised for orchestrator retry
2. **Validation Errors**: Logged → Re-raised (programming error, fix code)
3. **Storage Errors**: Logged → Re-raised (orchestrator handles retries)
4. **Instrumentation Errors**: Logged as warnings → Continue without instrumentation (graceful degradation)

**No retry logic in the library** - The orchestrator (Google Cloud Workflows) handles retries.

## Exception Hierarchy

```python
TelemetricError (base)
├── ConfigurationError
├── ValidationError
├── StorageError
│   └── AtomicWriteError
└── InstrumentationError
```

All exceptions include `correlation_id` and `job_id` for distributed tracing.

## Thread Safety

The library assumes **single-threaded FaaS execution** (Google Cloud Functions). Each `JobExecutionReporter` instance tracks its own metrics. See [Thread Safety Documentation](docs/THREAD_SAFETY.md) for details.

## Testing

### Setup

Install development dependencies:

```bash
pip install -r requirements-dev.txt
pip install -e .[faasjob]
```

Or use Make:

```bash
make install-dev
```

### Running Tests

Run all tests:

```bash
pytest tests/
```

Or use Make:

```bash
make test
```

Run tests with coverage:

```bash
make test-coverage
```

### Test Structure

Tests are organized to mirror the source code structure:

- `tests/faasjob/domain/` - Domain model tests
- `tests/faasjob/application/` - Application layer tests
- `tests/faasjob/infrastructure/` - Infrastructure adapter tests
- `tests/faasjob/utils/` - Utility function tests

See [TEST_CASES.md](tests/TEST_CASES.md) for comprehensive test scenarios.

## Development

### Make Commands

```bash
make help          # Show all available commands
make install       # Install package with faasjob dependencies
make install-dev   # Install all development dependencies
make test          # Run tests
make test-coverage # Run tests with coverage report
make lint          # Run linters (pylint, mypy)
make format        # Format code with black
make verify        # Run all verification checks (tests + linting)
make clean         # Clean build artifacts
```

### Dependencies

Production dependencies (installed with `pip install .[faasjob]`):

- `google-cloud-firestore==2.4.0`: Firestore client
- `psutil>=5.8.0`: Memory tracking
- `marshmallow-dataclass==8.3.2`: Data validation

Development dependencies (see `requirements-dev.txt`):

- `pytest>=7.0.0`: Testing framework
- `pytest-cov>=4.0.0`: Coverage reporting
- `pytest-mock>=3.10.0`: Mocking support
- `pylint>=2.15.0`: Code quality
- `black>=22.0.0`: Code formatting
- `mypy>=1.0.0`: Type checking

## Migration from FaasJobManager

If migrating from the old `FaasJobManager`:

1. Replace `FaasJobManager` with `create_job_execution_reporter()`
2. Replace `TaskContext` with `ExecutionContext`
3. Use `save_execution_payload()` instead of `save_business_data()`
4. Update collection names if different from defaults


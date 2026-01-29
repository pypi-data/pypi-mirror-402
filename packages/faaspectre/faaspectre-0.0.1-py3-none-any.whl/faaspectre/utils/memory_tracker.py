"""Memory tracking decorator for function-level memory sampling."""

from functools import wraps
from typing import Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..application.use_case.job_execution_reporter import JobExecutionReporter


def track_memory(reporter: "JobExecutionReporter"):
    """Decorator to track memory usage of a function.

    Samples memory before and after function execution to capture peak usage
    during the function's execution.

    Args:
        reporter: JobExecutionReporter instance to use for sampling

    Returns:
        Decorator function

    Example:
        >>> with create_job_execution_reporter(context, "PROCESS_DATA") as reporter:
        >>>     @track_memory(reporter)
        >>>     def load_and_process():
        >>>         data = load_large_dataset()
        >>>         return process_data(data)
        >>>
        >>>     result = load_and_process()  # Memory automatically sampled
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Sample before function execution
            reporter.sample_memory()
            try:
                result = func(*args, **kwargs)
                # Sample after function execution
                reporter.sample_memory()
                return result
            except Exception:
                # Sample even on error to capture peak during failure
                reporter.sample_memory()
                raise
        return wrapper
    return decorator

"""Instrumentation port for system metrics tracking."""

from abc import ABC, abstractmethod
from typing import Optional


class TimingTracker:
    """Stateful tracker object for timing operations.

    Tracks start and end times for execution duration calculation.
    """

    def __init__(self):
        """Initialize TimingTracker."""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start(self) -> None:
        """Start timing."""
        import time

        self.start_time = time.time()

    def stop(self) -> float:
        """Stop timing and return end time epoch.

        Returns:
            End time as epoch timestamp

        Raises:
            ValueError: If start() was not called first
        """
        import time

        if self.start_time is None:
            raise ValueError("TimingTracker.start() must be called before stop()")
        self.end_time = time.time()
        return self.end_time

    def duration_ms(self) -> float:
        """Calculate duration in milliseconds.

        Returns:
            Duration in milliseconds

        Raises:
            ValueError: If start() or stop() was not called
        """
        if self.start_time is None or self.end_time is None:
            raise ValueError("TimingTracker.start() and stop() must be called before duration_ms()")
        return (self.end_time - self.start_time) * 1000.0


class InstrumentationPort(ABC):
    """Abstract base class for system instrumentation.

    Defines contract for memory and timing tracking.
    """

    @abstractmethod
    def get_current_memory_mb(self) -> float:
        """Get current memory usage in megabytes.

        Returns:
            Current memory usage in MB

        Raises:
            InstrumentationError: If memory tracking fails
        """
        pass

    @abstractmethod
    def get_peak_memory_mb(self) -> float:
        """Get peak memory usage in megabytes during execution.

        Returns:
            Peak memory usage in MB

        Raises:
            InstrumentationError: If memory tracking fails
        """
        pass

    @abstractmethod
    def create_timing_tracker(self) -> TimingTracker:
        """Create a new timing tracker instance.

        Returns:
            TimingTracker instance
        """
        pass

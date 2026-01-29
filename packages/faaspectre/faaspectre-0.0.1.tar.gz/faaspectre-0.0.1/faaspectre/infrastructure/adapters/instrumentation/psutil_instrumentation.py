"""Psutil-based instrumentation adapter."""

import psutil
import os

from ....application.ports.instrumentation import InstrumentationPort, TimingTracker
from ....domain.exceptions import InstrumentationError


class PsutilInstrumentation(InstrumentationPort):
    """Psutil-based implementation of InstrumentationPort.

    Uses psutil library for memory tracking and time module for timing.
    """

    def __init__(self):
        """Initialize PsutilInstrumentation."""
        try:
            # Verify psutil is available
            self._process = psutil.Process(os.getpid())
            self._initial_memory = None
            self._peak_memory = None
        except Exception as e:
            raise InstrumentationError(f"Failed to initialize psutil: {e}") from e

    def get_current_memory_mb(self) -> float:
        """Get current memory usage in megabytes.

        Returns:
            Current memory usage in MB

        Raises:
            InstrumentationError: If memory tracking fails
        """
        try:
            memory_info = self._process.memory_info()
            return memory_info.rss / (1024 * 1024)  # Convert bytes to MB
        except Exception as e:
            raise InstrumentationError(f"Failed to get current memory: {e}") from e

    def get_peak_memory_mb(self) -> float:
        """Get peak memory usage in megabytes during execution.

        Returns:
            Peak memory usage in MB

        Raises:
            InstrumentationError: If memory tracking fails
        """
        try:
            if self._peak_memory is None:
                # Initialize peak memory to current if not set
                self._peak_memory = self.get_current_memory_mb()
            else:
                # Update peak if current is higher
                current = self.get_current_memory_mb()
                if current > self._peak_memory:
                    self._peak_memory = current
            return self._peak_memory
        except Exception as e:
            raise InstrumentationError(f"Failed to get peak memory: {e}") from e

    def create_timing_tracker(self) -> TimingTracker:
        """Create a new timing tracker instance.

        Returns:
            TimingTracker instance
        """
        return TimingTracker()

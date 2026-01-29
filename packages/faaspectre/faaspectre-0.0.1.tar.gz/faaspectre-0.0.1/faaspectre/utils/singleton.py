"""Singleton metaclass for Telemetric Reporter."""


class Singleton(type):
    """Singleton metaclass pattern."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Create or return existing instance."""
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

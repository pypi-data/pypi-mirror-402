"""Configuration management for Telemetric Reporter."""

import os
from typing import Optional
from dataclasses import dataclass

from ..domain.exceptions import ConfigurationError


@dataclass
class TelemetricConfig:
    """Configuration for Telemetric Reporter.

    Supports storage backend selection and collection configuration.
    """

    storage_backend: str = "firestore"
    pipeline_logs_collection: str = "pipeline_logs"
    pipeline_data_collection: str = "pipeline_data"
    project_id: Optional[str] = None
    # Future: BigQuery/Postgres specific config fields
    # bigquery_dataset: Optional[str] = None
    # bigquery_table_metrics: Optional[str] = None

    @classmethod
    def from_env(cls) -> "TelemetricConfig":
        """Load configuration from environment variables.

        Returns:
            TelemetricConfig instance

        Environment Variables:
            TELEMETRIC_STORAGE_BACKEND: Storage backend ("firestore" | "bigquery" | "postgres")
            PIPELINE_LOGS_COLLECTION: Collection name for pipeline_logs (default: "pipeline_logs")
            PIPELINE_DATA_COLLECTION: Collection name for pipeline_data (default: "pipeline_data")
            GC_PROJECT_ID: Google Cloud project ID
        """
        return cls(
            storage_backend=os.getenv("TELEMETRIC_STORAGE_BACKEND", "firestore"),
            pipeline_logs_collection=os.getenv("PIPELINE_LOGS_COLLECTION", "pipeline_logs"),
            pipeline_data_collection=os.getenv("PIPELINE_DATA_COLLECTION", "pipeline_data"),
            project_id=os.getenv("GC_PROJECT_ID"),
        )

    @classmethod
    def from_file(cls, config_path: str) -> "TelemetricConfig":
        """Load configuration from YAML/JSON file.

        Args:
            config_path: Path to configuration file

        Returns:
            TelemetricConfig instance

        Raises:
            ConfigurationError: If file cannot be read or parsed
        """
        # TODO: Implement YAML/JSON file loading
        # For now, raise not implemented
        raise ConfigurationError("Config file loading not yet implemented")

    def validate(self) -> None:
        """Validate configuration.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        valid_backends = ["firestore", "bigquery", "postgres"]
        if self.storage_backend not in valid_backends:
            raise ConfigurationError(
                f"Invalid storage_backend: {self.storage_backend}. Must be one of {valid_backends}"
            )

        if not self.pipeline_logs_collection:
            raise ConfigurationError("pipeline_logs_collection cannot be empty")

        if not self.pipeline_data_collection:
            raise ConfigurationError("pipeline_data_collection cannot be empty")

        if self.storage_backend == "firestore" and not self.project_id:
            raise ConfigurationError("project_id is required for Firestore storage backend")

"""Tests for application configuration."""

import pytest
import os
from unittest.mock import patch

from faaspectre.application.config import TelemetricConfig
from faaspectre.domain.exceptions import ConfigurationError


class TestTelemetricConfig:
    """Tests for TelemetricConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = TelemetricConfig()
        assert config.storage_backend == "firestore"
        assert config.pipeline_logs_collection == "pipeline_logs"
        assert config.pipeline_data_collection == "pipeline_data"
        assert config.project_id is None

    @patch.dict(
        os.environ,
        {
            "TELEMETRIC_STORAGE_BACKEND": "firestore",
            "PIPELINE_LOGS_COLLECTION": "my_logs",
            "PIPELINE_DATA_COLLECTION": "my_data",
            "GC_PROJECT_ID": "test-project",
        },
    )
    def test_from_env(self):
        """Test loading configuration from environment variables."""
        config = TelemetricConfig.from_env()
        assert config.storage_backend == "firestore"
        assert config.pipeline_logs_collection == "my_logs"
        assert config.pipeline_data_collection == "my_data"
        assert config.project_id == "test-project"

    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        config = TelemetricConfig(
            storage_backend="firestore",
            pipeline_logs_collection="logs",
            pipeline_data_collection="data",
            project_id="test-project",
        )
        # Should not raise
        config.validate()

    def test_validate_invalid_backend(self):
        """Test validation fails for invalid storage backend."""
        config = TelemetricConfig(storage_backend="invalid_backend")
        with pytest.raises(ConfigurationError, match="Invalid storage_backend"):
            config.validate()

    def test_validate_empty_collection_names(self):
        """Test validation fails for empty collection names."""
        config = TelemetricConfig(pipeline_logs_collection="")
        with pytest.raises(ConfigurationError, match="cannot be empty"):
            config.validate()

        config = TelemetricConfig(pipeline_data_collection="")
        with pytest.raises(ConfigurationError, match="cannot be empty"):
            config.validate()

    def test_validate_firestore_missing_project_id(self):
        """Test validation fails for Firestore without project_id."""
        config = TelemetricConfig(
            storage_backend="firestore",
            project_id=None,
        )
        with pytest.raises(ConfigurationError, match="project_id is required"):
            config.validate()

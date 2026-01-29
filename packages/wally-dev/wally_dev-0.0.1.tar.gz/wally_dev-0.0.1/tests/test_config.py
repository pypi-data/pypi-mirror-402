"""Tests for configuration module."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from wally_dev.config import LocalConfig, Settings


class TestSettings:
    """Tests for Settings class."""

    def test_default_values(self):
        """Test default settings values."""
        settings = Settings()
        assert settings.timeout == 30
        assert settings.max_retries == 3
        assert settings.workspace_dir == "workspace"

    def test_env_override(self):
        """Test environment variable override."""
        with patch.dict("os.environ", {"WALLY_DEV_TIMEOUT": "60"}):
            settings = Settings()
            assert settings.timeout == 60


class TestLocalConfig:
    """Tests for LocalConfig class."""

    @pytest.fixture
    def temp_config(self, tmp_path: Path) -> LocalConfig:
        """Create a LocalConfig with temporary file."""
        config_file = tmp_path / ".wally-dev.json"
        config = LocalConfig.__new__(LocalConfig)
        config.config_file = config_file
        config._data = {}
        return config

    def test_access_token_storage(self, temp_config: LocalConfig):
        """Test storing and retrieving access token."""
        temp_config.access_token = "test-token-123"

        # Load from file
        with open(temp_config.config_file) as f:
            data = json.load(f)
        assert data["access_token"] == "test-token-123"

    def test_is_logged_in(self, temp_config: LocalConfig):
        """Test login status check."""
        assert not temp_config.is_logged_in

        temp_config._data["access_token"] = "test-token"
        assert temp_config.is_logged_in

    def test_locked_norms_management(self, temp_config: LocalConfig):
        """Test locked norms tracking."""
        # Add locked norm
        temp_config.add_locked_norm("norm123", {"name": "Test Norm"})
        assert temp_config.is_norm_locked_locally("norm123")
        assert not temp_config.is_norm_locked_locally("norm456")

        # Remove locked norm
        temp_config.remove_locked_norm("norm123")
        assert not temp_config.is_norm_locked_locally("norm123")

    def test_clear_config(self, temp_config: LocalConfig):
        """Test clearing configuration."""
        temp_config.config_file.write_text('{"access_token": "test"}')
        temp_config._data = {"access_token": "test"}

        temp_config.clear()

        assert temp_config._data == {}
        assert not temp_config.config_file.exists()

    def test_refresh_token_storage(self, temp_config: LocalConfig):
        """Test storing and retrieving refresh token."""
        temp_config.refresh_token = "refresh-token-123"

        with open(temp_config.config_file) as f:
            data = json.load(f)
        assert data["refresh_token"] == "refresh-token-123"

    def test_user_id_storage(self, temp_config: LocalConfig):
        """Test storing and retrieving user ID."""
        temp_config.user_id = "user-123"

        with open(temp_config.config_file) as f:
            data = json.load(f)
        assert data["user_id"] == "user-123"

    def test_org_id_storage(self, temp_config: LocalConfig):
        """Test storing and retrieving org ID."""
        temp_config.organization_id = "org-123"

        with open(temp_config.config_file) as f:
            data = json.load(f)
        assert data["organization_id"] == "org-123"

    def test_get_locked_norms(self, temp_config: LocalConfig):
        """Test getting all locked norms."""
        temp_config.add_locked_norm("norm1", {"name": "Norm 1"})
        temp_config.add_locked_norm("norm2", {"name": "Norm 2"})

        norms = temp_config.get_locked_norms()

        assert "norm1" in norms
        assert "norm2" in norms
        assert norms["norm1"]["name"] == "Norm 1"

    def test_set_credentials_via_properties(self, temp_config: LocalConfig):
        """Test saving credentials via properties."""
        temp_config.access_token = "access-123"
        temp_config.refresh_token = "refresh-123"
        temp_config.user_id = "user-123"
        temp_config.organization_id = "org-123"

        assert temp_config.access_token == "access-123"
        assert temp_config.refresh_token == "refresh-123"
        assert temp_config.user_id == "user-123"
        assert temp_config.organization_id == "org-123"

    def test_clear_removes_credentials(self, temp_config: LocalConfig):
        """Test clearing credentials."""
        temp_config._data = {
            "access_token": "test",
            "refresh_token": "test",
            "user_id": "test",
            "organization_id": "test",
            "locked_norms": {"norm1": {}},
        }
        temp_config.config_file.parent.mkdir(parents=True, exist_ok=True)
        temp_config.config_file.write_text("{}")

        temp_config.clear()

        assert temp_config._data == {}
        assert temp_config.access_token is None

    def test_load_existing_config(self, tmp_path: Path):
        """Test loading existing config file."""
        config_file = tmp_path / ".wally-dev.json"
        config_file.write_text(
            json.dumps(
                {
                    "access_token": "existing-token",
                    "user_id": "existing-user",
                }
            )
        )

        config = LocalConfig.__new__(LocalConfig)
        config.config_file = config_file
        config._data = None
        config._load()

        assert config._data["access_token"] == "existing-token"
        assert config._data["user_id"] == "existing-user"

    def test_is_norm_locked_locally_empty(self, temp_config: LocalConfig):
        """Test checking lock for non-existent norm."""
        assert not temp_config.is_norm_locked_locally("nonexistent")

    def test_add_locked_norm_with_metadata(self, temp_config: LocalConfig):
        """Test adding locked norm with metadata."""
        from datetime import datetime

        temp_config.add_locked_norm(
            "norm123",
            {
                "norm_name": "Test Norm",
                "checkout_at": datetime.now().isoformat(),
                "version": "1.0",
            },
        )

        norms = temp_config.get_locked_norms()
        assert norms["norm123"]["norm_name"] == "Test Norm"
        assert "checkout_at" in norms["norm123"]

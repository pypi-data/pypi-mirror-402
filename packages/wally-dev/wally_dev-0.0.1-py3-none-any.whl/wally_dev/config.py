"""
Configuration module for Wally Dev CLI.

Handles local configuration storage and retrieval.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

from pydantic import Field
from pydantic_settings import BaseSettings

from .constants import (
    CONFIG_FILE_NAME,
    DEFAULT_BACKEND_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    WORKSPACE_DIR_NAME,
)


def get_config_dir() -> Path:
    """Get the configuration directory for wally-dev."""
    # Use XDG_CONFIG_HOME if available, otherwise use ~/.config
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        config_dir = Path(xdg_config) / "wally-dev"
    else:
        config_dir = Path.home() / ".config" / "wally-dev"

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_file() -> Path:
    """Get the path to the configuration file."""
    return get_config_dir() / CONFIG_FILE_NAME


class Settings(BaseSettings):
    """Application settings with environment variable support and validation."""

    # Server Configuration
    backend_url: str = Field(
        default=DEFAULT_BACKEND_URL,
        alias="WALLY_DEV_BACKEND_URL",
        description="Backend server URL",
    )

    # Authentication (loaded from config file, not env)
    access_token: Optional[str] = Field(
        default=None,
        alias="WALLY_DEV_ACCESS_TOKEN",
        description="JWT access token for authentication",
    )

    # HTTP Configuration
    timeout: int = Field(
        default=DEFAULT_TIMEOUT,
        ge=1,
        le=300,
        alias="WALLY_DEV_TIMEOUT",
        description="HTTP request timeout in seconds",
    )
    max_retries: int = Field(
        default=DEFAULT_MAX_RETRIES,
        ge=0,
        le=10,
        description="Maximum number of retry attempts",
    )

    # Workspace Configuration
    workspace_dir: str = Field(
        default=WORKSPACE_DIR_NAME,
        alias="WALLY_DEV_WORKSPACE_DIR",
        description="Directory for storing downloaded test cases",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "populate_by_name": True,
    }


class LocalConfig:
    """
    Manages local configuration storage.

    Stores API key and other persistent settings in a JSON file
    in the user's config directory.
    """

    def __init__(self) -> None:
        self.config_file = get_config_file()
        self._data: dict = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        """Save configuration to file."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    @property
    def access_token(self) -> Optional[str]:
        """Get stored access token."""
        return self._data.get("access_token")

    @access_token.setter
    def access_token(self, value: Optional[str]) -> None:
        """Set access token."""
        if value:
            self._data["access_token"] = value
        elif "access_token" in self._data:
            del self._data["access_token"]
        self._save()

    @property
    def refresh_token(self) -> Optional[str]:
        """Get stored refresh token."""
        return self._data.get("refresh_token")

    @refresh_token.setter
    def refresh_token(self, value: Optional[str]) -> None:
        """Set refresh token."""
        if value:
            self._data["refresh_token"] = value
        elif "refresh_token" in self._data:
            del self._data["refresh_token"]
        self._save()

    @property
    def user_email(self) -> Optional[str]:
        """Get stored user email."""
        return self._data.get("user_email")

    @user_email.setter
    def user_email(self, value: Optional[str]) -> None:
        """Set user email."""
        if value:
            self._data["user_email"] = value
        elif "user_email" in self._data:
            del self._data["user_email"]
        self._save()

    @property
    def user_id(self) -> Optional[str]:
        """Get stored user ID."""
        return self._data.get("user_id")

    @user_id.setter
    def user_id(self, value: Optional[str]) -> None:
        """Set user ID."""
        if value:
            self._data["user_id"] = value
        elif "user_id" in self._data:
            del self._data["user_id"]
        self._save()

    @property
    def organization_id(self) -> Optional[str]:
        """Get stored organization ID."""
        return self._data.get("organization_id")

    @organization_id.setter
    def organization_id(self, value: Optional[str]) -> None:
        """Set organization ID."""
        if value:
            self._data["organization_id"] = value
        elif "organization_id" in self._data:
            del self._data["organization_id"]
        self._save()

    @property
    def backend_url(self) -> Optional[str]:
        """Get stored backend URL."""
        return self._data.get("backend_url")

    @backend_url.setter
    def backend_url(self, value: Optional[str]) -> None:
        """Set backend URL."""
        if value:
            self._data["backend_url"] = value
        elif "backend_url" in self._data:
            del self._data["backend_url"]
        self._save()

    @property
    def is_logged_in(self) -> bool:
        """Check if user is logged in (has access token)."""
        return bool(self.access_token)

    def update_tokens(self, access_token: str, refresh_token: str) -> None:
        """
        Update access and refresh tokens.

        Used as callback when tokens are refreshed automatically.
        """
        self._data["access_token"] = access_token
        self._data["refresh_token"] = refresh_token
        self._save()

    def create_api_client(self, settings: Optional["Settings"] = None) -> Any:
        """
        Create an API client with current credentials and auto-refresh support.

        Args:
            settings: Optional Settings instance (will create one if not provided)

        Returns:
            WallyDevApiClient configured with tokens and refresh callback
        """
        from .api_client import WallyDevApiClient

        if settings is None:
            settings = Settings()

        backend_url = self.backend_url or settings.backend_url

        return WallyDevApiClient(
            base_url=backend_url,
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            organization_id=self.organization_id,
            on_token_refresh=self.update_tokens,
        )

    def clear(self) -> None:
        """Clear all stored configuration."""
        self._data = {}
        if self.config_file.exists():
            self.config_file.unlink()

    def get_locked_norms(self) -> dict[str, Any]:
        """Get dictionary of locked norms with their checkout info."""
        result: dict[str, Any] = self._data.get("locked_norms", {})
        return result

    def add_locked_norm(self, norm_id: str, info: dict) -> None:
        """Add a locked norm to the local tracking."""
        if "locked_norms" not in self._data:
            self._data["locked_norms"] = {}
        self._data["locked_norms"][norm_id] = info
        self._save()

    def remove_locked_norm(self, norm_id: str) -> None:
        """Remove a locked norm from local tracking."""
        if "locked_norms" in self._data and norm_id in self._data["locked_norms"]:
            del self._data["locked_norms"][norm_id]
            self._save()

    def is_norm_locked_locally(self, norm_id: str) -> bool:
        """Check if a norm is locked locally."""
        return norm_id in self.get_locked_norms()

"""
Auth configuration for VibeKit SDK.

Defines endpoints, OAuth settings, and storage locations for authentication.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel


def _is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return os.environ.get("VK_DEBUG", "").lower() in ("1", "true", "yes")


def _get_default_api_url() -> str:
    """Get API URL: localhost:8088/api in debug, api.vkcli.com/api in production."""
    if _is_debug_mode():
        return "http://localhost:8088/api"
    return "https://api.vkcli.com/api"


def _get_default_auth_url() -> str:
    """Get auth URL: localhost:5173 in debug, vkcli.com in production."""
    if _is_debug_mode():
        return "http://localhost:5173/auth"
    return "https://vkcli.com/auth"


def _get_default_token_url() -> str:
    """Get token URL: localhost:8088/api in debug, api.vkcli.com/api in production."""
    if _is_debug_mode():
        return "http://localhost:8088/api/oauth/token"
    return "https://api.vkcli.com/api/oauth/token"


class AuthConfig(BaseModel):
    """Configuration for VibeKit authentication."""

    # SaaS Platform URLs
    # Production: api.vkcli.com (default)
    # Debug: localhost:8088 (set VK_DEBUG=1)
    api_base_url: str = _get_default_api_url()
    auth_url: str = _get_default_auth_url()
    token_url: str = _get_default_token_url()

    # OAuth settings
    client_id: str = "vksdk-cli"
    redirect_uri: str = "http://localhost:8765/callback"
    scopes: list[str] = ["read", "write", "project:manage"]

    # Local storage
    config_dir: Path = Path.home() / ".vk"
    token_file: str = "auth.json"

    # Token settings
    token_refresh_buffer_seconds: int = 300  # Refresh 5 min before expiry

    @property
    def token_path(self) -> Path:
        """Full path to token storage file."""
        return self.config_dir / self.token_file

    def ensure_config_dir(self) -> None:
        """Create config directory if it doesn't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    class Config:
        """Pydantic config."""

        frozen = False


# Default configuration
DEFAULT_CONFIG = AuthConfig()


def get_config(config_dir: Path | None = None, api_url: str | None = None) -> AuthConfig:
    """
    Get auth configuration.

    Uses VK_DEBUG env var or api_url to switch between production and localhost.

    Args:
        config_dir: Override the config directory
        api_url: Override API URL (also derives auth URLs from it for localhost)

    Returns:
        AuthConfig instance

    Examples:
        # Production (default)
        config = get_config()  # → api.vkcli.com

        # Debug mode
        # export VK_DEBUG=1
        config = get_config()  # → localhost:8088

        # Override with project api_url
        config = get_config(api_url="http://localhost:8088")  # → localhost
    """
    config = AuthConfig()

    if config_dir:
        config.config_dir = config_dir

    # If api_url provided and it's localhost, derive auth URLs from it
    if api_url:
        parsed = urlparse(api_url)
        is_local = parsed.hostname in ("localhost", "127.0.0.1")

        if is_local:
            # Derive URLs from the provided api_url
            base = api_url.rstrip("/")
            # Remove /api suffix if present for consistency
            if base.endswith("/api"):
                base = base[:-4]

            config.api_base_url = f"{base}/api"
            config.token_url = f"{base}/api/oauth/token"
            # Assume frontend is on port 5173 for local dev
            config.auth_url = f"{parsed.scheme}://{parsed.hostname}:5173/auth"

    return config

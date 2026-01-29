"""
Token management for VibeKit SDK.

Handles storage, retrieval, and refresh of JWT tokens using the system keyring
for secure credential storage.
"""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import keyring

    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


@dataclass
class TokenData:
    """JWT token data structure."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: Optional[float] = None  # Unix timestamp
    user_id: Optional[str] = None
    email: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if self.expires_at is None:
            return False
        return time.time() >= self.expires_at

    def expires_soon(self, buffer_seconds: int = 300) -> bool:
        """Check if token expires within buffer time."""
        if self.expires_at is None:
            return False
        return time.time() >= (self.expires_at - buffer_seconds)

    @property
    def authorization_header(self) -> str:
        """Get Authorization header value."""
        return f"{self.token_type} {self.access_token}"

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_at": self.expires_at,
            "user_id": self.user_id,
            "email": self.email,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TokenData":
        """Create from dictionary."""
        # Normalize token_type to "Bearer" (API may return lowercase "bearer")
        token_type = data.get("token_type", "Bearer")
        if token_type.lower() == "bearer":
            token_type = "Bearer"
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=token_type,
            expires_at=data.get("expires_at"),
            user_id=data.get("user_id"),
            email=data.get("email"),
        )


class TokenManager:
    """
    Manages JWT token storage and retrieval.

    Uses system keyring for secure storage when available,
    falls back to encrypted file storage.
    """

    SERVICE_NAME = "vksdk"
    USERNAME = "default"

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize token manager.

        Args:
            config_dir: Directory for fallback file storage
        """
        self.config_dir = config_dir or Path.home() / ".vk"
        self.token_file = self.config_dir / "auth.json"

    def save_token(self, token: TokenData) -> None:
        """
        Save token to secure storage.

        Args:
            token: Token data to save
        """
        token_json = json.dumps(token.to_dict())

        if KEYRING_AVAILABLE:
            try:
                keyring.set_password(self.SERVICE_NAME, self.USERNAME, token_json)
                return
            except Exception:
                pass  # Fall back to file storage

        # File-based fallback
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.token_file.write_text(token_json)
        # Set restrictive permissions
        self.token_file.chmod(0o600)

    def get_token(self) -> Optional[TokenData]:
        """
        Retrieve stored token.

        Returns:
            TokenData if found, None otherwise
        """
        token_json = None

        if KEYRING_AVAILABLE:
            try:
                token_json = keyring.get_password(self.SERVICE_NAME, self.USERNAME)
            except Exception:
                pass

        if token_json is None and self.token_file.exists():
            token_json = self.token_file.read_text()

        if token_json:
            try:
                data = json.loads(token_json)
                return TokenData.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                return None

        return None

    def delete_token(self) -> None:
        """Delete stored token."""
        if KEYRING_AVAILABLE:
            try:
                keyring.delete_password(self.SERVICE_NAME, self.USERNAME)
            except Exception:
                pass

        if self.token_file.exists():
            self.token_file.unlink()

    def has_valid_token(self, buffer_seconds: int = 300) -> bool:
        """
        Check if we have a valid, non-expired token.

        Args:
            buffer_seconds: Consider expired if within this many seconds of expiry

        Returns:
            True if valid token exists
        """
        token = self.get_token()
        if token is None:
            return False
        return not token.expires_soon(buffer_seconds)

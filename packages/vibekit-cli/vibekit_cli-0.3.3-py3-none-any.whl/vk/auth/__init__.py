"""
VibeKit Auth Module - OAuth flow, JWT tokens, and session management.

This module handles authentication with the vkcli.com SaaS platform.

Usage:
    from vk.auth import AuthClient

    auth = AuthClient()
    auth.login()  # Opens browser for OAuth
    auth.get_token()  # Returns current JWT token
    auth.logout()  # Clears stored credentials
"""

from vk.auth.client import AuthClient
from vk.auth.config import AuthConfig
from vk.auth.tokens import TokenManager

__all__ = [
    "AuthClient",
    "TokenManager",
    "AuthConfig",
]

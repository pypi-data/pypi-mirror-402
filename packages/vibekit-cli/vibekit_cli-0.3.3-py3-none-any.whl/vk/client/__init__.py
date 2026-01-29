"""
VibeKit API Client Module - HTTP client for vkcli.com SaaS backend.

This module provides the API client for all CLI commands to communicate
with the SaaS platform.

Usage:
    from vk.client import VKClient

    client = VKClient()
    projects = client.projects.list()
    sprint = client.sprints.get_current()
"""

from vk.client.api import VKClient
from vk.client.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    VKClientError,
)

__all__ = [
    "VKClient",
    "VKClientError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
]

"""
VibeKit SDK - Vibe Coding Platform CLI

Simple, need-to-know platform for vibe coders.

This SDK is the CLI client that connects to the vkcli.com SaaS platform.
All configuration is done in the SaaS web UI, then synced locally.

Getting Started:
    $ pip install vibekit-cli
    $ vk init               # Register project, opens browser for auth
    $ vk pull               # Sync config from SaaS to local
    $ vk push               # Sync task status back to SaaS

Core Commands:
    vk init                 # Initialize & authenticate
    vk pull                 # SaaS -> Local (config, sprints, rules, CLAUDE.md)
    vk push                 # Local -> SaaS (task status, metrics)
    vk status               # View current sprint status
    vk open                 # Open project in browser

Stateless Intelligence (v0.3.0+):
    `vk pull` generates GSD-style artifacts with state encoded in filenames:
    - PROJECT.md            # Living requirements document
    - CLAUDE.md             # Context for Claude Code
    - .vk/INDEX.yaml        # Navigation hub (~100 tokens)
    - .vk/STATE.md          # Human-readable sprint summary
    - .vk/plans/ready/*.md  # Executable task plans

Documentation: https://vkcli.com/docs
Platform: https://vkcli.com
"""

__version__ = "0.3.2"
__author__ = "VibeKit Contributors"
__license__ = "MIT"

# Public API
from vk.auth import AuthClient
from vk.client import VKClient
from vk.generator import ClaudeMdGenerator
from vk.sync import SyncClient

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "AuthClient",
    "VKClient",
    "SyncClient",
    "ClaudeMdGenerator",
]

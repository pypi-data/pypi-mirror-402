#!/usr/bin/env python3
"""
VibeKit CLI - Configure in SaaS, execute locally.

Getting Started:
    pip install vibekit-cli         # Install
    vk login                  # Authenticate
    vk init                   # Initialize project
    vk pull                   # Sync config from SaaS

Commands:
    vk login                  # Authenticate with vkcli.com
    vk logout                 # Clear authentication
    vk init                   # Initialize project
    vk link <slug>            # Link existing project
    vk pull                   # Pull config from SaaS
    vk push                   # Push status to SaaS
    vk status                 # View sync status
    vk open                   # Open in browser
    vk sprint                 # View current sprint
    vk done <task-id>         # Mark task complete

Documentation: https://vkcli.com/docs
"""

import json
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import Optional

import httpx
import typer
import yaml
from rich.console import Console
from rich.table import Table

from vk import __version__

console = Console()


def _version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"vibekit-cli [green]{__version__}[/green]")
        raise typer.Exit()


app = typer.Typer(
    help="VibeKit - Configure in SaaS, execute locally | https://vkcli.com",
    add_completion=True,  # Enable shell completions
)


@app.callback()
def _main_callback(
    version: bool = typer.Option(
        False, "--version", "-v", callback=_version_callback, is_eager=True, help="Show version"
    ),
) -> None:
    """VibeKit CLI - Configure in SaaS, execute locally."""
    pass


def _is_newer_version(latest: str, current: str) -> bool:
    """Check if latest version is newer than current using semantic versioning."""
    try:
        latest_parts = [int(x) for x in latest.split(".")]
        current_parts = [int(x) for x in current.split(".")]
        return latest_parts > current_parts
    except (ValueError, AttributeError):
        return False


def _check_for_updates() -> None:
    """Check PyPI for newer version and show update notice."""
    cache_file = Path.home() / ".cache" / "vibekit" / "version_check.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    # Check cache (only check once per day)
    if cache_file.exists():
        try:
            cache = json.loads(cache_file.read_text())
            if time.time() - cache.get("checked_at", 0) < 86400:  # 24 hours
                if cache.get("latest") and _is_newer_version(cache["latest"], __version__):
                    _show_update_notice(cache["latest"])
                return
        except Exception:
            pass

    # Fetch latest version from PyPI (non-blocking, with timeout)
    try:
        response = httpx.get(
            "https://pypi.org/pypi/vibekit-cli/json",
            timeout=2.0,
            follow_redirects=True,
        )
        if response.status_code == 200:
            latest = response.json()["info"]["version"]
            cache_file.write_text(json.dumps({"latest": latest, "checked_at": time.time()}))
            if _is_newer_version(latest, __version__):
                _show_update_notice(latest)
    except Exception:
        pass  # Silently fail - don't interrupt user


def _show_update_notice(latest: str) -> None:
    """Show update notice to user."""
    console.print(
        f"\n[dim]Update available:[/dim] [yellow]{__version__}[/yellow] → [green]{latest}[/green]"
    )
    console.print("[dim]Run:[/dim] pip install --upgrade vibekit-cli\n")


# Project root - current working directory
PROJECT_ROOT = Path.cwd()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _get_vk_dir() -> Path:
    """Get .vk directory path (project data)."""
    return PROJECT_ROOT / ".vk"


def _get_claude_dir() -> Path:
    """Get .claude directory path (Claude config)."""
    return PROJECT_ROOT / ".claude"


def _get_config() -> Optional[dict]:
    """Load project config from .vk/config.yaml."""
    config_file = _get_vk_dir() / "config.yaml"
    if not config_file.exists():
        return None
    with open(config_file) as f:
        return yaml.safe_load(f)


def _save_config(config: dict) -> None:
    """Save project config to .vk/config.yaml."""
    config_file = _get_vk_dir() / "config.yaml"
    _get_vk_dir().mkdir(exist_ok=True)
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def _install_git_hooks() -> None:
    """Install git hooks for auto-sync on commit."""
    git_dir = PROJECT_ROOT / ".git"
    if not git_dir.exists():
        return

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    post_commit = hooks_dir / "post-commit"
    hook_content = """#!/bin/bash
# VibeKit Auto-Sync Hook
# Installed by: vk init

LOG_FILE=".vk/git-hook.log"
mkdir -p .vk

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

log "Post-commit hook triggered"

# Extract task IDs from commit message
TASKS=$(git log -1 --pretty=%B | grep -oE 'TASK-[0-9A-Za-z-]+' | sort -u)

# Mark each task as done
for task in $TASKS; do
    log "Marking task $task as done"
    vk done "$task" --quiet 2>> "$LOG_FILE" || log "Failed to mark $task as done"
done

# Push changes to SaaS (background)
log "Pushing to SaaS"
vk push --quiet 2>> "$LOG_FILE" &

exit 0
"""
    post_commit.write_text(hook_content)
    post_commit.chmod(0o755)


def _detect_project_from_git() -> Optional[str]:
    """Try to detect project from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        if result.returncode != 0:
            return None

        remote_url = result.stdout.strip()

        from vk.client import VKClient

        client = VKClient()
        if not client.is_authenticated():
            return None

        projects = client.projects.list()
        for project in projects:
            if project.get("git_url") == remote_url:
                return project.get("id")
            repo_name = remote_url.split("/")[-1].replace(".git", "")
            if project.get("name") == repo_name:
                return project.get("id")
        return None
    except Exception:
        return None


def _update_gitignore() -> None:
    """Add cache files to .gitignore."""
    gitignore_path = PROJECT_ROOT / ".gitignore"
    ignore_entries = [
        "# VibeKit cache",
        ".vk/cache/",
        ".vk/context-cache.json",
        ".vk/.state_hash",
    ]

    existing = ""
    if gitignore_path.exists():
        existing = gitignore_path.read_text()
        if ".vk/cache" in existing:
            return

    with open(gitignore_path, "a") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write("\n".join(ignore_entries) + "\n")


def _explain_synced_file(filepath: str) -> str:
    """Convert a synced file path to plain English explanation."""
    filepath_lower = filepath.lower()

    if "sprint" in filepath_lower and "current" in filepath_lower:
        return "Your current sprint tasks and progress"
    elif "sprint" in filepath_lower:
        return "Sprint plan and task list"
    elif "config.yaml" in filepath_lower or "config.json" in filepath_lower:
        return "Project settings and configuration"
    elif "rule" in filepath_lower:
        return "Coding rules and best practices"
    elif "pattern" in filepath_lower:
        return "Code patterns and templates"
    elif "workflow" in filepath_lower:
        return "Automated workflow definitions"
    elif "agent" in filepath_lower:
        return "AI agent configuration"
    elif "tool" in filepath_lower:
        return "Development tool settings"
    elif "claude.md" in filepath_lower:
        return "Instructions for Claude Code"
    elif "hook" in filepath_lower:
        return "Automation hooks and triggers"
    else:
        return filepath


# ============================================================================
# AUTH COMMANDS
# ============================================================================


@app.command()
def login():
    """
    Authenticate with vkcli.com using device flow.

    Opens browser for authentication and stores credentials locally.
    If a project is initialized with a custom api_url (e.g., localhost),
    authentication will use that URL instead of production.
    """
    console.print("\n[bold blue]🔐 VibeKit Login[/bold blue]")
    console.print("[blue]" + "━" * 50 + "[/blue]\n")

    from vk.auth import AuthClient
    from vk.auth.config import get_config

    # Check if project has custom api_url
    project_config = _get_config()
    api_url = project_config.get("api_url") if project_config else None

    # Get auth config (respects api_url for localhost)
    auth_config = get_config(api_url=api_url)
    auth = AuthClient(config=auth_config)

    if auth.is_authenticated():
        token = auth.get_token()
        # Validate token against the server to ensure it's actually valid
        try:
            from vk.client import VKClient

            client = VKClient(config=auth_config)
            client.get("/users/me")  # Validate token with server
            console.print(f"[green]Already logged in as {token.email}[/green]")
            console.print("[dim]Run 'vk logout' to switch accounts[/dim]")
            return
        except Exception:
            # Token exists locally but is invalid on server - clear and re-login
            console.print("[yellow]Session expired or invalid. Re-authenticating...[/yellow]")
            auth.token_manager.delete_token()  # Clear without printing logout message

    success = auth.login()

    if success:
        console.print("\n[green]✅ Login successful![/green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. Run [cyan]vk init[/cyan] to initialize a project")
        console.print("  2. Or [cyan]vk link <slug>[/cyan] to link existing project")
    else:
        console.print("\n[red]❌ Login failed[/red]")
        raise typer.Exit(1)


@app.command()
def logout():
    """Log out and clear stored credentials."""
    console.print("\n[bold blue]🔓 VibeKit Logout[/bold blue]")
    console.print("[blue]" + "━" * 50 + "[/blue]\n")

    from vk.auth import AuthClient

    auth = AuthClient()
    auth.logout()
    console.print("[green]✅ Logged out successfully[/green]")


# ============================================================================
# PROJECT COMMANDS
# ============================================================================


@app.command()
def init(
    project: Optional[str] = typer.Argument(
        None,
        help="Project slug (owner/name) to link to existing project. Creates new project if omitted.",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Reinitialize existing project"),
):
    """
    Initialize project and authenticate with vkcli.com.

    This command:
    1. Opens browser for authentication (if needed)
    2. Registers project in SaaS (or links to existing if slug provided)
    3. Creates local .vk/ and .claude/ folders
    4. Pulls initial configuration

    Examples:
        vk init                       # Create new project
        vk init myuser/myproject      # Link to existing project

    After init, configure your project at vkcli.com, then run 'vk pull'.
    """
    console.print("\n[bold blue]🚀 VibeKit - Initialize Project[/bold blue]")
    console.print("[blue]" + "━" * 50 + "[/blue]\n")

    from vk.auth import AuthClient
    from vk.client import VKClient

    # Check if already initialized
    config = _get_config()
    if config and config.get("project_id") and not force:
        console.print(f"[yellow]Project already initialized: {config.get('name')}[/yellow]")
        console.print(f"[dim]Project ID: {config.get('project_id')}[/dim]")
        console.print("\n[dim]Run 'vk pull' to sync or 'vk init --force' to reinitialize[/dim]")
        return

    if force and config and config.get("project_id"):
        console.print("[yellow]⚠ Warning: This will reinitialize the project[/yellow]")
        console.print(f"  Current project: [bold]{config.get('name')}[/bold]")
        console.print(f"  Project ID: {config.get('project_id')}")
        console.print("\n[dim]This action will:")
        console.print("  • Keep your project linked to SaaS")
        console.print("  • Refresh local configuration")
        console.print("  • Overwrite .vk/config.yaml[/dim]\n")

        if not typer.confirm("Do you want to continue?", default=False):
            console.print("\n[dim]Cancelled. Your project remains unchanged.[/dim]")
            raise typer.Exit(0)
        console.print("\n[yellow]Reinitializing project...[/yellow]\n")

    # Ensure authenticated
    auth = AuthClient()
    if not auth.is_authenticated():
        console.print("[bold]Step 1: Authentication[/bold]")
        success = auth.login()
        if not success:
            console.print("[red]Authentication failed[/red]")
            raise typer.Exit(1)
    else:
        token = auth.get_token()
        console.print(f"[green]✓ Authenticated as {token.email}[/green]")

    # If project slug provided, link to existing project
    if project:
        console.print(f"\n[bold]Step 2: Link to Existing Project[/bold]")
        linked_project = _link_to_project(project)
        if not linked_project:
            raise typer.Exit(1)

        # Pull initial config
        console.print("\n[bold]Step 3: Initial Sync[/bold]")
        from vk.sync import SyncClient

        sync = SyncClient(PROJECT_ROOT)
        result = sync.pull()

        if result.success:
            console.print(f"  [green]✓ Synced {len(result.files_synced)} files[/green]")
        else:
            console.print(f"  [yellow]⚠ Sync had issues: {result.errors}[/yellow]")

        # Success message
        project_id = linked_project.get("id") or linked_project.get("project_id")
        config_url = linked_project.get("config_url", f"https://vkcli.com/p/{project_id}")
        console.print("\n[green]" + "━" * 50 + "[/green]")
        console.print("[bold green]✅ Project initialized![/bold green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print(f"  1. Configure at: [link={config_url}]{config_url}[/link]")
        console.print("  2. Run [cyan]vk pull[/cyan] to sync changes")
        console.print("  3. Start coding!")
        return

    # Detect project info (no slug provided - create new project)
    console.print("\n[bold]Step 2: Project Detection[/bold]")

    project_name = PROJECT_ROOT.name
    git_remote = None

    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        if result.returncode == 0:
            git_remote = result.stdout.strip()
            console.print(f"  Git remote: {git_remote}")
    except Exception:
        pass

    console.print(f"  Project name: {project_name}")
    console.print(f"  Location: {PROJECT_ROOT}")

    # Check for existing project
    client = VKClient()
    existing_project = _detect_project_from_git()

    if existing_project:
        console.print("\n[green]Found existing project in SaaS![/green]")
        project_id = existing_project
        project_data = client.projects.get(project_id)
    else:
        # Create new project
        console.print("\n[bold]Step 3: Register Project[/bold]")

        # Detect languages
        languages = []
        if (PROJECT_ROOT / "pyproject.toml").exists() or (PROJECT_ROOT / "setup.py").exists():
            languages.append("python")
        if (PROJECT_ROOT / "package.json").exists():
            languages.append("javascript")
            if (PROJECT_ROOT / "tsconfig.json").exists():
                languages.append("typescript")
        if (PROJECT_ROOT / "go.mod").exists():
            languages.append("go")
        if (PROJECT_ROOT / "Cargo.toml").exists():
            languages.append("rust")

        console.print(f"  Detected languages: {', '.join(languages) or 'none'}")

        project_data = client.projects.create(
            name=project_name,
            path=str(PROJECT_ROOT),
            languages=languages or None,
        )
        project_id = project_data.get("id") or project_data.get("project_id")
        console.print(f"  [green]✓ Created project: {project_id}[/green]")

        # Update with git remote
        if git_remote:
            client.projects.update(project_id, git_remote_url=git_remote)

    # Save local config
    console.print("\n[bold]Step 4: Local Setup[/bold]")
    _get_vk_dir().mkdir(exist_ok=True)

    _save_config(
        {
            "project_id": project_id,
            "project_slug": project_data.get("slug", f"project/{project_name}"),
            "name": project_data.get("name", project_name),
        }
    )
    console.print("  [green]✓ Created .vk/config.yaml[/green]")

    # Update gitignore
    _update_gitignore()
    console.print("  [green]✓ Updated .gitignore[/green]")

    # Install git hooks
    _install_git_hooks()
    console.print("  [green]✓ Installed git hooks[/green]")

    # Pull initial config
    console.print("\n[bold]Step 5: Initial Sync[/bold]")
    from vk.sync import SyncClient

    sync = SyncClient(PROJECT_ROOT)
    result = sync.pull()

    if result.success:
        console.print(f"  [green]✓ Synced {len(result.files_synced)} files[/green]")
    else:
        console.print(f"  [yellow]⚠ Sync had issues: {result.errors}[/yellow]")

    # Success message
    config_url = project_data.get("config_url", f"https://vkcli.com/p/{project_id}")
    console.print("\n[green]" + "━" * 50 + "[/green]")
    console.print("[bold green]✅ Project initialized![/bold green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  1. Configure at: [link={config_url}]{config_url}[/link]")
    console.print("  2. Run [cyan]vk pull[/cyan] to sync changes")
    console.print("  3. Start coding!")


def _detect_git_slug() -> Optional[str]:
    """
    Detect project slug from git remote URL.

    Parses remote URLs like:
    - git@github.com:username/project.git
    - https://github.com/username/project.git
    - https://github.com/username/project

    Returns:
        Slug like "username/project" or None if not detected
    """
    import re
    import subprocess

    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None

        url = result.stdout.strip()

        # SSH format: git@github.com:username/project.git
        ssh_match = re.match(r"git@[\w.-]+:(.+?)(?:\.git)?$", url)
        if ssh_match:
            return ssh_match.group(1)

        # HTTPS format: https://github.com/username/project.git
        https_match = re.match(r"https?://[\w.-]+/(.+?)(?:\.git)?$", url)
        if https_match:
            return https_match.group(1)

        return None
    except Exception:
        return None


def _link_to_project(identifier: str, silent: bool = False) -> Optional[dict]:
    """
    Link to an existing project by slug or ID.

    Args:
        identifier: Project slug (owner/name) or project ID
        silent: If True, suppress output messages

    Returns:
        Project dict if successful, None if failed
    """
    from vk.auth import AuthClient
    from vk.client import VKClient
    from vk.client.exceptions import AuthenticationError, NotFoundError

    # Ensure authenticated
    auth = AuthClient()
    if not auth.is_authenticated():
        if not silent:
            console.print("[red]Not authenticated. Run 'vk login' first.[/red]")
        return None

    client = VKClient()

    # Fetch project
    if not silent:
        console.print(f"Looking up project: {identifier}")

    try:
        if "/" in identifier:
            project = client.projects.get_by_slug(identifier)
        else:
            project = client.projects.get(identifier)
    except NotFoundError:
        if not silent:
            console.print(f"[red]Project '{identifier}' not found in vkcli.com[/red]")
            console.print("[dim]Make sure the project exists and you have access to it.[/dim]")
        return None
    except AuthenticationError:
        if not silent:
            console.print("[red]Authentication failed. Try 'vk login' again.[/red]")
        return None
    except Exception as e:
        if not silent:
            console.print(f"[red]Error looking up project: {e}[/red]")
        return None

    project_id = project.get("id") or project.get("project_id")
    project_name = project.get("name", "Unknown")

    if not silent:
        console.print(f"[green]✓ Found: {project_name}[/green]")

    # Save config
    _get_vk_dir().mkdir(exist_ok=True)
    _save_config(
        {
            "project_id": project_id,
            "project_slug": project.get("slug", identifier),
            "name": project_name,
        }
    )

    # Update gitignore and hooks
    _update_gitignore()
    _install_git_hooks()

    return project


@app.command()
def link(
    identifier: Optional[str] = typer.Argument(
        None,
        help="Project slug (owner/name) or project ID. Auto-detects from git remote if omitted.",
    ),
):
    """
    Link an existing SaaS project to the current directory.

    Use this when you have a project configured in vkcli.com
    and want to connect it to a local directory.

    If no identifier is provided, auto-detects from git remote URL.

    Examples:
        vk link                       # Auto-detect from git remote
        vk link myuser/myproject      # Link by slug
        vk link 507f1f77bcf86cd799439011  # Link by project ID
    """
    console.print("\n[bold blue]🔗 VibeKit - Link Project[/bold blue]")
    console.print("[blue]" + "━" * 50 + "[/blue]\n")

    from vk.auth import AuthClient
    from vk.client import VKClient

    # Ensure authenticated
    auth = AuthClient()
    if not auth.is_authenticated():
        console.print("[red]Not authenticated. Run 'vk login' first.[/red]")
        raise typer.Exit(1)

    # Auto-detect from git remote if not provided
    if not identifier:
        console.print("Auto-detecting from git remote...")
        detected_slug = _detect_git_slug()
        if detected_slug:
            console.print(f"[green]✓ Detected: {detected_slug}[/green]")
            # Ask for confirmation
            if not typer.confirm(f"Link this directory to '{detected_slug}'?", default=True):
                console.print("[dim]Cancelled. Use: vk link username/project[/dim]")
                raise typer.Exit(0)
            identifier = detected_slug
        else:
            console.print("[red]Could not detect project from git remote.[/red]")
            console.print("[dim]Usage: vk link username/project[/dim]")
            raise typer.Exit(1)

    client = VKClient()

    # Fetch project
    console.print(f"Looking up project: {identifier}")

    try:
        if "/" in identifier:
            project = client.projects.get_by_slug(identifier)
        else:
            project = client.projects.get(identifier)
    except Exception as e:
        console.print(f"[red]Project not found: {e}[/red]")
        raise typer.Exit(1)

    project_id = project.get("id") or project.get("project_id")
    project_name = project.get("name", "Unknown")

    console.print(f"[green]✓ Found: {project_name}[/green]")

    # Check if already linked to a different project
    existing_config = _get_config()
    if existing_config and existing_config.get("project_id"):
        existing_id = existing_config.get("project_id")
        existing_name = existing_config.get("name", "Unknown")

        if existing_id != project_id:
            console.print(
                f"\n[yellow]⚠ This directory is already linked to '{existing_name}'[/yellow]"
            )
            if not typer.confirm(f"Switch to '{project_name}'?", default=False):
                console.print("[dim]Cancelled[/dim]")
                raise typer.Exit(0)

    # Save config
    _get_vk_dir().mkdir(exist_ok=True)
    _save_config(
        {
            "project_id": project_id,
            "project_slug": project.get("slug", identifier),
            "name": project_name,
        }
    )

    # Update gitignore and hooks
    _update_gitignore()
    _install_git_hooks()

    # Pull config
    console.print("\nPulling configuration...")
    from vk.sync import SyncClient

    sync = SyncClient(PROJECT_ROOT)
    result = sync.pull()

    if result.success:
        console.print(f"[green]✓ Synced {len(result.files_synced)} files[/green]")
    else:
        console.print(f"[yellow]⚠ {result.errors}[/yellow]")

    console.print("\n[green]✅ Project linked![/green]")
    console.print("[dim]Run 'vk pull' to sync updates[/dim]")


# ============================================================================
# SYNC COMMANDS
# ============================================================================


@app.command()
def pull(
    project: Optional[str] = typer.Argument(
        None,
        help="Project slug (owner/name) to link and pull. Uses current project if omitted.",
    ),
    generate: bool = typer.Option(
        False,
        "--generate",
        "-g",
        help="Use AI to generate project-specific rules, patterns, and CLAUDE.md content",
    ),
    studio: bool = typer.Option(
        False,
        "--studio",
        "-s",
        help="Pull AI Studio content as Claude Code plugin files (agents, commands, skills, hooks)",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Bypass local cache and fetch fresh data from SaaS",
    ),
    explain: bool = typer.Option(
        False,
        "--explain",
        help="Show plain English explanations of what's happening",
    ),
):
    """
    Pull configuration from SaaS to local .vk/ and .claude/ folders.

    If a project slug is provided, links to that project first then pulls.

    Downloads:
    - config.yaml: Project settings
    - sprints/current.yaml: Current sprint and tasks
    - rules/*.md: Coding rules and patterns
    - agents/*.yaml: Agent configurations
    - tools/*.yaml: Tool configurations

    Also generates CLAUDE.md for Claude Code integration.

    Examples:
        vk pull                       # Pull for current project
        vk pull myuser/myproject      # Link to project and pull

    Use --generate to enhance content with AI-powered generation based on your tech stack.
    Use --studio to pull AI Studio content (agents, commands, skills, hooks, rules, patterns).
    Use --no-cache to ensure you get the latest data from SaaS (stateless mode).
    """
    console.print("\n[bold blue]📥 VibeKit - Pull from SaaS[/bold blue]")
    console.print("[blue]" + "━" * 50 + "[/blue]\n")

    from vk.sync import SyncClient

    # If project slug provided, link to it first
    if project:
        console.print(f"[bold]Linking to project...[/bold]")
        linked_project = _link_to_project(project)
        if not linked_project:
            raise typer.Exit(1)
        console.print()

    sync = SyncClient(PROJECT_ROOT)

    if not sync.is_initialized():
        console.print("[red]Project not initialized. Run 'vk init' first.[/red]")
        raise typer.Exit(1)

    if explain:
        console.print("[dim]Downloading your project configuration from the cloud...[/dim]")
        console.print("[dim]This includes your custom rules, workflows, and current tasks.[/dim]\n")

    status_msg = (
        "[bold blue]Syncing from SaaS (fresh data)...[/bold blue]"
        if no_cache
        else "[bold blue]Syncing from SaaS...[/bold blue]"
    )
    with console.status(status_msg, spinner="dots"):
        result = sync.pull(no_cache=no_cache)

    if result.success:
        console.print()
        if explain:
            console.print("[bold]What we downloaded:[/bold]")
            for f in result.files_synced:
                explanation = _explain_synced_file(f)
                console.print(f"  [green]✓[/green] {explanation}")
        else:
            console.print("[bold]Synced files:[/bold]")
            for f in result.files_synced:
                console.print(f"  [green]✓[/green] {f}")

        # AI Generation if requested
        if generate:
            console.print("\n[bold cyan]🤖 AI Generation[/bold cyan]")
            with console.status("[bold cyan]Generating content...[/bold cyan]", spinner="dots"):
                gen_result = sync.generate_content()
            if gen_result.get("success"):
                console.print("  [green]✓[/green] Generated rules for your tech stack")
                console.print("  [green]✓[/green] Generated code patterns")
                console.print("  [green]✓[/green] Enhanced CLAUDE.md sections")
                if gen_result.get("files_written"):
                    for f in gen_result["files_written"]:
                        console.print(f"  [cyan]↳[/cyan] {f}")
            elif gen_result.get("error") == "not_configured":
                console.print(
                    "  [yellow]⚠[/yellow] AI not configured - set OpenRouter key in Admin settings"
                )
            else:
                console.print(
                    f"  [yellow]⚠[/yellow] {gen_result.get('error', 'Generation failed')}"
                )

        # AI Studio content if requested
        if studio:
            console.print("\n[bold magenta]🎨 AI Studio Content[/bold magenta]")
            with console.status("[bold magenta]Syncing AI Studio content...[/bold magenta]", spinner="dots"):
                studio_result = sync.pull_generated(include_claude_md=True)
            if studio_result.success:
                console.print("  [green]✓[/green] Synced Claude Code plugin files")
                if studio_result.files_synced:
                    for f in studio_result.files_synced:
                        console.print(f"    [magenta]↳[/magenta] {f}")
                if studio_result.warnings:
                    for w in studio_result.warnings:
                        console.print(f"  [yellow]⚠[/yellow] {w}")
            else:
                for error in studio_result.errors:
                    console.print(f"  [red]✗[/red] {error}")

        console.print("\n[green]✅ Pull complete![/green]")
        console.print("\n[dim]CLAUDE.md generated - Claude Code follows your rules.[/dim]")
    else:
        console.print("\n[red]❌ Pull failed:[/red]")
        for error in result.errors:
            console.print(f"  [red]• {error}[/red]")
        raise typer.Exit(1)


@app.command()
def push(
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output"),
    explain: bool = typer.Option(
        False,
        "--explain",
        help="Show plain English explanations of what's happening",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force push without conflict detection",
    ),
):
    """
    Push local changes to SaaS.

    Syncs task status and progress back to vkcli.com dashboard.

    Includes conflict detection to prevent overwriting server changes.
    Use --force to skip conflict detection.
    """
    if not quiet:
        console.print("\n[bold blue]📤 VibeKit - Push to SaaS[/bold blue]")
        console.print("[blue]" + "━" * 50 + "[/blue]\n")

    from vk.sync import SyncClient

    sync = SyncClient(PROJECT_ROOT)

    if not sync.is_initialized():
        if not quiet:
            console.print("[red]Project not initialized. Run 'vk init' first.[/red]")
        raise typer.Exit(1)

    if explain and not quiet:
        console.print("[dim]Uploading your local progress to the cloud dashboard...[/dim]")
        console.print("[dim]This lets you and your team see what's been completed.[/dim]\n")

    if quiet:
        result = sync.push(force=force)
    else:
        with console.status("[bold blue]Pushing to SaaS...[/bold blue]", spinner="dots"):
            result = sync.push(force=force)

    if result.success:
        if not quiet:
            console.print("[green]✅ Push complete![/green]")
            if result.files_synced:
                if explain:
                    console.print("[dim]Updated the dashboard with your latest progress[/dim]")
                else:
                    for f in result.files_synced:
                        console.print(f"  [green]✓[/green] {f}")
    else:
        if not quiet:
            # Check for conflict error
            is_conflict = any("Remote state has changed" in str(e) for e in result.errors)
            if is_conflict:
                console.print("[yellow]⚠ Conflict detected[/yellow]")
                for error in result.errors:
                    console.print(f"  {error}")
                console.print("\n[bold]Options:[/bold]")
                console.print("  1. [cyan]vk pull[/cyan] - Sync latest changes first")
                console.print(
                    "  2. [cyan]vk push --force[/cyan] - Override remote changes (use with caution)"
                )
            else:
                console.print(f"[red]❌ Push failed: {result.errors}[/red]")
        raise typer.Exit(1)


@app.command()
def update():
    """
    Update local config and regenerate CLAUDE.md.

    Convenience command that runs pull and regenerates Claude integration.
    """
    console.print("\n[bold blue]🔄 VibeKit - Update[/bold blue]")
    console.print("[blue]" + "━" * 50 + "[/blue]\n")

    from vk.sync import SyncClient

    sync = SyncClient(PROJECT_ROOT)

    if not sync.is_initialized():
        console.print("[red]Project not initialized. Run 'vk init' first.[/red]")
        raise typer.Exit(1)

    # Pull latest
    with console.status("[bold blue]Pulling latest config...[/bold blue]", spinner="dots"):
        result = sync.pull()

    if result.success:
        console.print(f"[green]✓ Synced {len(result.files_synced)} files[/green]")
    else:
        console.print(f"[yellow]⚠ {result.errors}[/yellow]")

    # Regenerate CLAUDE.md
    with console.status("[bold blue]Regenerating CLAUDE.md...[/bold blue]", spinner="dots"):
        from vk.generator import ClaudeMdGenerator

        generator = ClaudeMdGenerator(PROJECT_ROOT)
        output_path = generator.generate()
    console.print(f"[green]✓ {output_path.name}[/green]")

    console.print("\n[green]✅ Update complete![/green]")


# ============================================================================
# CONFIG COMMANDS
# ============================================================================


@app.command()
def config(
    key: Optional[str] = typer.Argument(None, help="Config key (e.g., api_url, debug_mode)"),
    value: Optional[str] = typer.Argument(None, help="Value to set (only with key)"),
    get: Optional[str] = typer.Option(None, "--get", help="Get specific config value"),
    set_key: Optional[str] = typer.Option(None, "--set", help="Set config key (use with VALUE)"),
    unset: Optional[str] = typer.Option(None, "--unset", help="Remove config key"),
    list_all: bool = typer.Option(False, "--list", "-l", help="List all configuration"),
    global_config: bool = typer.Option(
        False, "--global", "-g", help="Use global config (~/.vk/config.yaml)"
    ),
):
    """
    View and manage VibeKit configuration.

    Configuration can be stored at two levels:
    - Project: .vk/config.yaml (default)
    - Global: ~/.vk/config.yaml (use --global)

    Examples:
        vk config                        # Show all config
        vk config api_url                # Get specific value
        vk config api_url http://...     # Set value
        vk config --get api_url          # Get specific value
        vk config --set api_url http://... # Set value
        vk config --unset api_url        # Remove value
        vk config --list                 # List all config
        vk config --global --list        # List global config
    """
    from pathlib import Path

    # Determine config file location
    if global_config:
        config_file = Path.home() / ".vk" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
    else:
        config_file = _get_vk_dir() / "config.yaml"
        if not config_file.parent.exists():
            console.print("[yellow]Project not initialized. Run 'vk init' or use --global[/yellow]")
            raise typer.Exit(1)

    # Load existing config
    if config_file.exists():
        with open(config_file) as f:
            config_data = yaml.safe_load(f) or {}
    else:
        config_data = {}

    # Handle --unset
    if unset:
        if unset in config_data:
            del config_data[unset]
            with open(config_file, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)
            console.print(f"[green]Removed '{unset}' from config[/green]")
        else:
            console.print(f"[yellow]Key '{unset}' not found in config[/yellow]")
        return

    # Handle --set KEY VALUE or KEY VALUE pattern
    if set_key and value:
        config_data[set_key] = value
        with open(config_file, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False)
        console.print(f"[green]Set '{set_key}' = '{value}'[/green]")
        return
    elif key and value:
        config_data[key] = value
        with open(config_file, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False)
        console.print(f"[green]Set '{key}' = '{value}'[/green]")
        return

    # Handle --get KEY or single KEY argument (get mode)
    if get:
        if get in config_data:
            console.print(f"{config_data[get]}")
        else:
            console.print(f"[yellow]Key '{get}' not found[/yellow]")
            raise typer.Exit(1)
        return
    elif key and not value:
        if key in config_data:
            console.print(f"{config_data[key]}")
        else:
            console.print(f"[yellow]Key '{key}' not found[/yellow]")
            raise typer.Exit(1)
        return

    # Default: show all config (--list or no args)
    console.print("\n[bold blue]VibeKit Configuration[/bold blue]")
    console.print("[blue]" + "━" * 50 + "[/blue]\n")

    scope = "Global" if global_config else "Project"
    console.print(f"[bold]Scope:[/bold] {scope}")
    console.print(f"[dim]File: {config_file}[/dim]\n")

    if not config_data:
        console.print("[dim]No configuration set[/dim]")
        console.print("\n[bold]Usage:[/bold]")
        console.print("  vk config KEY VALUE      # Set a value")
        console.print("  vk config KEY            # Get a value")
        console.print("  vk config --unset KEY    # Remove a value")
    else:
        console.print("[bold]Configuration:[/bold]")
        for k, v in sorted(config_data.items()):
            # Format nested values nicely
            if isinstance(v, dict):
                console.print(f"  [cyan]{k}[/cyan]:")
                for sub_k, sub_v in v.items():
                    console.print(f"    {sub_k}: {sub_v}")
            elif isinstance(v, list):
                console.print(f"  [cyan]{k}[/cyan]: {', '.join(str(x) for x in v)}")
            else:
                console.print(f"  [cyan]{k}[/cyan]: {v}")


# ============================================================================
# STATUS COMMANDS
# ============================================================================


@app.command()
def status(
    explain: bool = typer.Option(
        False,
        "--explain",
        help="Show plain English explanations of what's happening",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output in JSON format",
    ),
):
    """Show project and authentication status."""
    from vk.auth import AuthClient

    # Auth status
    auth = AuthClient()
    authenticated = auth.is_authenticated()
    user_email = auth.get_token().email if authenticated else None

    # Project status
    config = _get_config()

    # Files status
    vk_dir = _get_vk_dir()
    vk_exists = vk_dir.exists()
    file_count = 0
    if vk_exists:
        files = list(vk_dir.rglob("*"))
        file_count = len([f for f in files if f.is_file()])

    claude_md = PROJECT_ROOT / "CLAUDE.md"
    claude_md_exists = claude_md.exists()

    # JSON output
    if json_output:
        status_data = {
            "authenticated": authenticated,
            "user_email": user_email,
            "project": {
                "initialized": config is not None,
                "name": config.get("name") if config else None,
                "project_id": config.get("project_id") if config else None,
                "project_slug": config.get("project_slug") if config else None,
            },
            "local_files": {
                "vk_dir_exists": vk_exists,
                "file_count": file_count,
                "claude_md_exists": claude_md_exists,
            },
        }
        console.print(json.dumps(status_data, indent=2))
        return

    # Human-readable output
    console.print("\n[bold blue]📊 VibeKit Status[/bold blue]")
    console.print("[blue]" + "━" * 50 + "[/blue]\n")

    if explain:
        console.print("[bold]Are you logged in?[/bold]")
    else:
        console.print("[bold]Authentication:[/bold]")

    if authenticated:
        if explain:
            console.print(f"  [green]✓[/green] Yes, you're logged in as {user_email}")
        else:
            console.print(f"  [green]✓[/green] Logged in as {user_email}")
    else:
        if explain:
            console.print("  [red]✗[/red] No, you need to log in first")
            console.print("  [dim]Run 'vk login' to connect to your account[/dim]")
        else:
            console.print("  [red]✗[/red] Not authenticated")
            console.print("  [dim]Run 'vk login' to authenticate[/dim]")

    # Project status
    if explain:
        console.print("\n[bold]What project is this?[/bold]")
    else:
        console.print("\n[bold]Project:[/bold]")

    if config:
        if explain:
            console.print(f"  This is: {config.get('name', 'Unknown')}")
            console.print("  [dim]You can see it on the dashboard at vkcli.com[/dim]")
        else:
            console.print(f"  Name: {config.get('name', 'Unknown')}")
            console.print(f"  ID: {config.get('project_id', 'Unknown')}")
            console.print(f"  Slug: {config.get('project_slug', 'Unknown')}")
    else:
        if explain:
            console.print("  [yellow]This project isn't connected yet[/yellow]")
            console.print("  [dim]Run 'vk init' to get started[/dim]")
        else:
            console.print("  [yellow]Not initialized[/yellow]")
            console.print("  [dim]Run 'vk init' to initialize[/dim]")

    # Files status
    if explain:
        console.print("\n[bold]Is everything set up locally?[/bold]")
    else:
        console.print("\n[bold]Local Files:[/bold]")

    if vk_exists:
        if explain:
            console.print(
                f"  [green]✓[/green] Yes, your configuration is downloaded ({file_count} files)"
            )
        else:
            console.print(f"  [green]✓[/green] .vk/ exists ({file_count} files)")

        if claude_md_exists:
            if explain:
                console.print("  [green]✓[/green] Claude Code is configured and ready")
            else:
                console.print("  [green]✓[/green] CLAUDE.md exists")
        else:
            if explain:
                console.print(
                    "  [yellow]✗[/yellow] Claude Code needs configuration (run 'vk pull')"
                )
            else:
                console.print("  [yellow]✗[/yellow] CLAUDE.md missing (run 'vk pull')")
    else:
        if explain:
            console.print("  [yellow]✗[/yellow] No configuration found locally")
            console.print("  [dim]Run 'vk pull' to download your settings[/dim]")
        else:
            console.print("  [yellow]✗[/yellow] .vk/ not found")


@app.command(name="open")
def open_browser():
    """Open project in browser at vkcli.com."""
    config = _get_config()

    if not config or not config.get("project_id"):
        console.print("[red]Project not initialized. Run 'vk init' first.[/red]")
        raise typer.Exit(1)

    project_id = config["project_id"]
    url = f"https://vkcli.com/p/{project_id}"

    console.print(f"Opening: {url}")
    webbrowser.open(url)


# ============================================================================
# TASK COMMANDS
# ============================================================================


@app.command()
def sprint(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output in JSON format",
    ),
):
    """View current sprint status."""
    sprint_file = _get_vk_dir() / "sprints" / "current.yaml"

    if not sprint_file.exists():
        if json_output:
            console.print(json.dumps({"error": "No active sprint"}, indent=2))
        else:
            console.print("[yellow]No active sprint.[/yellow]")
            console.print("[dim]Configure a sprint at vkcli.com, then run 'vk pull'[/dim]")
        return

    with open(sprint_file) as f:
        sprint_data = yaml.safe_load(f)

    if not sprint_data:
        if json_output:
            console.print(json.dumps({"error": "Sprint file is empty"}, indent=2))
        else:
            console.print("[yellow]Sprint file is empty.[/yellow]")
        return

    # JSON output
    if json_output:
        tasks = sprint_data.get("tasks", [])
        done = len([t for t in tasks if t.get("status") in ("done", "completed")])
        output_data = {
            "name": sprint_data.get("name", "Unnamed Sprint"),
            "goal": sprint_data.get("goal"),
            "tasks": tasks,
            "summary": {
                "total": len(tasks),
                "done": done,
                "in_progress": len([t for t in tasks if t.get("status") == "in_progress"]),
                "pending": len([t for t in tasks if t.get("status") == "pending"]),
                "blocked": len([t for t in tasks if t.get("status") == "blocked"]),
            },
        }
        console.print(json.dumps(output_data, indent=2))
        return

    # Human-readable output
    console.print("\n[bold blue]🏃 Current Sprint[/bold blue]")
    console.print("[blue]" + "━" * 50 + "[/blue]\n")

    # Sprint info
    console.print(f"[bold]{sprint_data.get('name', 'Unnamed Sprint')}[/bold]")
    if sprint_data.get("goal"):
        console.print(f"[dim]{sprint_data['goal']}[/dim]")

    # Tasks table
    tasks = sprint_data.get("tasks", [])
    if tasks:
        console.print()
        table = Table(show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("Title")
        table.add_column("Status", style="bold")
        table.add_column("Priority")

        for task in tasks:
            status = task.get("status", "pending")
            status_style = {
                "done": "[green]✓ done[/green]",
                "completed": "[green]✓ done[/green]",
                "in_progress": "[yellow]▶ active[/yellow]",
                "pending": "[dim]○ pending[/dim]",
                "blocked": "[red]✗ blocked[/red]",
                "skipped": "[dim]⊘ skipped[/dim]",
            }.get(status, status)

            table.add_row(
                task.get("id", "?"),
                task.get("title", "Untitled")[:50],
                status_style,
                task.get("priority", "-"),
            )

        console.print(table)

        # Summary (handle both "done" and "completed" for backwards compat)
        done = len([t for t in tasks if t.get("status") in ("done", "completed")])
        console.print(f"\n[bold]Progress:[/bold] {done}/{len(tasks)} tasks complete")
    else:
        console.print("\n[dim]No tasks in sprint.[/dim]")


@app.command()
def tasks(
    status: str = typer.Option(
        None, "--status", "-s", help="Filter by status (pending, in_progress, done, blocked)"
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output in JSON format",
    ),
):
    """
    List tasks in current sprint.

    Shows all tasks with optional status filtering.
    """
    sprint_file = _get_vk_dir() / "sprints" / "current.yaml"

    if not sprint_file.exists():
        if json_output:
            console.print(json.dumps({"error": "No active sprint"}, indent=2))
        else:
            console.print("[yellow]No active sprint.[/yellow]")
            console.print("[dim]Configure a sprint at vkcli.com, then run 'vk pull'[/dim]")
        return

    with open(sprint_file) as f:
        sprint_data = yaml.safe_load(f)

    if not sprint_data:
        if json_output:
            console.print(json.dumps({"error": "Sprint file is empty"}, indent=2))
        else:
            console.print("[yellow]Sprint file is empty.[/yellow]")
        return

    task_list = sprint_data.get("tasks", [])

    if not task_list:
        if json_output:
            console.print(json.dumps({"tasks": [], "summary": {"total": 0}}, indent=2))
        else:
            console.print("[dim]No tasks in sprint.[/dim]")
        return

    # Filter by status if specified
    filtered_task_list = task_list
    if status:
        # Handle "done" and "completed" as synonyms
        if status in ("done", "completed"):
            filtered_task_list = [t for t in task_list if t.get("status") in ("done", "completed")]
        else:
            filtered_task_list = [t for t in task_list if t.get("status") == status]
        if not filtered_task_list:
            if json_output:
                console.print(json.dumps({"tasks": [], "filter": status}, indent=2))
            else:
                console.print(f"[dim]No tasks with status '{status}'[/dim]")
            return

    # JSON output
    if json_output:
        total = len(task_list)
        done_count = len([t for t in task_list if t.get("status") in ("done", "completed")])
        in_progress = len([t for t in task_list if t.get("status") == "in_progress"])
        output_data = {
            "tasks": filtered_task_list,
            "summary": {
                "total": total,
                "done": done_count,
                "in_progress": in_progress,
                "pending": total - done_count - in_progress,
            },
        }
        if status:
            output_data["filter"] = status
        console.print(json.dumps(output_data, indent=2))
        return

    # Human-readable output
    console.print("\n[bold blue]📋 Tasks[/bold blue]")
    console.print("[blue]" + "━" * 50 + "[/blue]\n")

    table = Table(show_header=True)
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Status", style="bold")
    table.add_column("Priority")

    for task in filtered_task_list:
        task_status = task.get("status", "pending")
        status_style = {
            "done": "[green]✓ done[/green]",
            "completed": "[green]✓ done[/green]",
            "in_progress": "[yellow]▶ active[/yellow]",
            "pending": "[dim]○ pending[/dim]",
            "blocked": "[red]✗ blocked[/red]",
            "skipped": "[dim]⊘ skipped[/dim]",
        }.get(task_status, task_status)

        table.add_row(
            task.get("id", task.get("task_id", "?")),
            task.get("title", "Untitled")[:50],
            status_style,
            task.get("priority", "-"),
        )

    console.print(table)

    # Summary
    total = len(task_list)
    done_count = len([t for t in task_list if t.get("status") in ("done", "completed")])
    in_progress = len([t for t in task_list if t.get("status") == "in_progress"])

    console.print(
        f"\n[bold]Summary:[/bold] {done_count} done, {in_progress} active, {total - done_count - in_progress} pending"
    )


@app.command()
def start(
    task_id: str = typer.Argument(None, help="Task ID (auto-selects first pending if omitted)"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output"),
):
    """
    Start working on a task.

    Marks task as in_progress and syncs to SaaS immediately.
    If no task ID provided, auto-selects the first pending task.

    Note: All task updates go to SaaS first, then local cache is updated.
    """
    from vk.sync import SyncClient

    sync = SyncClient(PROJECT_ROOT)

    # Pull latest state from SaaS first (stateless approach)
    sync.pull(no_cache=True)

    sprint_file = _get_vk_dir() / "sprints" / "current.yaml"

    if not sprint_file.exists():
        if not quiet:
            console.print("[red]No active sprint.[/red]")
        raise typer.Exit(1)

    with open(sprint_file) as f:
        sprint_data = yaml.safe_load(f) or {}

    tasks = sprint_data.get("tasks", [])

    # Auto-select first pending task if no ID provided
    if not task_id:
        pending_tasks = [t for t in tasks if t.get("status") == "pending"]
        if not pending_tasks:
            if not quiet:
                console.print("[yellow]No pending tasks to start.[/yellow]")
            raise typer.Exit(0)
        task_id = pending_tasks[0].get("id")
        if not quiet:
            console.print(f"[dim]Auto-selected: {task_id}[/dim]")

    task_found = False

    for task in tasks:
        if task.get("id") == task_id:
            task["status"] = "in_progress"
            task_found = True
            break

    if not task_found:
        if not quiet:
            console.print(f"[red]Task not found: {task_id}[/red]")
        raise typer.Exit(1)

    # Save locally (cache)
    with open(sprint_file, "w") as f:
        yaml.dump(sprint_data, f, default_flow_style=False)

    if not quiet:
        console.print(f"[yellow]▶ Started {task_id}[/yellow]")

    # Push to SaaS (source of truth)
    sync.push()

    if not quiet:
        console.print("[dim]Synced to SaaS (source of truth)[/dim]")


@app.command()
def done(
    task_id: str = typer.Argument(..., help="Task ID to mark as complete"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output"),
):
    """
    Mark a task as complete.

    Updates local sprint file and syncs to SaaS.
    """
    sprint_file = _get_vk_dir() / "sprints" / "current.yaml"

    if not sprint_file.exists():
        if not quiet:
            console.print("[red]No active sprint.[/red]")
        raise typer.Exit(1)

    with open(sprint_file) as f:
        sprint_data = yaml.safe_load(f) or {}

    tasks = sprint_data.get("tasks", [])
    task_found = False

    for task in tasks:
        if task.get("id") == task_id:
            task["status"] = "completed"
            task_found = True
            break

    if not task_found:
        if not quiet:
            console.print(f"[red]Task not found: {task_id}[/red]")
        raise typer.Exit(1)

    # Save
    with open(sprint_file, "w") as f:
        yaml.dump(sprint_data, f, default_flow_style=False)

    if not quiet:
        console.print(f"[green]✓ Marked {task_id} as done[/green]")

    # Push to SaaS
    from vk.sync import SyncClient

    sync = SyncClient(PROJECT_ROOT)
    sync.push()

    if not quiet:
        console.print("[dim]Synced to SaaS[/dim]")


@app.command()
def block(
    task_id: str = typer.Argument(..., help="Task ID to block"),
    reason: str = typer.Option(None, "--reason", "-r", help="Reason for blocking"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output"),
):
    """
    Mark a task as blocked.

    Use when a task cannot proceed due to dependencies or issues.
    """
    sprint_file = _get_vk_dir() / "sprints" / "current.yaml"

    if not sprint_file.exists():
        if not quiet:
            console.print("[red]No active sprint.[/red]")
        raise typer.Exit(1)

    with open(sprint_file) as f:
        sprint_data = yaml.safe_load(f) or {}

    tasks = sprint_data.get("tasks", [])
    task_found = False

    for task in tasks:
        if task.get("id") == task_id:
            task["status"] = "blocked"
            if reason:
                task["blocked_reason"] = reason
            task_found = True
            break

    if not task_found:
        if not quiet:
            console.print(f"[red]Task not found: {task_id}[/red]")
        raise typer.Exit(1)

    # Save
    with open(sprint_file, "w") as f:
        yaml.dump(sprint_data, f, default_flow_style=False)

    if not quiet:
        console.print(f"[red]✗ Blocked {task_id}[/red]")
        if reason:
            console.print(f"[dim]Reason: {reason}[/dim]")

    # Push to SaaS
    from vk.sync import SyncClient

    sync = SyncClient(PROJECT_ROOT)
    sync.push()

    if not quiet:
        console.print("[dim]Synced to SaaS[/dim]")


@app.command()
def skip(
    task_id: str = typer.Argument(..., help="Task ID to skip"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output"),
):
    """
    Skip a task in the current sprint.

    Removes the task from active work without marking it complete.
    """
    sprint_file = _get_vk_dir() / "sprints" / "current.yaml"

    if not sprint_file.exists():
        if not quiet:
            console.print("[red]No active sprint.[/red]")
        raise typer.Exit(1)

    with open(sprint_file) as f:
        sprint_data = yaml.safe_load(f) or {}

    tasks = sprint_data.get("tasks", [])
    task_found = False

    for task in tasks:
        if task.get("id") == task_id:
            task["status"] = "skipped"
            task_found = True
            break

    if not task_found:
        if not quiet:
            console.print(f"[red]Task not found: {task_id}[/red]")
        raise typer.Exit(1)

    # Save
    with open(sprint_file, "w") as f:
        yaml.dump(sprint_data, f, default_flow_style=False)

    if not quiet:
        console.print(f"[yellow]⊘ Skipped {task_id}[/yellow]")

    # Push to SaaS
    from vk.sync import SyncClient

    sync = SyncClient(PROJECT_ROOT)
    sync.push()

    if not quiet:
        console.print("[dim]Synced to SaaS[/dim]")


@app.command()
def run(
    project: Optional[str] = typer.Argument(
        None,
        help="Project slug (e.g., 'username/project-name'). Links if not already linked.",
    ),
    task_id: Optional[str] = typer.Option(
        None,
        "--task",
        "-t",
        help="Specific task ID to start. Auto-selects first pending if omitted.",
    ),
):
    """
    Link, pull, and start working on a task in one command.

    This is a convenience command that combines:
    - vk link <project> (if project specified and not already linked)
    - vk pull (sync latest config from SaaS)
    - vk start (start the next pending task)

    Examples:
        vk run myorg/myproject    # Link, pull, and start first task
        vk run                    # Pull and start (if already linked)
        vk run -t abc123          # Start a specific task
    """
    console.print("\n[bold blue]🚀 VibeKit - Run[/bold blue]")
    console.print("[blue]" + "━" * 50 + "[/blue]\n")

    from vk.sync import SyncClient

    sync = SyncClient(PROJECT_ROOT)

    # Step 1: Link if project provided and not already linked
    if project:
        if not sync.is_initialized():
            console.print(f"[cyan]Linking to project:[/cyan] {project}")

            from vk.auth import AuthClient
            from vk.client import VKClient

            auth = AuthClient()
            if not auth.is_authenticated():
                console.print("[red]Not logged in. Run 'vk login' first.[/red]")
                raise typer.Exit(1)

            client = VKClient()
            try:
                if "/" in project:
                    proj = client.projects.get_by_slug(project)
                else:
                    proj = client.projects.get(project)
            except Exception as e:
                console.print(f"[red]Project not found: {e}[/red]")
                raise typer.Exit(1)

            project_id = proj.get("id") or proj.get("project_id")
            project_name = proj.get("name", "Unknown")

            # Save config
            _get_vk_dir().mkdir(exist_ok=True)
            _save_config(
                {
                    "project_id": project_id,
                    "project_slug": proj.get("slug", project),
                    "slug": proj.get("slug", project),
                    "name": project_name,
                }
            )
            _update_gitignore()

            console.print(f"[green]✓ Linked to {project_name}[/green]\n")
        else:
            # Already initialized, check if same project
            current_slug = sync.get_project_slug()
            if current_slug and current_slug != project:
                console.print(f"[yellow]Already linked to {current_slug}[/yellow]")
                console.print(f"[dim]Run 'vk link {project}' to switch projects[/dim]")
            else:
                console.print(f"[dim]Already linked to {project}[/dim]\n")

    # Check if initialized
    if not sync.is_initialized():
        console.print("[red]Project not initialized.[/red]")
        console.print("[dim]Run 'vk run <project-slug>' or 'vk init' first.[/dim]")
        raise typer.Exit(1)

    # Step 2: Pull latest
    console.print("[cyan]Pulling latest configuration...[/cyan]")
    try:
        pull_result = sync.pull()
        if pull_result.success:
            console.print("[green]✓ Synced from SaaS[/green]\n")
        else:
            errors = ", ".join(pull_result.errors) if pull_result.errors else "Unknown"
            console.print(f"[yellow]Pull warning: {errors}[/yellow]\n")
    except Exception as e:
        console.print(f"[red]Pull failed: {e}[/red]")
        raise typer.Exit(1)

    # Step 3: Start task
    sprint_file = PROJECT_ROOT / ".vk" / "sprints" / "current.yaml"
    if not sprint_file.exists():
        console.print("[yellow]No active sprint.[/yellow]")
        console.print("[dim]Create a sprint at vkcli.com, then run again.[/dim]")
        raise typer.Exit(0)

    import yaml

    with open(sprint_file) as f:
        sprint_data = yaml.safe_load(f)

    if not sprint_data:
        console.print("[yellow]Sprint file is empty.[/yellow]")
        raise typer.Exit(0)

    tasks_list = sprint_data.get("tasks", [])
    if not tasks_list:
        console.print("[yellow]No tasks in current sprint.[/yellow]")
        raise typer.Exit(0)

    # Find task to start
    target_task = None
    if task_id:
        # Find specific task
        for t in tasks_list:
            if t.get("task_id", "").startswith(task_id) or t.get("id", "").startswith(task_id):
                target_task = t
                break
        if not target_task:
            console.print(f"[red]Task {task_id} not found in current sprint.[/red]")
            raise typer.Exit(1)
    else:
        # Auto-select first pending task
        for t in tasks_list:
            if t.get("status") == "pending":
                target_task = t
                break

    if not target_task:
        console.print("[green]✓ All tasks completed![/green]")
        console.print("[dim]Create more tasks at vkcli.com[/dim]")
        raise typer.Exit(0)

    # Display task info
    task_title = target_task.get("title", "Untitled")
    task_priority = target_task.get("priority", "medium")
    task_desc = target_task.get("description", "")

    console.print(f"[bold]Starting task:[/bold] {task_title}")
    console.print(f"[dim]Priority: {task_priority}[/dim]")
    if task_desc:
        console.print(f"\n[dim]{task_desc[:200]}{'...' if len(task_desc) > 200 else ''}[/dim]")

    # Show acceptance criteria if available
    criteria = target_task.get("acceptance_criteria", [])
    if criteria:
        console.print("\n[bold]Acceptance Criteria:[/bold]")
        for i, c in enumerate(criteria[:5], 1):
            console.print(f"  {i}. {c}")
        if len(criteria) > 5:
            console.print(f"  [dim]...and {len(criteria) - 5} more[/dim]")

    # Show files likely to modify
    files = target_task.get("files_likely", [])
    if files:
        console.print("\n[bold]Files to modify:[/bold]")
        for f in files[:5]:
            console.print(f"  • {f}")
        if len(files) > 5:
            console.print(f"  [dim]...and {len(files) - 5} more[/dim]")

    console.print("\n[green]Ready to code![/green]")
    console.print("[dim]Use your Claude Code assistant to implement this task.[/dim]")


@app.command()
def watch(
    verbose: bool = typer.Option(True, "--verbose/--quiet", help="Print events to console"),
):
    """
    Watch project for real-time updates from SaaS.

    Connects to vkcli.com SSE endpoint and auto-updates local files
    when changes occur on the server (task updates, sprint changes, etc.).

    This enables true stateless operation - your local files stay in sync
    with the dashboard automatically.

    Press Ctrl+C to stop watching.
    """
    console.print("\n[bold blue]👁 VibeKit - Watch Mode[/bold blue]")
    console.print("[blue]" + "━" * 50 + "[/blue]\n")

    try:
        import asyncio

        from vk.sync.realtime import watch_project

        # Run the async watch function
        asyncio.run(watch_project(PROJECT_ROOT, verbose=verbose))
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching[/dim]")
    except ImportError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[dim]Install httpx to enable watch mode: pip install httpx[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Watch failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def whoami():
    """
    Show current authenticated user.

    Displays email and organization information.
    """
    from vk.auth import AuthClient

    auth = AuthClient()

    if not auth.is_authenticated():
        console.print("[yellow]Not logged in.[/yellow]")
        console.print("[dim]Run 'vk login' to authenticate.[/dim]")
        raise typer.Exit(1)

    token = auth.get_token()
    console.print(f"\n[bold]Logged in as:[/bold] {token.email}")
    if hasattr(token, "org") and token.org:
        console.print(f"[dim]Organization: {token.org}[/dim]")

    # Show project info if initialized
    config = _get_config()
    if config and config.get("project_id"):
        console.print(f"\n[bold]Current project:[/bold] {config.get('name')}")
        console.print(f"[dim]Project ID: {config.get('project_id')}[/dim]")


@app.command()
def deploy(
    environment: str = typer.Argument("local", help="Environment: local, prod, or ci"),
    framework: Optional[str] = typer.Option(
        None, "--framework", "-f", help="Force framework (nextjs, vue, fastapi, express)"
    ),
    no_start: bool = typer.Option(
        False, "--no-start", help="Generate files only, don't start services"
    ),
):
    """
    Generate Docker infrastructure and deploy to local staging.

    Detects project framework and generates:
    - Dockerfile (optimized multi-stage build)
    - docker-compose.yaml (for local environment)
    - .dockerignore
    - CI/CD configs (for ci environment)

    Environments:
        local: Docker Compose for local staging (default)
        prod: Production-ready Dockerfile only
        ci: CI/CD pipeline setup

    Examples:
        vk deploy                    # Local staging with auto-detect
        vk deploy prod              # Generate production Dockerfile
        vk deploy ci                # Setup CI/CD pipeline
        vk deploy --framework vue   # Force Vue.js template
    """
    console.print("\n[bold blue]🐳 VibeKit - Deploy Infrastructure[/bold blue]")
    console.print("[blue]" + "━" * 50 + "[/blue]\n")

    # Get plugin root for templates
    plugin_root = Path(__file__).parent.parent / "vk-plugin"
    templates_dir = plugin_root / "templates"

    if not templates_dir.exists():
        console.print(f"[red]Templates directory not found: {templates_dir}[/red]")
        raise typer.Exit(1)

    # Step 1: Detect framework
    console.print("[bold]Step 1: Framework Detection[/bold]")

    detected_framework = None
    if not framework:
        # Auto-detect framework
        if (PROJECT_ROOT / "next.config.js").exists() or (PROJECT_ROOT / "next.config.ts").exists():
            detected_framework = "nextjs"
        elif (PROJECT_ROOT / "package.json").exists():
            package_json = json.loads((PROJECT_ROOT / "package.json").read_text())
            deps = {
                **package_json.get("dependencies", {}),
                **package_json.get("devDependencies", {}),
            }
            if "vue" in deps and ("vite" in deps or "nuxt" in deps):
                detected_framework = "vue"
            elif "express" in deps:
                detected_framework = "express"
        elif (PROJECT_ROOT / "pyproject.toml").exists():
            pyproject = (PROJECT_ROOT / "pyproject.toml").read_text()
            if "fastapi" in pyproject:
                detected_framework = "fastapi"
        elif (PROJECT_ROOT / "requirements.txt").exists():
            requirements = (PROJECT_ROOT / "requirements.txt").read_text()
            if "fastapi" in requirements:
                detected_framework = "fastapi"

        if detected_framework:
            console.print(f"  [green]✓ Detected: {detected_framework}[/green]")
        else:
            console.print("  [yellow]Could not auto-detect framework[/yellow]")
            console.print("  [dim]Use --framework to specify (nextjs, vue, fastapi, express)[/dim]")
            raise typer.Exit(1)
    else:
        detected_framework = framework.lower()
        console.print(f"  [cyan]Using specified framework: {detected_framework}[/cyan]")

    # Validate framework
    valid_frameworks = ["nextjs", "vue", "fastapi", "express"]
    if detected_framework not in valid_frameworks:
        console.print(f"[red]Invalid framework: {detected_framework}[/red]")
        console.print(f"[dim]Valid options: {', '.join(valid_frameworks)}[/dim]")
        raise typer.Exit(1)

    # Step 2: Generate Dockerfile
    console.print("\n[bold]Step 2: Generate Dockerfile[/bold]")
    dockerfile_template = templates_dir / f"{detected_framework}.dockerfile"

    if not dockerfile_template.exists():
        console.print(f"[red]Template not found: {dockerfile_template}[/red]")
        raise typer.Exit(1)

    dockerfile_dest = PROJECT_ROOT / "Dockerfile"
    if dockerfile_dest.exists():
        console.print("  [yellow]⚠ Dockerfile already exists[/yellow]")
        console.print("  [dim]Overwriting will replace your existing Dockerfile[/dim]")
        if not typer.confirm("  Overwrite existing Dockerfile?", default=False):
            console.print("  [dim]Skipped - keeping existing Dockerfile[/dim]")
        else:
            dockerfile_dest.write_text(dockerfile_template.read_text())
            console.print(f"  [green]✓ Generated Dockerfile ({detected_framework})[/green]")
    else:
        dockerfile_dest.write_text(dockerfile_template.read_text())
        console.print(f"  [green]✓ Generated Dockerfile ({detected_framework})[/green]")

    # Step 3: Generate .dockerignore
    console.print("\n[bold]Step 3: Generate .dockerignore[/bold]")
    dockerignore_content = """# Dependencies
node_modules
__pycache__
*.pyc
venv
.venv

# Build outputs
dist
build
.next
out

# Development
.git
.vk
.claude
*.log
.DS_Store

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode
.idea
*.swp
*.swo

# Testing
coverage
.pytest_cache
.coverage
"""
    dockerignore_dest = PROJECT_ROOT / ".dockerignore"
    if not dockerignore_dest.exists():
        dockerignore_dest.write_text(dockerignore_content)
        console.print("  [green]✓ Generated .dockerignore[/green]")
    else:
        console.print("  [dim].dockerignore already exists[/dim]")

    # Step 4: Environment-specific generation
    if environment == "local":
        console.print("\n[bold]Step 4: Generate docker-compose.yaml[/bold]")

        # Choose template based on project structure
        has_frontend = (PROJECT_ROOT / "frontend").exists() or detected_framework in [
            "nextjs",
            "vue",
        ]
        has_backend = (
            (PROJECT_ROOT / "backend").exists()
            or (PROJECT_ROOT / "api").exists()
            or detected_framework in ["fastapi", "express"]
        )

        if has_frontend and has_backend:
            compose_template = templates_dir / "docker-compose-fullstack.yaml"
        else:
            compose_template = templates_dir / "docker-compose-simple.yaml"

        compose_dest = PROJECT_ROOT / "docker-compose.yaml"

        if compose_dest.exists():
            console.print("  [yellow]⚠ docker-compose.yaml already exists[/yellow]")
            console.print("  [dim]Overwriting will replace your existing configuration[/dim]")
            if not typer.confirm("  Overwrite existing docker-compose.yaml?", default=False):
                console.print("  [dim]Skipped - keeping existing docker-compose.yaml[/dim]")
            else:
                compose_dest.write_text(compose_template.read_text())
                console.print("  [green]✓ Generated docker-compose.yaml[/green]")
        else:
            compose_dest.write_text(compose_template.read_text())
            console.print("  [green]✓ Generated docker-compose.yaml[/green]")

        # Step 5: Start services
        if not no_start:
            console.print("\n[bold]Step 5: Start Services[/bold]")
            try:
                result = subprocess.run(
                    ["docker-compose", "up", "--build", "-d"],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    console.print("  [green]✓ Services started successfully[/green]")

                    # Show service URLs
                    console.print("\n[bold]Access URLs:[/bold]")
                    if detected_framework in ["nextjs", "vue"]:
                        console.print(
                            "  Frontend: [link=http://localhost:3000]http://localhost:3000[/link]"
                        )
                    if detected_framework in ["fastapi", "express"]:
                        console.print(
                            "  API: [link=http://localhost:8000]http://localhost:8000[/link]"
                        )

                    console.print("\n[bold]Useful Commands:[/bold]")
                    console.print("  [cyan]docker-compose logs -f[/cyan]          # View logs")
                    console.print(
                        "  [cyan]docker-compose ps[/cyan]                # Service status"
                    )
                    console.print("  [cyan]docker-compose down[/cyan]              # Stop services")
                    console.print(
                        "  [cyan]docker-compose restart <service>[/cyan] # Restart a service"
                    )
                else:
                    console.print("  [red]Failed to start services:[/red]")
                    console.print(f"  {result.stderr}")
                    raise typer.Exit(1)
            except FileNotFoundError:
                console.print("  [red]docker-compose not found. Install Docker Desktop.[/red]")
                raise typer.Exit(1)
        else:
            console.print(
                "\n[dim]Files generated. Run 'docker-compose up' to start services.[/dim]"
            )

    elif environment == "prod":
        console.print("\n[green]✅ Production Dockerfile generated![/green]")
        console.print("\n[bold]Build and push:[/bold]")
        console.print("  [cyan]docker build -t myapp:latest .[/cyan]")
        console.print("  [cyan]docker tag myapp:latest registry.example.com/myapp:latest[/cyan]")
        console.print("  [cyan]docker push registry.example.com/myapp:latest[/cyan]")

    elif environment == "ci":
        console.print("\n[bold]Step 4: Generate CI/CD Configuration[/bold]")

        # Detect Git platform
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )
            remote_url = result.stdout.strip()

            if "github" in remote_url:
                # Generate GitHub Actions
                workflows_dir = PROJECT_ROOT / ".github" / "workflows"
                workflows_dir.mkdir(parents=True, exist_ok=True)

                ci_workflow = workflows_dir / "docker-build.yml"
                ci_content = """name: Docker Build

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build Docker image
        run: docker build -t ${{ github.repository }}:${{ github.sha }} .

      - name: Run tests in container
        run: |
          docker run --rm ${{ github.repository }}:${{ github.sha }} npm test || true

      - name: Login to Docker Hub
        if: github.ref == 'refs/heads/main'
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Push to Docker Hub
        if: github.ref == 'refs/heads/main'
        run: |
          docker tag ${{ github.repository }}:${{ github.sha }} ${{ github.repository }}:latest
          docker push ${{ github.repository }}:${{ github.sha }}
          docker push ${{ github.repository }}:latest
"""
                ci_workflow.write_text(ci_content)
                console.print("  [green]✓ Generated .github/workflows/docker-build.yml[/green]")

            elif "gitlab" in remote_url:
                # Generate GitLab CI
                gitlab_ci = PROJECT_ROOT / ".gitlab-ci.yml"
                gitlab_content = """stages:
  - build
  - test
  - deploy

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA $CI_REGISTRY_IMAGE:latest
  only:
    - main
    - develop

test:
  stage: test
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker run --rm $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA npm test || true
  only:
    - main
    - develop
"""
                gitlab_ci.write_text(gitlab_content)
                console.print("  [green]✓ Generated .gitlab-ci.yml[/green]")

        except Exception:
            console.print("  [yellow]Could not detect Git platform[/yellow]")

        console.print("\n[green]✅ CI/CD configuration generated![/green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. Add Docker registry credentials to CI secrets")
        console.print("  2. Push to trigger CI pipeline")
        console.print("  3. Review pipeline execution")

    console.print("\n[green]" + "━" * 50 + "[/green]")
    console.print("[bold green]✅ Deployment infrastructure ready![/bold green]")


@app.command()
def idea(
    description: str = typer.Argument(..., help="Natural language app description"),
    framework: Optional[str] = typer.Option(
        None, "--framework", "-f", help="Force specific framework (nextjs, vue, fastapi, express)"
    ),
    output_dir: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output directory (default: current directory)"
    ),
):
    """
    AI-powered project scaffolding from natural language description.

    Takes a natural language app description and generates a complete
    project structure with:
    - Best framework selection (Next.js, Vue, FastAPI, Express)
    - Database schema and setup
    - Authentication scaffolding
    - Basic UI components
    - API endpoints
    - Configuration files

    Examples:
        vk idea "I want a task management app with teams"
        vk idea "Build a blog with user comments" --framework nextjs
        vk idea "Create an API for inventory management" --output ./my-api
    """
    console.print("\n[bold blue]🚀 VibeKit - AI Project Scaffolder[/bold blue]")
    console.print("[blue]" + "━" * 50 + "[/blue]\n")

    from vk.auth import AuthClient
    from vk.client import VKClient

    # Ensure authenticated
    auth = AuthClient()
    if not auth.is_authenticated():
        console.print("[red]Not authenticated. Run 'vk login' first.[/red]")
        raise typer.Exit(1)

    # Determine output directory
    target_dir = Path(output_dir) if output_dir else PROJECT_ROOT
    target_dir = target_dir.resolve()

    console.print(f"[bold]Project Idea:[/bold] {description}")
    if framework:
        console.print(f"[bold]Framework:[/bold] {framework} (forced)")
    console.print(f"[bold]Output Directory:[/bold] {target_dir}\n")

    # Call API to generate project
    client = VKClient()

    with console.status("[bold blue]Analyzing project requirements...[/bold blue]", spinner="dots"):
        try:
            response = client.post(
                "/projects/scaffold",
                json={
                    "description": description,
                    "framework": framework,
                    "output_path": str(target_dir),
                },
            )
        except Exception as e:
            console.print(f"\n[red]Scaffolding failed: {e}[/red]")
            raise typer.Exit(1)

    # Show results
    console.print("\n[green]✅ Project scaffolded successfully![/green]\n")

    project_name = response.get("project_name", "project")
    framework_used = response.get("framework", "unknown")
    files_created = response.get("files_created", [])

    console.print(f"[bold]Project:[/bold] {project_name}")
    console.print(f"[bold]Framework:[/bold] {framework_used}")
    console.print(f"[bold]Files Created:[/bold] {len(files_created)}")

    if files_created:
        console.print("\n[bold]Created Files:[/bold]")
        for file in files_created[:10]:
            console.print(f"  [green]✓[/green] {file}")
        if len(files_created) > 10:
            console.print(f"  [dim]... and {len(files_created) - 10} more[/dim]")

    # Show next steps
    console.print("\n[bold]Next Steps:[/bold]")
    next_steps = response.get("next_steps", [])
    if next_steps:
        for i, step in enumerate(next_steps, 1):
            console.print(f"  {i}. {step}")
    else:
        console.print("  1. Review generated code")
        console.print("  2. Install dependencies")
        console.print("  3. Run development server")

    # Link to VibeKit if desired
    console.print("\n[bold]Want to manage this with VibeKit?[/bold]")
    console.print(f"  Run: [cyan]cd {project_name} && vk init[/cyan]")


# ============================================================================
# MAIN
# ============================================================================


def main():
    """CLI entry point."""
    _check_for_updates()
    app()


if __name__ == "__main__":
    main()

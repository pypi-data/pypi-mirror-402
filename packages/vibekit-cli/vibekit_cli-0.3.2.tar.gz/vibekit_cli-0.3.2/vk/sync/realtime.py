"""
Real-time sync client for VibeKit using Server-Sent Events (SSE).

Connects to vkcli.com SSE endpoint and auto-updates local files
when changes occur on the server (task updates, sprint changes, etc.).

Updates are written to:
- .vk/ for project data (config, sprints, tasks)
- .claude/ for Claude config (rules, patterns, agents)
"""

import asyncio
import json
import signal
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import yaml

try:
    import httpx
except ImportError:
    httpx = None


class HeartbeatPublisher:
    """Publishes periodic heartbeat events during CLI execution."""

    def __init__(
        self,
        project_id: str,
        auth_token: str,
        api_url: str = "https://vkcli.com/api",
        interval: int = 10,
    ):
        """
        Initialize heartbeat publisher.

        Args:
            project_id: Project ID to publish heartbeats for
            auth_token: Authentication token
            api_url: Base URL for the API
            interval: Heartbeat interval in seconds (default: 10)
        """
        self.project_id = project_id
        self.auth_token = auth_token
        self.api_url = api_url
        self.interval = interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._start_time: Optional[datetime] = None
        self._status = "working"
        self._current_agent: Optional[str] = None

    async def start(self) -> None:
        """Start publishing heartbeats."""
        if httpx is None:
            return  # Silently skip if httpx not available

        self._running = True
        self._start_time = datetime.now()
        self._task = asyncio.create_task(self._publish_loop())

    async def stop(self) -> None:
        """Stop publishing heartbeats."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def set_status(self, status: str) -> None:
        """Update current status (working, idle, waiting)."""
        self._status = status

    def set_agent(self, agent_name: Optional[str]) -> None:
        """Set currently active agent."""
        self._current_agent = agent_name

    async def _publish_loop(self) -> None:
        """Background loop that publishes heartbeats."""
        while self._running:
            await self._publish_heartbeat()
            await asyncio.sleep(self.interval)

    async def _publish_heartbeat(self) -> None:
        """Publish a single heartbeat event."""
        if httpx is None:
            return

        elapsed = (
            int((datetime.now() - self._start_time).total_seconds()) if self._start_time else 0
        )

        payload = {
            "event_type": "cli_heartbeat",
            "data": {
                "agent_name": self._current_agent,
                "elapsed_seconds": elapsed,
                "status": self._status,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(
                    f"{self.api_url}/projects/{self.project_id}/events",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                )
        except Exception:
            pass  # Fail silently


async def publish_event(
    project_id: str,
    auth_token: str,
    event_type: str,
    data: Optional[dict] = None,
    task_id: Optional[str] = None,
    api_url: str = "https://vkcli.com/api",
) -> bool:
    """
    Publish a single event to the API.

    Args:
        project_id: Project ID to publish event for
        auth_token: Authentication token
        event_type: Type of event to publish
        data: Event data payload
        task_id: Optional task ID to associate with event
        api_url: Base URL for the API

    Returns:
        True if event was published successfully, False otherwise
    """
    if httpx is None:
        return False

    payload = {
        "event_type": event_type,
        "data": data or {},
    }

    if task_id:
        payload["task_id"] = task_id

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(
                f"{api_url}/projects/{project_id}/events",
                json=payload,
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            return response.status_code == 200
    except Exception:
        return False  # Fail silently


class RealtimeSyncClient:
    """
    Background SSE listener that auto-updates local files.

    Updates project data in .vk/ and Claude config in .claude/.

    Usage:
        client = RealtimeSyncClient(project_root)
        await client.connect(project_id, auth_token)

    Or use the sync helper:
        await watch_project(project_root)
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        api_url: str = "https://vkcli.com/api",
    ):
        """
        Initialize real-time sync client.

        Args:
            project_root: Root directory of the project (default: cwd)
            api_url: Base URL for the API
        """
        self.project_root = project_root or Path.cwd()
        self.vk_dir = self.project_root / ".vk"  # Project data
        self.claude_dir = self.project_root / ".claude"  # Claude config
        self.api_url = api_url
        self._running = False
        self._reconnect_delay = 1  # seconds, exponential backoff
        self._max_reconnect_delay = 60
        self._handlers: dict[str, list[Callable]] = {}

    def on(self, event_type: str, handler: Callable) -> None:
        """
        Register event handler.

        Args:
            event_type: Event type to handle (task.updated, sprint.changed, etc.)
            handler: Async function to call with event data
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def connect(
        self,
        project_id: str,
        auth_token: str,
        on_connected: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ) -> None:
        """
        Connect to SSE endpoint and start listening.

        Args:
            project_id: Project ID to subscribe to
            auth_token: Authentication token
            on_connected: Callback when connected
            on_error: Callback on errors
        """
        if httpx is None:
            raise ImportError(
                "httpx is required for real-time sync. Install with: pip install httpx"
            )

        self._running = True
        url = f"{self.api_url}/projects/{project_id}/events"
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Accept": "text/event-stream",
        }

        while self._running:
            try:
                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream("GET", url, headers=headers) as response:
                        if response.status_code != 200:
                            if on_error:
                                await on_error(f"Connection failed: {response.status_code}")
                            await self._backoff()
                            continue

                        # Reset backoff on successful connection
                        self._reconnect_delay = 1

                        if on_connected:
                            await on_connected()

                        # Process SSE stream
                        await self._process_stream(response)

            except httpx.TimeoutException:
                # Normal timeout, reconnect
                continue
            except httpx.ConnectError as e:
                if on_error:
                    await on_error(f"Connection error: {e}")
                await self._backoff()
            except Exception as e:
                if on_error:
                    await on_error(f"Error: {e}")
                await self._backoff()

    async def _process_stream(self, response) -> None:
        """Process incoming SSE events from stream."""
        event_type = None
        event_data = ""

        async for line in response.aiter_lines():
            if not self._running:
                break

            line = line.strip()

            if not line:
                # Empty line = end of event
                if event_type and event_data:
                    await self._handle_event(event_type, event_data)
                event_type = None
                event_data = ""
                continue

            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                event_data = line[5:].strip()
            elif line.startswith(":"):
                # Comment/keepalive, ignore
                pass

    async def _handle_event(self, event_type: str, event_data: str) -> None:
        """Handle a single SSE event."""
        try:
            data = json.loads(event_data)
        except json.JSONDecodeError:
            data = {"raw": event_data}

        # Call registered handlers
        handlers = self._handlers.get(event_type, [])
        handlers.extend(self._handlers.get("*", []))  # Wildcard handlers

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, data)
                else:
                    handler(event_type, data)
            except Exception as e:
                print(f"Handler error for {event_type}: {e}")

        # Built-in handlers for local file updates
        await self._update_local_files(event_type, data)

    async def _update_local_files(self, event_type: str, data: dict) -> None:
        """Update local files based on event (project data to .vk/, Claude config to .claude/)."""
        if event_type == "task.updated":
            await self._update_task(data)
        elif event_type == "task.created":
            await self._add_task(data)
        elif event_type == "sprint.changed":
            await self._update_sprint(data)
        elif event_type == "content.updated":
            await self._update_content(data)

    async def _update_task(self, data: dict) -> None:
        """Update task status in local sprint file."""
        task_id = data.get("task_id")
        new_status = data.get("status")

        if not task_id or not new_status:
            return

        sprint_file = self.vk_dir / "sprints" / "current.yaml"
        if not sprint_file.exists():
            return

        try:
            with open(sprint_file) as f:
                sprint = yaml.safe_load(f) or {}

            # Find and update task
            for req in sprint.get("requirements", []):
                for task in req.get("tasks", []):
                    if task.get("task_id") == task_id:
                        task["status"] = new_status
                        if "updated_at" in data:
                            task["updated_at"] = data["updated_at"]
                        break

            # Write back
            with open(sprint_file, "w") as f:
                yaml.safe_dump(sprint, f, default_flow_style=False, sort_keys=False)

        except Exception as e:
            print(f"Error updating task: {e}")

    async def _add_task(self, data: dict) -> None:
        """Add new task to local sprint file."""
        # For new tasks, trigger a full pull for consistency
        # This is a simplified approach; could be enhanced to surgically add
        pass

    async def _update_sprint(self, data: dict) -> None:
        """Update sprint info in local files."""
        sprint_file = self.vk_dir / "sprints" / "current.yaml"
        if not sprint_file.exists():
            return

        try:
            with open(sprint_file) as f:
                sprint = yaml.safe_load(f) or {}

            # Update sprint-level fields
            for key in ["name", "goal", "status", "start_date", "end_date"]:
                if key in data:
                    sprint[key] = data[key]

            with open(sprint_file, "w") as f:
                yaml.safe_dump(sprint, f, default_flow_style=False, sort_keys=False)

        except Exception as e:
            print(f"Error updating sprint: {e}")

    async def _update_content(self, data: dict) -> None:
        """Handle content update notification."""
        content_type = data.get("content_type")
        name = data.get("name")

        if content_type and name:
            # Log the update; user can run 'vk pull' to get latest
            print(f"[sync] System content updated: {content_type}/{name}")

    async def _backoff(self) -> None:
        """Wait with exponential backoff before reconnecting."""
        await asyncio.sleep(self._reconnect_delay)
        self._reconnect_delay = min(
            self._reconnect_delay * 2,
            self._max_reconnect_delay,
        )

    def stop(self) -> None:
        """Stop the sync client."""
        self._running = False


async def watch_project(
    project_root: Optional[Path] = None,
    verbose: bool = True,
    enable_heartbeat: bool = False,
) -> None:
    """
    Watch a project for real-time updates.

    Convenience function that:
    1. Loads project config from .vk/config.yaml
    2. Gets auth token from keyring
    3. Connects to SSE and prints updates
    4. Optionally publishes heartbeats during watch

    Args:
        project_root: Project root directory
        verbose: Print events to console
        enable_heartbeat: Enable heartbeat publishing during watch
    """
    project_root = project_root or Path.cwd()
    vk_dir = project_root / ".vk"
    config_file = vk_dir / "config.yaml"

    if not config_file.exists():
        raise FileNotFoundError("Project not initialized. Run 'vk init' first.")

    # Load project ID
    with open(config_file) as f:
        config = yaml.safe_load(f)
    project_id = config.get("project_id")

    if not project_id:
        raise ValueError("No project_id in config")

    # Get auth token
    try:
        from vk.auth import AuthClient

        auth = AuthClient()
        token = auth.get_token()
    except ImportError:
        raise ImportError("Auth module required for real-time sync")

    if not token:
        raise ValueError("Not authenticated. Run 'vk login' first.")

    # Create client
    client = RealtimeSyncClient(project_root)

    # Create heartbeat publisher if enabled
    heartbeat: Optional[HeartbeatPublisher] = None
    if enable_heartbeat:
        heartbeat = HeartbeatPublisher(
            project_id=project_id,
            auth_token=token,
            api_url="https://vkcli.com/api",
        )
        heartbeat.set_status("watching")
        await heartbeat.start()

    # Setup handlers if verbose
    if verbose:

        async def log_event(event_type: str, data: dict):
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {event_type}: {json.dumps(data, indent=2)}")

        client.on("*", log_event)

    # Handle graceful shutdown
    loop = asyncio.get_event_loop()

    def shutdown():
        print("\n[sync] Stopping...")
        client.stop()
        if heartbeat:
            asyncio.create_task(heartbeat.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)

    # Connect and run
    async def on_connected():
        print(f"[sync] Connected to project {project_id}")
        print("[sync] Watching for updates... (Ctrl+C to stop)")

    async def on_error(msg: str):
        print(f"[sync] {msg}")

    try:
        await client.connect(
            project_id=project_id,
            auth_token=token,
            on_connected=on_connected,
            on_error=on_error,
        )
    finally:
        if heartbeat:
            await heartbeat.stop()

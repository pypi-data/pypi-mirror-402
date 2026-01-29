"""
Main API client for VibeKit SDK.

Provides authenticated HTTP client for all SaaS backend operations.
"""

from __future__ import annotations

from typing import Any, Optional, TypeVar

import httpx
from pydantic import BaseModel

from vk.auth import AuthClient, AuthConfig
from vk.client.exceptions import (
    AuthenticationError,
    NotFoundError,
    OfflineError,
    RateLimitError,
    ServerError,
    ValidationError,
    VKClientError,
)

T = TypeVar("T", bound=BaseModel)


class ProjectsAPI:
    """Projects API endpoints."""

    def __init__(self, client: VKClient):
        self._client = client

    def list(self) -> list[dict]:
        """List all projects for the authenticated user."""
        return self._client.get("/projects")

    def get(self, project_id: str) -> dict:
        """Get a specific project."""
        return self._client.get(f"/projects/{project_id}")

    def get_by_slug(self, slug: str) -> dict:
        """
        Get a project by its GitHub-style slug (owner/name).

        Args:
            slug: Project slug like "johndoe/my-project"

        Returns:
            Project data dict with id, name, slug, etc.
        """
        if "/" not in slug:
            raise ValueError(f"Invalid slug format: {slug}. Expected 'owner/project-name'")
        owner, name = slug.split("/", 1)
        return self._client.get(f"/projects/by-slug/{owner}/{name}")

    def create(
        self,
        name: str,
        path: Optional[str] = None,
        description: Optional[str] = None,
        languages: Optional[list[str]] = None,
    ) -> dict:
        """Create a new project with auto-detected metadata."""
        data = {"name": name}
        if path:
            data["path"] = path
        if description:
            data["description"] = description
        if languages:
            data["languages"] = languages
        return self._client.post("/projects", json=data)

    def update(self, project_id: str, **kwargs) -> dict:
        """
        Update project settings.

        Supports: name, description, git_remote_url, languages, frameworks, databases
        """
        # Filter out None values
        data = {k: v for k, v in kwargs.items() if v is not None}
        return self._client.patch(f"/projects/{project_id}", json=data)

    def link(self, project_id: str, local_path: str) -> dict:
        """Link a local directory to a project."""
        return self._client.post(f"/projects/{project_id}/link", json={"local_path": local_path})


class SprintsAPI:
    """Sprints API endpoints."""

    def __init__(self, client: VKClient):
        self._client = client

    def list(self, project_id: str) -> list[dict]:
        """List all sprints for a project."""
        return self._client.get(f"/projects/{project_id}/sprints")

    def get_current(self, project_id: str) -> Optional[dict]:
        """Get the current active sprint."""
        return self._client.get(f"/projects/{project_id}/sprints/current")

    def create(self, project_id: str, name: str, goal: Optional[str] = None) -> dict:
        """Create a new sprint."""
        return self._client.post(
            f"/projects/{project_id}/sprints", json={"name": name, "goal": goal}
        )

    def start(self, project_id: str, sprint_id: str) -> dict:
        """Start a sprint."""
        return self._client.post(f"/projects/{project_id}/sprints/{sprint_id}/start")

    def complete(self, project_id: str, sprint_id: str) -> dict:
        """Complete a sprint."""
        return self._client.post(f"/projects/{project_id}/sprints/{sprint_id}/complete")


class RequirementsAPI:
    """Requirements API endpoints."""

    def __init__(self, client: VKClient):
        self._client = client

    def list(self, project_id: str, status: Optional[str] = None) -> list[dict]:
        """List requirements for a project."""
        params = {"status": status} if status else {}
        return self._client.get(f"/projects/{project_id}/requirements", params=params)

    def create(
        self, project_id: str, type: str, description: str, priority: str = "medium"
    ) -> dict:
        """Create a new requirement."""
        return self._client.post(
            f"/projects/{project_id}/requirements",
            json={
                "type": type,
                "description": description,
                "priority": priority,
            },
        )

    def get(self, project_id: str, requirement_id: str) -> dict:
        """Get a specific requirement."""
        return self._client.get(f"/projects/{project_id}/requirements/{requirement_id}")


class TasksAPI:
    """Tasks API endpoints."""

    def __init__(self, client: VKClient):
        self._client = client

    def list(self, project_id: str, sprint_id: Optional[str] = None) -> list[dict]:
        """List tasks for a project or sprint."""
        params = {"sprint_id": sprint_id} if sprint_id else {}
        return self._client.get(f"/projects/{project_id}/tasks", params=params)

    def create(
        self,
        project_id: str,
        title: str,
        requirement_id: Optional[str] = None,
        sprint_id: Optional[str] = None,
        estimate: Optional[int] = None,
    ) -> dict:
        """Create a new task."""
        return self._client.post(
            f"/projects/{project_id}/tasks",
            json={
                "title": title,
                "requirement_id": requirement_id,
                "sprint_id": sprint_id,
                "estimate": estimate,
            },
        )

    def update_status(self, project_id: str, task_id: str, status: str) -> dict:
        """Update task status."""
        return self._client.patch(
            f"/projects/{project_id}/tasks/{task_id}", json={"status": status}
        )


class VKClient:
    """
    Main API client for VibeKit SDK.

    Provides authenticated access to all SaaS backend endpoints.
    Handles token refresh and error mapping automatically.

    Usage:
        client = VKClient()

        # Must be authenticated first
        if not client.is_authenticated():
            client.login()

        # Then use the APIs
        projects = client.projects.list()
    """

    def __init__(
        self,
        config: Optional[AuthConfig] = None,
        project_id: Optional[str] = None,
    ):
        """
        Initialize the VK client.

        Args:
            config: Optional auth configuration
            project_id: Optional default project ID
        """
        self.auth = AuthClient(config)
        self.config = self.auth.config
        self.project_id = project_id
        self._http_client: Optional[httpx.Client] = None

        # API namespaces
        self.projects = ProjectsAPI(self)
        self.sprints = SprintsAPI(self)
        self.requirements = RequirementsAPI(self)
        self.tasks = TasksAPI(self)

    @property
    def http_client(self) -> httpx.Client:
        """Get or create authenticated HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.Client(
                base_url=self.config.api_base_url,
                timeout=30.0,
            )
        return self._http_client

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.auth.is_authenticated()

    def login(self) -> bool:
        """Perform OAuth login."""
        return self.auth.login()

    def logout(self) -> None:
        """Log out and clear credentials."""
        self.auth.logout()

    def _get_headers(self) -> dict:
        """Get request headers with authentication."""
        token = self.auth.get_token()
        if not token:
            raise AuthenticationError()

        return {
            "Authorization": token.authorization_header,
            "Content-Type": "application/json",
            "User-Agent": "vibekit-cli/0.2.4",
        }

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response and map errors."""
        if response.status_code == 401:
            raise AuthenticationError()
        elif response.status_code == 404:
            raise NotFoundError()
        elif response.status_code == 422:
            raise ValidationError(response.json().get("detail"))
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(int(retry_after) if retry_after else None)
        elif response.status_code >= 500:
            raise ServerError()
        elif response.status_code >= 400:
            raise VKClientError(
                response.json().get("detail", "Unknown error"),
                status_code=response.status_code,
            )

        if response.status_code == 204:
            return None

        return response.json()

    def get(self, path: str, params: Optional[dict] = None) -> Any:
        """Make GET request."""
        try:
            response = self.http_client.get(
                path,
                headers=self._get_headers(),
                params=params,
            )
            return self._handle_response(response)
        except httpx.ConnectError:
            raise OfflineError()

    def post(self, path: str, json: Optional[dict] = None) -> Any:
        """Make POST request."""
        try:
            response = self.http_client.post(
                path,
                headers=self._get_headers(),
                json=json,
            )
            return self._handle_response(response)
        except httpx.ConnectError:
            raise OfflineError()

    def patch(self, path: str, json: Optional[dict] = None) -> Any:
        """Make PATCH request."""
        try:
            response = self.http_client.patch(
                path,
                headers=self._get_headers(),
                json=json,
            )
            return self._handle_response(response)
        except httpx.ConnectError:
            raise OfflineError()

    def delete(self, path: str) -> Any:
        """Make DELETE request."""
        try:
            response = self.http_client.delete(
                path,
                headers=self._get_headers(),
            )
            return self._handle_response(response)
        except httpx.ConnectError:
            raise OfflineError()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit."""
        if self._http_client:
            self._http_client.close()

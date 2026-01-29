"""
Auth client for VibeKit SDK.

Handles device flow authentication with the vkcli.com SaaS platform.
"""

import time
import webbrowser
from typing import Callable, Optional

import httpx
from rich.console import Console

from vk.auth.config import AuthConfig, get_config
from vk.auth.tokens import TokenData, TokenManager

console = Console()


class AuthClient:
    """
    Client for authenticating with vkcli.com.

    Handles the device flow authentication:
    1. Requests device code from API
    2. Displays user code and opens verification URL in browser
    3. Polls API for authorization status
    4. Receives and stores token when authorized
    """

    def __init__(self, config: Optional[AuthConfig] = None):
        """
        Initialize auth client.

        Args:
            config: Optional auth configuration override
        """
        self.config = config or get_config()
        self.token_manager = TokenManager(self.config.config_dir)
        self._http_client: Optional[httpx.Client] = None

    @property
    def http_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.Client(
                base_url=self.config.api_base_url,
                timeout=30.0,
            )
        return self._http_client

    def is_authenticated(self) -> bool:
        """Check if user is authenticated with valid token."""
        return self.token_manager.has_valid_token(self.config.token_refresh_buffer_seconds)

    def get_token(self) -> Optional[TokenData]:
        """
        Get current valid token, refreshing if needed.

        Returns:
            TokenData if authenticated, None otherwise
        """
        token = self.token_manager.get_token()

        if token is None:
            return None

        # Refresh if expired or expiring soon
        if token.expires_soon(self.config.token_refresh_buffer_seconds):
            if token.refresh_token:
                try:
                    token = self._refresh_token(token.refresh_token)
                    self.token_manager.save_token(token)
                except Exception:
                    return None
            else:
                return None

        return token

    def login(self, callback: Optional[Callable[[], None]] = None) -> bool:
        """
        Perform device flow login.

        Initiates device flow, displays user code, opens browser,
        and polls for authorization.

        Args:
            callback: Optional callback to run after successful login

        Returns:
            True if login successful
        """
        console.print("\n[bold blue]Authenticating with vkcli.com...[/bold blue]")

        try:
            # Step 1: Initiate device flow
            response = self.http_client.post("/auth/device/code")
            response.raise_for_status()
            device_data = response.json()

            device_code = device_data["device_code"]
            user_code = device_data["user_code"]
            verification_uri = device_data["verification_uri"]
            expires_in = device_data["expires_in"]
            interval = device_data.get("interval", 5)

            # Step 2: Display user code and open browser
            console.print(
                "\n[bold yellow]Please confirm the following code in your browser:[/bold yellow]"
            )
            console.print(f"\n[bold green]    {user_code}[/bold green]\n")
            console.print(f"Opening browser to: {verification_uri}")
            console.print("[dim]If browser doesn't open, visit manually[/dim]\n")

            webbrowser.open(verification_uri)

            # Step 3: Poll for authorization
            console.print("[dim]Waiting for authorization...[/dim]")
            start_time = time.time()
            poll_count = 0

            while True:
                # Check timeout
                if time.time() - start_time > expires_in:
                    console.print("[red]Authentication timed out. Please try again.[/red]")
                    return False

                # Wait before polling
                time.sleep(interval)
                poll_count += 1

                # Show progress indicator
                if poll_count % 6 == 0:  # Every 30 seconds
                    elapsed = int(time.time() - start_time)
                    remaining = expires_in - elapsed
                    console.print(f"[dim]Still waiting... ({remaining}s remaining)[/dim]")

                # Poll for token
                try:
                    token_response = self.http_client.post(
                        "/auth/device/token", json={"device_code": device_code}
                    )

                    if token_response.status_code == 200:
                        # Success! Got the token
                        token_data = token_response.json()
                        # Always use "Bearer" (API may return lowercase "bearer")
                        token = TokenData(
                            access_token=token_data["access_token"],
                            refresh_token=None,  # CLI tokens don't have refresh tokens
                            token_type="Bearer",
                            expires_at=time.time()
                            + token_data.get("expires_in", 30 * 24 * 60 * 60),
                            user_id=token_data["user"]["id"],
                            email=token_data["user"].get("email"),
                        )
                        self.token_manager.save_token(token)

                        console.print(
                            f"\n[green]Successfully logged in as {token.email or 'user'}[/green]"
                        )

                        if callback:
                            callback()

                        return True

                    elif token_response.status_code == 400:
                        # Check error type
                        error_data = token_response.json()
                        error_detail = error_data.get("detail", "")

                        if error_detail == "authorization_pending":
                            # Still waiting, continue polling
                            continue
                        else:
                            # Other error
                            console.print(f"[red]Authentication failed: {error_detail}[/red]")
                            return False

                    elif token_response.status_code == 429:
                        # Rate limited - back off and retry
                        retry_after = int(token_response.headers.get("Retry-After", interval * 2))
                        console.print(f"[dim]Rate limited, waiting {retry_after}s...[/dim]")
                        time.sleep(retry_after)
                        continue

                    else:
                        # Unexpected status code
                        console.print(
                            f"[red]Unexpected response: {token_response.status_code}[/red]"
                        )
                        return False

                except httpx.HTTPError as e:
                    console.print(f"[red]Network error during polling: {e}[/red]")
                    return False

        except httpx.HTTPError as e:
            console.print(f"[red]Failed to initiate authentication: {e}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Authentication error: {e}[/red]")
            return False

    def logout(self) -> None:
        """Log out and clear stored credentials."""
        self.token_manager.delete_token()
        console.print("[green]Successfully logged out[/green]")

    def _refresh_token(self, refresh_token: str) -> TokenData:
        """
        Refresh access token using refresh token.

        Note: CLI tokens are long-lived (30 days) and don't support refresh.
        This method is kept for compatibility but shouldn't be called.
        """
        # CLI tokens don't have refresh tokens, user needs to re-login
        raise NotImplementedError("CLI tokens must be refreshed by logging in again")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit."""
        if self._http_client:
            self._http_client.close()

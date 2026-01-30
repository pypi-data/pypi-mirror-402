"""
Authentication commands for Xenfra CLI.
"""

import base64
import hashlib
import secrets
import urllib.parse
import webbrowser
from http.server import HTTPServer

import click
import httpx
import keyring
from rich.console import Console
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..utils.auth import (
    API_BASE_URL,
    CLI_CLIENT_ID,
    CLI_LOCAL_SERVER_END_PORT,
    CLI_LOCAL_SERVER_START_PORT,
    CLI_REDIRECT_PATH,
    SERVICE_ID,
    AuthCallbackHandler,
    clear_tokens,
    get_auth_token,
)

console = Console()

# HTTP request timeout (30 seconds)
HTTP_TIMEOUT = 30.0


@click.group()
def auth():
    """Authentication commands (login, logout, whoami)."""
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    reraise=True,
)
def _exchange_code_for_tokens_with_retry(code: str, code_verifier: str, redirect_uri: str) -> dict:
    """
    Exchange authorization code for tokens with retry logic.

    Returns token data dictionary.
    """
    with httpx.Client(timeout=HTTP_TIMEOUT) as client:
        response = client.post(
            f"{API_BASE_URL}/auth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": CLI_CLIENT_ID,
                "code": code,
                "code_verifier": code_verifier,
                "redirect_uri": redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()

        # Safe JSON parsing with content-type check
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            raise ValueError(f"Expected JSON response, got {content_type}")

        try:
            token_data = response.json()
        except (ValueError, TypeError) as e:
            raise ValueError(f"Failed to parse JSON response: {e}")

        return token_data


@auth.command()
def login():
    """Login to Xenfra using Device Authorization Flow (like GitHub CLI, Claude Code)."""
    from .auth_device import device_login
    device_login()

    # Removed old PKCE flow - now using Device Authorization Flow


@auth.command()
def logout():
    """Logout and clear stored tokens."""
    try:
        clear_tokens()
        console.print("[bold green]Logged out successfully.[/bold green]")
    except Exception as e:
        console.print(f"[yellow]Warning: Error during logout: {e}[/yellow]")
        console.print("[dim]Tokens may still be stored in keyring.[/dim]")


@auth.command()
@click.option("--token", is_flag=True, help="Show access token")
def whoami(token):
    """Show current authenticated user."""
    access_token = get_auth_token()

    if not access_token:
        console.print("[bold red]Not logged in. Run 'xenfra login' first.[/bold red]")
        return

    try:
        import base64
        import json

        # Manually decode JWT payload without verification
        # JWT format: header.payload.signature
        parts = access_token.split(".")
        if len(parts) != 3:
            console.print("[bold red]Invalid token format[/bold red]")
            return

        # Decode payload (second part)
        payload_b64 = parts[1]
        # Add padding if needed
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding

        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        claims = json.loads(payload_bytes)

        console.print("[bold green]Logged in as:[/bold green]")
        console.print(f"  Email: {claims.get('sub', 'N/A')}")
        console.print(f"  User ID: {claims.get('user_id', 'N/A')}")

        if token:
            console.print(f"\n[dim]Access Token:[/dim]\n{access_token}")
    except Exception as e:
        console.print(f"[bold red]Failed to decode token: {e}[/bold red]")

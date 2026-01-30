"""
Device Authorization Flow for Xenfra CLI.
Modern OAuth flow used by GitHub CLI, AWS CLI, Claude Code, etc.
"""

import time
import webbrowser
from urllib.parse import urlencode

import click
import httpx
import keyring
from rich.console import Console
from rich.panel import Panel

from ..utils.auth import API_BASE_URL, CLI_CLIENT_ID, HTTP_TIMEOUT, SERVICE_ID

console = Console()


def device_login():
    """
    Device Authorization Flow (OAuth 2.0 Device Grant).

    Flow:
    1. CLI calls /auth/device/authorize to get device_code and user_code
    2. User visits https://www.xenfra.tech/activate and enters user_code
    3. CLI polls /auth/device/token until user authorizes
    4. CLI receives access_token and stores it
    """
    try:
        # Step 1: Request device code
        console.print("[cyan]Initiating device authorization...[/cyan]")

        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            response = client.post(
                f"{API_BASE_URL}/auth/device/authorize",
                data={
                    "client_id": CLI_CLIENT_ID,
                    "scope": "openid profile",
                },
            )
            response.raise_for_status()
            device_data = response.json()

        device_code = device_data["device_code"]
        user_code = device_data["user_code"]
        verification_uri = device_data["verification_uri"]
        verification_uri_complete = device_data.get("verification_uri_complete")
        expires_in = device_data["expires_in"]
        interval = device_data.get("interval", 5)

        # Step 2: Show user code and open browser
        console.print()
        console.print(
            Panel.fit(
                f"[bold white]{user_code}[/bold white]",
                title="[bold green]Your Activation Code[/bold green]",
                border_style="green",
            )
        )
        console.print()
        console.print(f"[bold]Visit:[/bold] [link]{verification_uri}[/link]")
        console.print(f"[bold]Enter code:[/bold] [cyan]{user_code}[/cyan]")
        console.print()

        # Open browser automatically
        try:
            url_to_open = verification_uri_complete or verification_uri
            webbrowser.open(url_to_open)
            console.print("[dim]Opening browser...[/dim]")
        except Exception:
            console.print("[yellow]Could not open browser automatically. Please visit the URL above.[/yellow]")

        # Step 3: Poll for authorization
        console.print()
        console.print("[cyan]Waiting for authorization...[/cyan]")
        console.print("[dim](Press Ctrl+C to cancel)[/dim]")
        console.print()

        start_time = time.time()
        poll_count = 0

        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            while True:
                # Check timeout
                if time.time() - start_time > expires_in:
                    console.print("[bold red]✗ Authorization timed out. Please try again.[/bold red]")
                    return False

                # Poll the token endpoint
                try:
                    response = client.post(
                        f"{API_BASE_URL}/auth/device/token",
                        data={
                            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                            "device_code": device_code,
                            "client_id": CLI_CLIENT_ID,
                        },
                    )

                    if response.status_code == 200:
                        # Success! User authorized
                        token_data = response.json()
                        access_token = token_data["access_token"]
                        refresh_token = token_data.get("refresh_token")

                        # Store tokens (keyring or file fallback)
                        try:
                            keyring.set_password(SERVICE_ID, "access_token", access_token)
                            if refresh_token:
                                keyring.set_password(SERVICE_ID, "refresh_token", refresh_token)
                        except keyring.errors.KeyringError as e:
                            console.print(f"[dim]Keyring unavailable, using file storage: {e}[/dim]")
                            # Fallback to file storage
                            from ..utils.auth import _set_token_to_file
                            _set_token_to_file("access_token", access_token)
                            if refresh_token:
                                _set_token_to_file("refresh_token", refresh_token)

                        console.print()
                        console.print("[bold green]✓ Successfully authenticated![/bold green]")
                        console.print()
                        return True

                    elif response.status_code == 400:
                        error_data = response.json()
                        error = error_data.get("error", "unknown_error")

                        if error == "authorization_pending":
                            # Still waiting for user to authorize
                            poll_count += 1
                            if poll_count % 6 == 0:  # Every 30 seconds
                                console.print("[dim]Still waiting...[/dim]")
                            time.sleep(interval)
                            continue

                        elif error == "slow_down":
                            # We're polling too fast
                            interval += 5
                            time.sleep(interval)
                            continue

                        else:
                            # Other error
                            error_desc = error_data.get("error_description", error)
                            console.print(f"[bold red]✗ Authorization failed: {error_desc}[/bold red]")
                            return False

                    else:
                        console.print(f"[bold red]✗ Unexpected response: {response.status_code}[/bold red]")
                        return False

                except httpx.HTTPError as e:
                    console.print(f"[bold red]✗ Network error: {e}[/bold red]")
                    return False

    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Authorization cancelled.[/yellow]")
        return False
    except Exception as e:
        console.print(f"[bold red]✗ Error: {e}[/bold red]")
        return False

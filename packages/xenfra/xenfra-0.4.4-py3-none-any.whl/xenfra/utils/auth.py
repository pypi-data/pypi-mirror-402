"""
Authentication utilities for Xenfra CLI.
Handles OAuth2 PKCE flow and token management.
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
import keyring
from rich.console import Console
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .security import validate_and_get_api_url

console = Console()

# Get validated API URL (includes all security checks)
API_BASE_URL = validate_and_get_api_url()
SERVICE_ID = "xenfra"

# Fallback file-based token storage (for Windows if keyring fails)
TOKEN_FILE = Path.home() / ".xenfra" / "tokens.json"

# CLI OAuth2 Configuration
CLI_CLIENT_ID = "xenfra-cli"
CLI_REDIRECT_PATH = "/auth/callback"
CLI_LOCAL_SERVER_START_PORT = 8001
CLI_LOCAL_SERVER_END_PORT = 8005

# HTTP request timeout (30 seconds)
HTTP_TIMEOUT = 30.0

# Global storage for OAuth callback data
oauth_data = {"code": None, "state": None, "error": None}


class AuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth redirect callback."""

    def do_GET(self):
        global oauth_data
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        query_params = parse_qs(urlparse(self.path).query)

        if "code" in query_params:
            oauth_data["code"] = query_params["code"][0]
            oauth_data["state"] = query_params["state"][0] if "state" in query_params else None
            self.wfile.write(
                b"<html><body><h1>Authentication successful!</h1><p>You can close this window.</p></body></html>"
            )
        elif "error" in query_params:
            oauth_data["error"] = query_params["error"][0]
            self.wfile.write(
                f"<html><body><h1>Authentication failed!</h1><p>Error: {oauth_data['error']}</p></body></html>".encode()
            )
        else:
            self.wfile.write(
                b"<html><body><h1>Authentication callback received.</h1><p>Waiting for code...</p></body></html>"
            )

        # Shut down the server after processing
        self.server.shutdown()  # type: ignore


def run_local_oauth_server(port: int, redirect_path: str):
    """Start a local HTTP server to capture the OAuth redirect."""
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, AuthCallbackHandler)
    httpd.timeout = 30  # seconds
    console.print(
        f"[dim]Listening for OAuth redirect on http://localhost:{port}{redirect_path}...[/dim]"
    )

    # Store the server instance in the handler for shutdown
    AuthCallbackHandler.server = httpd  # type: ignore

    # Handle a single request (blocking call)
    httpd.handle_request()
    console.print("[dim]Local OAuth server shut down.[/dim]")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    reraise=True,
)
def _refresh_token_with_retry(refresh_token: str) -> dict:
    """
    Refresh access token with retry logic.

    Returns token data dictionary.
    """
    with httpx.Client(timeout=HTTP_TIMEOUT) as client:
        response = client.post(
            f"{API_BASE_URL}/auth/refresh",
            data={"refresh_token": refresh_token, "client_id": CLI_CLIENT_ID},
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


def _get_encryption_key() -> bytes:
    """
    Get or create encryption key for file-based token storage.

    Uses machine-specific identifier to generate key (not perfect but better than plaintext).
    """
    import platform
    import hashlib

    # Use machine ID + username as seed (available on Windows/Linux/Mac)
    machine_id = platform.node() + os.getlogin()
    key = hashlib.sha256(machine_id.encode()).digest()[:32]  # 32 bytes for Fernet
    return key


def _get_token_from_file(key: str) -> str | None:
    """Fallback: Get token from file storage (for Windows if keyring fails)."""
    try:
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, "rb") as f:
                encrypted_data = f.read()

            # Decrypt the file contents
            from cryptography.fernet import Fernet
            import base64

            fernet_key = base64.urlsafe_b64encode(_get_encryption_key())
            cipher = Fernet(fernet_key)
            decrypted_data = cipher.decrypt(encrypted_data)
            tokens = json.loads(decrypted_data.decode())
            return tokens.get(key)
    except Exception:
        # If decryption fails, try reading as plaintext (for backward compatibility)
        try:
            with open(TOKEN_FILE, "r") as f:
                tokens = json.load(f)
                return tokens.get(key)
        except Exception:
            pass
    return None


def _set_token_to_file(key: str, value: str):
    """Fallback: Save token to file storage (encrypted for Windows if keyring fails)."""
    try:
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Load existing tokens (try encrypted first, then plaintext)
        tokens = {}
        if TOKEN_FILE.exists():
            try:
                with open(TOKEN_FILE, "rb") as f:
                    encrypted_data = f.read()
                from cryptography.fernet import Fernet
                import base64

                fernet_key = base64.urlsafe_b64encode(_get_encryption_key())
                cipher = Fernet(fernet_key)
                decrypted_data = cipher.decrypt(encrypted_data)
                tokens = json.loads(decrypted_data.decode())
            except Exception:
                # Fallback to plaintext for backward compatibility
                try:
                    with open(TOKEN_FILE, "r") as f:
                        tokens = json.load(f)
                except Exception:
                    tokens = {}

        # Update token
        tokens[key] = value

        # Encrypt and save
        from cryptography.fernet import Fernet
        import base64

        fernet_key = base64.urlsafe_b64encode(_get_encryption_key())
        cipher = Fernet(fernet_key)
        encrypted_data = cipher.encrypt(json.dumps(tokens).encode())

        with open(TOKEN_FILE, "wb") as f:
            f.write(encrypted_data)

        # Set file permissions (owner read/write only) - works on Unix-like systems
        if os.name != "nt":  # Not Windows
            TOKEN_FILE.chmod(0o600)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not save token to file: {e}[/yellow]")


def _delete_token_from_file(key: str):
    """Fallback: Delete token from file storage."""
    try:
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, "r") as f:
                tokens = json.load(f)

            if key in tokens:
                del tokens[key]

                if tokens:
                    with open(TOKEN_FILE, "w") as f:
                        json.dump(tokens, f)
                else:
                    TOKEN_FILE.unlink()  # Delete file if empty
    except Exception:
        pass


def get_auth_token() -> str | None:
    """
    Retrieve a valid access token, refreshing it if necessary.

    Returns:
        Valid access token or None if not authenticated
    """
    # Try keyring first
    access_token = None
    refresh_token = None
    use_file_fallback = False

    try:
        access_token = keyring.get_password(SERVICE_ID, "access_token")
        refresh_token = keyring.get_password(SERVICE_ID, "refresh_token")
        if os.getenv("XENFRA_DEBUG") == "1":
            console.print("[dim]DEBUG: Token retrieved from keyring[/dim]")
    except keyring.errors.KeyringError as e:
        if os.getenv("XENFRA_DEBUG") == "1":
            console.print(f"[dim]DEBUG: Keyring unavailable, using file storage: {e}[/dim]")
        use_file_fallback = True
        access_token = _get_token_from_file("access_token")
        refresh_token = _get_token_from_file("refresh_token")

    if not access_token:
        return None

    # Check if access token is expired
    # Manually decode JWT payload to check expiration without verifying signature
    try:
        import base64
        import json
        
        # JWT format: header.payload.signature
        parts = access_token.split(".")
        if len(parts) != 3:
            claims = None
        else:
            # Decode payload (second part)
            payload_b64 = parts[1]
            # Add padding if needed
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            claims = json.loads(payload_bytes)
            
            # Check expiration manually
            exp = claims.get("exp")
            if exp:
                import time
                if time.time() >= exp:
                    claims = None  # Token expired
    except Exception:
        claims = None

    # Refresh token if expired
    if not claims and refresh_token:
        console.print("[dim]Access token expired. Attempting to refresh...[/dim]")
        try:
            token_data = _refresh_token_with_retry(refresh_token)
            new_access_token = token_data.get("access_token")
            new_refresh_token = token_data.get("refresh_token")

            if new_access_token:
                # Save tokens (keyring or file fallback)
                if use_file_fallback:
                    _set_token_to_file("access_token", new_access_token)
                    if new_refresh_token:
                        _set_token_to_file("refresh_token", new_refresh_token)
                else:
                    try:
                        keyring.set_password(SERVICE_ID, "access_token", new_access_token)
                        if new_refresh_token:
                            keyring.set_password(SERVICE_ID, "refresh_token", new_refresh_token)
                    except keyring.errors.KeyringError as e:
                        console.print(f"[dim]Keyring failed, falling back to file storage: {e}[/dim]")
                        _set_token_to_file("access_token", new_access_token)
                        if new_refresh_token:
                            _set_token_to_file("refresh_token", new_refresh_token)

                console.print("[bold green]Token refreshed successfully.[/bold green]")
                return new_access_token
            else:
                console.print("[bold red]Failed to get new access token.[/bold red]")
                return None

        except httpx.TimeoutException:
            console.print("[bold red]Token refresh failed: Request timed out.[/bold red]")
            return None
        except httpx.NetworkError:
            console.print("[bold red]Token refresh failed: Network error.[/bold red]")
            return None
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 400:
                console.print("[bold red]Refresh token expired. Please log in again.[/bold red]")
            else:
                error_detail = "Unknown error"
                try:
                    if exc.response.content:
                        content_type = exc.response.headers.get("content-type", "")
                        if "application/json" in content_type:
                            error_data = exc.response.json()
                            error_detail = error_data.get("detail", str(error_data))
                except Exception:
                    error_detail = exc.response.text[:200] if exc.response.text else "Unknown error"

                console.print(
                    f"[bold red]Token refresh failed: {exc.response.status_code} - {error_detail}[/bold red]"
                )

            # Clear tokens on refresh failure
            clear_tokens()
            return None
        except ValueError as e:
            console.print(f"[bold red]Token refresh failed: {e}[/bold red]")
            return None
        except Exception as e:
            console.print(
                f"[bold red]Token refresh failed: Unexpected error - {type(e).__name__}[/bold red]"
            )
            return None

    return access_token


def clear_tokens():
    """Clear stored access and refresh tokens (from both keyring and file)."""
    # Clear from keyring
    try:
        keyring.delete_password(SERVICE_ID, "access_token")
        keyring.delete_password(SERVICE_ID, "refresh_token")
    except keyring.errors.PasswordDeleteError:
        pass  # Tokens already cleared
    except keyring.errors.KeyringError:
        pass  # Keyring not available, that's OK

    # Clear from file storage (fallback)
    _delete_token_from_file("access_token")
    _delete_token_from_file("refresh_token")

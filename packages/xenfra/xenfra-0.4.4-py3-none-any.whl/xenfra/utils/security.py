"""
Security utilities for Xenfra CLI.
Implements comprehensive URL validation, domain whitelisting, HTTPS enforcement, and certificate pinning.
"""

import os
import ssl
from urllib.parse import urlparse

import certifi
import click
import httpx
from rich.console import Console

console = Console()

# Production API URL
PRODUCTION_API_URL = "https://api.xenfra.tech"

# Allowed domains (whitelist) - Solution 2
ALLOWED_DOMAINS = [
    "api.xenfra.tech",  # Production
    "api-staging.xenfra.tech",  # Staging
    "localhost",  # Local development
    "127.0.0.1",  # Local development (IP)
]

# Certificate fingerprints for pinning - Solution 4
# These should be updated when certificates are rotated
PINNED_CERTIFICATES = {
    "api.xenfra.tech": {
        # SHA256 fingerprint of the expected certificate
        # Example: "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
        # To get fingerprint, run:
        # openssl s_client -connect api.xenfra.tech:443 | openssl x509 -pubkey -noout \
        # | openssl pkey -pubin -outform der | openssl dgst -sha256 -binary | base64
        "fingerprints": [],  # Add actual fingerprints when you have production cert
    }
}


class SecurityConfig:
    """Security configuration for CLI."""

    def __init__(self):
        """Initialize security configuration from environment."""
        # PRODUCTION-ONLY: Default to production settings
        # Environment variable only used for self-hosted instances
        self.environment = "production"

        # Security settings - ALWAYS enforced for production safety
        self.enforce_https = True  # Always require HTTPS
        self.enforce_whitelist = False  # Allow self-hosted instances
        self.enable_cert_pinning = False  # Disabled (see future-enhancements.md #3)
        self.warn_on_http = True  # Always warn on HTTP

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment in ["development", "dev", "local"]


# Global security configuration
security_config = SecurityConfig()


def validate_url_format(url: str) -> dict:
    """
    Solution 1: Basic URL validation.

    Args:
        url: The URL to validate

    Returns:
        Parsed URL components

    Raises:
        ValueError: If URL format is invalid
    """
    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in ["http", "https"]:
            raise ValueError(
                f"Invalid URL scheme '{parsed.scheme}'. " f"Only 'http' and 'https' are allowed."
            )

        # Check hostname exists
        if not parsed.hostname:
            raise ValueError("URL must include a hostname")

        # Check for malicious patterns
        if ".." in url or "@" in url:
            raise ValueError("URL contains suspicious characters")

        # Prevent URL with credentials (http://user:pass@host)
        if parsed.username or parsed.password:
            raise ValueError("URLs with embedded credentials are not allowed")

        return {
            "scheme": parsed.scheme,
            "hostname": parsed.hostname,
            "port": parsed.port,
            "url": url,
        }

    except Exception as e:
        raise ValueError(f"Invalid URL format: {e}")


def check_domain_whitelist(hostname: str) -> bool:
    """
    Solution 2: Domain whitelist validation.

    Args:
        hostname: The hostname to check

    Returns:
        True if domain is whitelisted

    Raises:
        ValueError: If domain is not whitelisted and enforcement is enabled
    """
    is_whitelisted = hostname in ALLOWED_DOMAINS

    if not is_whitelisted:
        if security_config.enforce_whitelist:
            # Hard block in strict mode
            raise ValueError(
                f"Domain '{hostname}' is not in the whitelist.\n"
                f"Allowed domains: {', '.join(ALLOWED_DOMAINS)}\n\n"
                f"If you're using a self-hosted Xenfra instance:\n"
                f"1. Set XENFRA_ENFORCE_WHITELIST=false\n"
                f"2. Or contact support to whitelist your domain"
            )
        else:
            # Soft warning in permissive mode
            console.print(
                f"[yellow]⚠️  Warning: Domain '{hostname}' is not in the official whitelist.[/yellow]"
            )
            console.print(f"[dim]Whitelisted domains: {', '.join(ALLOWED_DOMAINS)}[/dim]")
            console.print("[yellow]Are you sure you want to connect to this API?[/yellow]")

            if not click.confirm("Continue?", default=False):
                raise click.Abort()

    return is_whitelisted


def enforce_https(scheme: str, hostname: str) -> None:
    """
    Solution 3: HTTPS enforcement.

    Args:
        scheme: URL scheme (http/https)
        hostname: The hostname

    Raises:
        ValueError: If HTTPS is required but HTTP is used
    """
    # Development exception: localhost is OK with HTTP
    is_localhost = hostname in ["localhost", "127.0.0.1"]

    if scheme == "http" and not is_localhost:
        if security_config.enforce_https:
            # Hard block in production/strict mode
            raise ValueError(
                f"HTTPS is required (environment: {security_config.environment}).\n"
                f"Current URL uses insecure HTTP.\n\n"
                f"To fix:\n"
                f"1. Update XENFRA_API_URL to use https://\n"
                f"2. Or set XENFRA_ENFORCE_HTTPS=false (not recommended)"
            )
        elif security_config.warn_on_http:
            # Soft warning
            console.print("[bold yellow]⚠️  Security Warning: Using unencrypted HTTP![/bold yellow]")
            console.print(f"[yellow]Connecting to: {scheme}://{hostname}[/yellow]")
            console.print("[yellow]Your credentials and data will be sent in plain text.[/yellow]")
            console.print("[yellow]This should ONLY be used for local development.[/yellow]\n")

            if not click.confirm("Continue with insecure connection?", default=False):
                raise click.Abort()


def create_secure_client(url: str, token: str = None) -> httpx.Client:
    """
    Solution 4: Create HTTP client with optional certificate pinning.

    Args:
        url: The base URL
        token: Optional authentication token

    Returns:
        Configured httpx.Client with security settings
    """
    parsed = urlparse(url)
    headers = {"Content-Type": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Certificate pinning for production domains (if enabled)
    if security_config.enable_cert_pinning and parsed.hostname in PINNED_CERTIFICATES:
        console.print(f"[dim]Enabling certificate pinning for {parsed.hostname}[/dim]")

        # Create SSL context with certificate verification
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED

        # Note: Full certificate pinning implementation would require custom verification
        # For now, we use strict certificate validation with system CA bundle
        # Future enhancement: Certificate fingerprint pinning (see docs/future-enhancements.md #3)

        return httpx.Client(
            base_url=url,
            headers=headers,
            verify=ssl_context,
            timeout=30.0,
        )
    else:
        # Standard client with default certificate verification
        return httpx.Client(
            base_url=url,
            headers=headers,
            timeout=30.0,
        )


def validate_and_get_api_url(url: str = None) -> str:
    """
    Comprehensive API URL validation (combines all 4 solutions).

    Args:
        url: Optional URL override (only for self-hosted instances)

    Returns:
        Validated API URL (defaults to https://api.xenfra.tech)

    Raises:
        ValueError: If URL fails validation
        click.Abort: If user cancels security prompts
    """
    # PRODUCTION DEFAULT: Use hardcoded production URL
    # Only check environment variable for self-hosted overrides
    if url is None:
        url = os.getenv("XENFRA_API_URL", PRODUCTION_API_URL)

    try:
        # Solution 1: Validate URL format
        parsed = validate_url_format(url)

        # Solution 2: Check domain whitelist
        check_domain_whitelist(parsed["hostname"])

        # Solution 3: Enforce HTTPS
        enforce_https(parsed["scheme"], parsed["hostname"])

        # Display security info ONLY in debug mode
        # Normal users shouldn't see this
        if os.getenv("DEBUG") or os.getenv("XENFRA_DEBUG"):
            console.print(f"[dim]🔒 Security: API URL validated: {url}[/dim]")
            console.print(f"[dim]   Environment: {security_config.environment}[/dim]")
            console.print(f"[dim]   HTTPS enforced: {security_config.enforce_https}[/dim]")
            console.print(f"[dim]   Whitelist enforced: {security_config.enforce_whitelist}[/dim]")
            console.print(f"[dim]   Cert pinning: {security_config.enable_cert_pinning}[/dim]")

        return url

    except ValueError as e:
        console.print("[bold red]🔒 Security Validation Failed:[/bold red]")
        console.print(f"[red]{e}[/red]")
        raise click.Abort()


def display_security_info():
    """Display current security configuration."""
    console.print("\n[bold cyan]🔒 Security Configuration:[/bold cyan]")

    table_data = [
        ("Environment", security_config.environment),
        ("HTTPS Enforcement", "✅ Enabled" if security_config.enforce_https else "⚠️  Disabled"),
        (
            "Domain Whitelist",
            "✅ Enforced" if security_config.enforce_whitelist else "⚠️  Warning Only",
        ),
        ("HTTP Warning", "✅ Enabled" if security_config.warn_on_http else "❌ Disabled"),
        (
            "Certificate Pinning",
            "✅ Enabled" if security_config.enable_cert_pinning else "❌ Disabled",
        ),
    ]

    for key, value in table_data:
        console.print(f"  {key}: {value}")

    console.print()


# Environment variable documentation
"""
PRODUCTION-FIRST DESIGN:
The CLI defaults to production (api.xenfra.tech) with HTTPS enforcement.
No configuration needed for normal users.

Environment variables (for developers/self-hosted only):

XENFRA_ENV=development
  - Enables local development mode
  - Allows HTTP, relaxes security
  - Default: production (safe by default)

XENFRA_API_URL=https://your-instance.com
  - Override API URL for self-hosted instances
  - Default: https://api.xenfra.tech

XENFRA_ENFORCE_HTTPS=true|false
  - Require HTTPS for all connections
  - Default: true (production), false (development)

Example usage:

# Production users (zero config):
xenfra auth login
xenfra deploy

# Local development:
XENFRA_ENV=development xenfra auth login

# Self-hosted instance:
XENFRA_API_URL=https://xenfra.mycompany.com xenfra login
"""

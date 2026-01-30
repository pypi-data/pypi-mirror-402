"""
Security configuration commands for Xenfra CLI.
"""

import os

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..utils.security import ALLOWED_DOMAINS, security_config, validate_and_get_api_url

console = Console()


@click.group(hidden=True)
def security():
    """Security and configuration management (for debugging/advanced users)."""
    pass


@security.command()
def check():
    """Display current security configuration."""
    # Get current API URL
    try:
        api_url = validate_and_get_api_url()
    except click.Abort:
        api_url = os.getenv("XENFRA_API_URL", "Not set")

    # Display configuration
    console.print("\n[bold cyan]🔒 Xenfra CLI Security Configuration[/bold cyan]\n")

    # API URL
    console.print(f"[bold]API URL:[/bold] {api_url}")

    # Environment
    env_color = "green" if security_config.is_production() else "yellow"
    console.print(
        f"[bold]Environment:[/bold] [{env_color}]{security_config.environment}[/{env_color}]"
    )

    console.print()

    # Security features table
    table = Table(title="Security Features", show_header=True)
    table.add_column("Feature", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Description", style="dim")

    features = [
        (
            "HTTPS Enforcement",
            "✅ Enabled" if security_config.enforce_https else "⚠️  Disabled",
            "Blocks HTTP connections (except localhost)",
        ),
        (
            "Domain Whitelist",
            "✅ Enforced" if security_config.enforce_whitelist else "⚠️  Warning Only",
            "Restricts connections to approved domains",
        ),
        (
            "HTTP Warning",
            "✅ Enabled" if security_config.warn_on_http else "❌ Disabled",
            "Warns when using insecure HTTP",
        ),
        (
            "Certificate Pinning",
            "✅ Enabled" if security_config.enable_cert_pinning else "❌ Disabled",
            "Validates SSL certificate fingerprints",
        ),
    ]

    for feature, status, description in features:
        table.add_row(feature, status, description)

    console.print(table)
    console.print()

    # Whitelisted domains
    console.print("[bold]Whitelisted Domains:[/bold]")
    for domain in ALLOWED_DOMAINS:
        console.print(f"  • {domain}")

    console.print()

    # Environment variables
    console.print("[bold]Configuration via Environment Variables:[/bold]")
    env_vars = [
        ("XENFRA_ENV", os.getenv("XENFRA_ENV", "development")),
        ("XENFRA_API_URL", os.getenv("XENFRA_API_URL", "http://localhost:8000")),
        ("XENFRA_ENFORCE_HTTPS", os.getenv("XENFRA_ENFORCE_HTTPS", "auto")),
        ("XENFRA_ENFORCE_WHITELIST", os.getenv("XENFRA_ENFORCE_WHITELIST", "auto")),
        ("XENFRA_ENABLE_CERT_PINNING", os.getenv("XENFRA_ENABLE_CERT_PINNING", "auto")),
        ("XENFRA_WARN_ON_HTTP", os.getenv("XENFRA_WARN_ON_HTTP", "true")),
    ]

    for var, value in env_vars:
        console.print(f"  {var}=[cyan]{value}[/cyan]")

    console.print()

    # Security recommendations
    if not security_config.is_production():
        console.print(
            Panel(
                "[yellow]⚠️  Development Mode Active[/yellow]\n\n"
                "For production use:\n"
                "1. Set XENFRA_ENV=production\n"
                "2. Use HTTPS API URL\n"
                "3. All security features will auto-enable",
                title="Recommendation",
                border_style="yellow",
            )
        )
    else:
        console.print(
            Panel(
                "[green]✅ Production Security Enabled[/green]\n\n"
                "All security features are active.\n"
                "Your credentials and data are protected.",
                title="Status",
                border_style="green",
            )
        )


@security.command()
@click.argument("url")
def validate(url):
    """Validate an API URL against security policies."""
    console.print(f"\n[cyan]Validating URL:[/cyan] {url}\n")

    try:
        validated_url = validate_and_get_api_url(url)
        console.print("[bold green]✅ URL is valid and passed all security checks![/bold green]")
        console.print(f"[dim]Validated URL: {validated_url}[/dim]")
    except click.Abort:
        console.print("[bold red]❌ URL failed security validation[/bold red]")
    except Exception as e:
        console.print(f"[bold red]❌ Validation error: {e}[/bold red]")


@security.command()
def docs():
    """Show security documentation."""
    docs_text = """
[bold cyan]Xenfra CLI Security Guide[/bold cyan]

[bold]Environment Detection:[/bold]
The CLI automatically adjusts security based on the environment:

• [green]production[/green]: All security features enforced
• [yellow]staging[/yellow]: HTTPS required, whitelist warnings
• [blue]development[/blue]: Permissive (localhost allowed)

[bold]Security Features:[/bold]

1. [cyan]URL Validation[/cyan]
   - Prevents malicious URL patterns
   - Blocks URLs with embedded credentials
   - Validates scheme (http/https only)

2. [cyan]Domain Whitelist[/cyan]
   - Restricts connections to approved domains
   - Prevents credential theft via fake APIs
   - Can be disabled for self-hosted instances

3. [cyan]HTTPS Enforcement[/cyan]
   - Requires encrypted connections in production
   - Warns on insecure HTTP (non-localhost)
   - Protects credentials and data in transit

4. [cyan]Certificate Pinning[/cyan]
   - Validates SSL certificate fingerprints
   - Prevents man-in-the-middle attacks
   - Optional (enabled in production by default)

[bold]Configuration Examples:[/bold]

[yellow]Development (default):[/yellow]
  $ xenfra login
  # Uses http://localhost:8000

[yellow]Self-hosted instance:[/yellow]
  $ export XENFRA_API_URL=https://xenfra.mycompany.com
  $ export XENFRA_ENFORCE_WHITELIST=false
  $ xenfra login

[yellow]Production (strict):[/yellow]
  $ export XENFRA_ENV=production
  $ xenfra login
  # All security features enabled

[bold]Environment Variables:[/bold]

XENFRA_ENV
  Values: production | staging | development
  Default: development

XENFRA_API_URL
  Default: http://localhost:8000 (dev), https://api.xenfra.tech (prod)

XENFRA_ENFORCE_HTTPS
  Values: true | false
  Default: false (dev), true (prod)

XENFRA_ENFORCE_WHITELIST
  Values: true | false
  Default: false (dev), true (prod)

XENFRA_ENABLE_CERT_PINNING
  Values: true | false
  Default: false (dev), true (prod)

XENFRA_WARN_ON_HTTP
  Values: true | false
  Default: true

[bold]Security Best Practices:[/bold]

1. Always use HTTPS in production
2. Never disable security features without understanding risks
3. Keep whitelisted domains list updated
4. Rotate credentials if you suspect compromise
5. Use environment-specific configurations
6. Enable all features for production deployments

[dim]For more information: https://docs.xenfra.tech/security[/dim]
"""

    console.print(Panel(docs_text, border_style="cyan", padding=(1, 2)))

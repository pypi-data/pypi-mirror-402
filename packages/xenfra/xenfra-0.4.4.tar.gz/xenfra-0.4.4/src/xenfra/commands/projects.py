"""
Project management commands for Xenfra CLI.
"""

import click
from rich.console import Console
from rich.table import Table
from xenfra_sdk import XenfraClient
from xenfra_sdk.exceptions import XenfraAPIError, XenfraError

from ..utils.auth import API_BASE_URL, get_auth_token
from ..utils.validation import (
    validate_project_id,
    validate_project_name,
    validate_region,
    validate_size_slug,
)

console = Console()


def get_client() -> XenfraClient:
    """Get authenticated SDK client."""
    token = get_auth_token()
    if not token:
        console.print("[bold red]Not logged in. Run 'xenfra login' first.[/bold red]")
        raise click.Abort()

    return XenfraClient(token=token, api_url=API_BASE_URL)


@click.group()
def projects():
    """Manage projects."""
    pass


@projects.command()
def list():
    """List all projects."""
    try:
        # Use context manager for proper cleanup
        with get_client() as client:
            projects_list = client.projects.list()

            if not projects_list:
                console.print("[bold yellow]No projects found.[/bold yellow]")
                return

            # Create a rich table
            table = Table(title="Projects")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Region", style="blue")
            table.add_column("IP Address", style="magenta")
            table.add_column("Cost/Month", style="red")

            for project in projects_list:
                cost = (
                    f"${project.estimated_monthly_cost:.2f}"
                    if project.estimated_monthly_cost
                    else "N/A"
                )
                table.add_row(
                    str(project.id),
                    project.name,
                    project.status,
                    project.region,
                    project.ip_address or "N/A",
                    cost,
                )

            console.print(table)

    except XenfraAPIError as e:
        console.print(f"[bold red]API Error: {e.detail}[/bold red]")
    except XenfraError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
    except click.Abort:
        pass


@projects.command()
@click.argument("project_id", type=int)
def show(project_id):
    """Show details for a specific project."""
    # Validate project ID
    is_valid, error_msg = validate_project_id(project_id)
    if not is_valid:
        console.print(f"[bold red]Invalid project ID: {error_msg}[/bold red]")
        raise click.Abort()

    try:
        with get_client() as client:
            project = client.projects.show(project_id)

            # Create detailed panel
            from rich.panel import Panel

            details = f"""[cyan]Name:[/cyan] {project.name}
[cyan]Status:[/cyan] {project.status}
[cyan]Region:[/cyan] {project.region}
[cyan]IP Address:[/cyan] {project.ip_address or 'N/A'}
[cyan]Size:[/cyan] {project.size_slug}
[cyan]Cost/Month:[/cyan] ${project.estimated_monthly_cost:.2f} USD
[cyan]Created:[/cyan] {project.created_at}"""

            panel = Panel(
                details,
                title=f"[bold green]Project {project.id}[/bold green]",
                border_style="green",
            )
            console.print(panel)

    except XenfraAPIError as e:
        console.print(f"[bold red]API Error: {e.detail}[/bold red]")
    except XenfraError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
    except click.Abort:
        pass


@projects.command()
@click.argument("project_id", type=int)
@click.confirmation_option(prompt="Are you sure you want to delete this project?")
def delete(project_id):
    """Delete a project."""
    # Validate project ID
    is_valid, error_msg = validate_project_id(project_id)
    if not is_valid:
        console.print(f"[bold red]Invalid project ID: {error_msg}[/bold red]")
        raise click.Abort()

    try:
        with get_client() as client:
            client.projects.delete(str(project_id))
            console.print(f"[bold green]Project {project_id} deletion initiated.[/bold green]")

    except XenfraAPIError as e:
        console.print(f"[bold red]API Error: {e.detail}[/bold red]")
    except XenfraError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
    except click.Abort:
        pass


@projects.command()
@click.argument("name")
@click.option("--region", default="nyc3", help="DigitalOcean region (default: nyc3)")
@click.option(
    "--size", "size_slug", default="s-1vcpu-1gb", help="Droplet size (default: s-1vcpu-1gb)"
)
def create(name, region, size_slug):
    """Create a new project."""
    # Validate project name
    is_valid, error_msg = validate_project_name(name)
    if not is_valid:
        console.print(f"[bold red]Invalid project name: {error_msg}[/bold red]")
        raise click.Abort()

    # Validate region
    is_valid, error_msg = validate_region(region)
    if not is_valid:
        console.print(f"[bold red]Invalid region: {error_msg}[/bold red]")
        raise click.Abort()

    # Validate size slug
    is_valid, error_msg = validate_size_slug(size_slug)
    if not is_valid:
        console.print(f"[bold red]Invalid size slug: {error_msg}[/bold red]")
        raise click.Abort()

    try:
        with get_client() as client:
            console.print(f"[cyan]Creating project '{name}'...[/cyan]")

            # Create project
            project = client.projects.create(name=name, region=region, size_slug=size_slug)

            # Display success message
            console.print("[bold green]✓[/bold green] Project created successfully!")

            # Show project details
            from rich.panel import Panel

            details = f"""[cyan]ID:[/cyan] {project.id}
[cyan]Name:[/cyan] {project.name}
[cyan]Status:[/cyan] {project.status}
[cyan]Region:[/cyan] {project.region}
[cyan]Size:[/cyan] {project.size_slug}
[cyan]Estimated Cost:[/cyan] ${project.estimated_monthly_cost:.2f}/month"""

            panel = Panel(
                details, title="[bold green]New Project[/bold green]", border_style="green"
            )
            console.print(panel)

    except XenfraAPIError as e:
        console.print(f"[bold red]API Error: {e.detail}[/bold red]")
    except XenfraError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
    except click.Abort:
        pass

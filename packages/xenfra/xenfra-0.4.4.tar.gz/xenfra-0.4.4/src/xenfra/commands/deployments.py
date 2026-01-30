"""
Deployment commands for Xenfra CLI.
"""

import os

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from xenfra_sdk import XenfraClient
from xenfra_sdk.exceptions import XenfraAPIError, XenfraError
from xenfra_sdk.privacy import scrub_logs

from ..utils.auth import API_BASE_URL, get_auth_token
from ..utils.codebase import has_xenfra_config
from ..utils.config import apply_patch, read_xenfra_yaml
from ..utils.validation import (
    validate_branch_name,
    validate_deployment_id,
    validate_framework,
    validate_git_repo_url,
    validate_project_id,
    validate_project_name,
)

import time
from datetime import datetime

from rich.live import Live
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

console = Console()

# Maximum number of retry attempts for auto-healing
MAX_RETRY_ATTEMPTS = 3


def get_client() -> XenfraClient:
    """Get authenticated SDK client."""
    token = get_auth_token()
    if not token:
        console.print("[bold red]Not logged in. Run 'xenfra auth login' first.[/bold red]")
        raise click.Abort()

    return XenfraClient(token=token, api_url=API_BASE_URL)


def show_diagnosis_panel(diagnosis: str, suggestion: str):
    """Display diagnosis and suggestion in formatted panels."""
    console.print()
    console.print(Panel(diagnosis, title="[bold red]🔍 Diagnosis[/bold red]", border_style="red"))
    console.print()
    console.print(
        Panel(suggestion, title="[bold yellow]💡 Suggestion[/bold yellow]", border_style="yellow")
    )


def show_patch_preview(patch_data: dict):
    """Show a preview of the patch that will be applied."""
    console.print()
    console.print("[bold green]🔧 Automatic Fix Available[/bold green]")
    console.print(f"  [cyan]File:[/cyan] {patch_data.get('file')}")
    console.print(f"  [cyan]Operation:[/cyan] {patch_data.get('operation')}")
    console.print(f"  [cyan]Value:[/cyan] {patch_data.get('value')}")
    console.print()


def _stream_deployment(client: XenfraClient, project_name: str, git_repo: str, branch: str, framework: str, region: str, size_slug: str, is_dockerized: bool = True, port: int = None, command: str = None, entrypoint: str = None, database: str = None, package_manager: str = None, dependency_file: str = None, file_manifest: list = None, cleanup_on_failure: bool = False, services: list = None, mode: str = None):
    """
    Creates deployment with real-time SSE streaming (no polling needed).

    Returns tuple of (status, deployment_id, logs_buffer)
    """
    console.print(Panel(
        f"[bold cyan]Project:[/bold cyan] {project_name}\n"
        f"[bold cyan]Mode:[/bold cyan] Real-time Streaming Deployment",
        title="[bold green]🚀 Deployment Starting[/bold green]",
        border_style="green"
    ))

    deployment_id = None
    logs_buffer = []
    status_val = "PENDING"

    try:
        for event in client.deployments.create_stream(
            project_name=project_name,
            git_repo=git_repo,
            branch=branch,
            framework=framework,
            region=region,
            size_slug=size_slug,
            is_dockerized=is_dockerized,
            port=port,
            command=command,
            entrypoint=entrypoint,  # Pass entrypoint to deployment API
            database=database,
            package_manager=package_manager,
            dependency_file=dependency_file,
            file_manifest=file_manifest,
            cleanup_on_failure=cleanup_on_failure,
            services=services,  # Microservices support
            mode=mode,  # Deployment mode
        ):

            event_type = event.get("event", "message")
            data = event.get("data", "")

            if event_type == "deployment_created":
                # Extract deployment ID
                if isinstance(data, dict):
                    deployment_id = data.get("deployment_id")
                    console.print(f"[bold green]✓[/bold green] Deployment created: [cyan]{deployment_id}[/cyan]\n")

            elif event_type == "log":
                # Real-time log output
                log_line = str(data)
                logs_buffer.append(log_line)

                # Colorize output
                if any(x in log_line for x in ["ERROR", "FAILED", "✗"]):
                    console.print(f"[bold red]{log_line}[/bold red]")
                elif any(x in log_line for x in ["WARN", "WARNING", "⚠"]):
                    console.print(f"[yellow]{log_line}[/yellow]")
                elif any(x in log_line for x in ["SUCCESS", "COMPLETED", "✓", "passed!"]):
                    console.print(f"[bold green]{log_line}[/bold green]")
                elif "PHASE" in log_line:
                    console.print(f"\n[bold blue]{log_line}[/bold blue]")
                elif "[InfraEngine]" in log_line or "[INFO]" in log_line:
                    console.print(f"[cyan]›[/cyan] {log_line}")
                else:
                    console.print(f"[dim]{log_line}[/dim]")

            elif event_type == "error":
                error_msg = str(data)
                logs_buffer.append(f"ERROR: {error_msg}")
                console.print(f"\n[bold red]❌ Error: {error_msg}[/bold red]")
                status_val = "FAILED"

            elif event_type == "deployment_complete":
                # Final status
                if isinstance(data, dict):
                    status_val = data.get("status", "UNKNOWN")
                    ip_address = data.get("ip_address")

                    console.print()
                    if status_val == "SUCCESS":
                        console.print("[bold green]✨ SUCCESS: Your application is live![/bold green]")
                        if ip_address and ip_address != "unknown":
                            console.print(f"[bold]Accessible at:[/bold] [link=http://{ip_address}]http://{ip_address}[/link]")
                    elif status_val == "FAILED":
                        console.print("[bold red]❌ DEPLOYMENT FAILED[/bold red]")
                        error = data.get("error")
                        if error:
                            console.print(f"[red]Error: {error}[/red]")
                break

    except Exception as e:
        console.print(f"\n[bold red]❌ Streaming error: {e}[/bold red]")
        status_val = "FAILED"
        logs_buffer.append(f"Streaming error: {e}")

    return (status_val, deployment_id, "\n".join(logs_buffer))


def _follow_deployment(client: XenfraClient, deployment_id: str):
    """
    Polls logs and status in real-time until completion with CI/CD style output.
    (LEGACY - Used for backward compatibility)
    """
    console.print(Panel(
        f"[bold cyan]Deployment ID:[/bold cyan] {deployment_id}\n"
        f"[bold cyan]Mode:[/bold cyan] Streaming Real-time Infrastructure Logs",
        title="[bold green]🚀 Deployment Monitor[/bold green]",
        border_style="green"
    ))

    last_log_len = 0
    status_val = "PENDING"

    # Use a live display for the progress bar at the bottom
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("Waiting for server response...", total=100)

        while status_val not in ["SUCCESS", "FAILED", "CANCELLED"]:
            try:
                # 1. Update Status
                dep_status = client.deployments.get_status(deployment_id)
                status_val = dep_status.get("status", "PENDING")
                progress_val = dep_status.get("progress", 0)
                state = dep_status.get("state", "preparing")

                # Use a more descriptive description for the progress task
                desc = f"Phase: {state}"
                if status_val == "FAILED":
                    desc = "[bold red]FAILED[/bold red]"
                elif status_val == "SUCCESS":
                    desc = "[bold green]SUCCESS[/bold green]"

                progress.update(task, completed=progress_val, description=desc)

                # 2. Update Logs
                log_content = client.deployments.get_logs(deployment_id)
                if log_content and len(log_content) > last_log_len:
                    new_logs = log_content[last_log_len:].strip()
                    for line in new_logs.split("\n"):
                        # Process and colorize lines
                        clean_line = line.strip()
                        if not clean_line:
                            continue

                        if any(x in clean_line for x in ["ERROR", "FAILED", "✗"]):
                            progress.console.print(f"[bold red]{clean_line}[/bold red]")
                        elif any(x in clean_line for x in ["WARN", "WARNING", "⚠"]):
                            progress.console.print(f"[yellow]{clean_line}[/yellow]")
                        elif any(x in clean_line for x in ["SUCCESS", "COMPLETED", "✓", "passed!"]):
                            progress.console.print(f"[bold green]{clean_line}[/bold green]")
                        elif "PHASE" in clean_line:
                            progress.console.print(f"\n[bold blue]{clean_line}[/bold blue]")
                        elif "[InfraEngine]" in clean_line:
                            progress.console.print(f"[dim]{clean_line}[/dim]")
                        else:
                            progress.console.print(f"[cyan]›[/cyan] {clean_line}")

                    last_log_len = len(log_content)

                if status_val in ["SUCCESS", "FAILED", "CANCELLED"]:
                    break

                time.sleep(1.5)  # Slightly faster polling for better feel
            except Exception as e:
                # progress.console.print(f"[dim]Transient connection issue: {e}[/dim]")
                time.sleep(3)
                continue

    console.print()
    if status_val == "SUCCESS":
        console.print("[bold green]✨ SUCCESS: Your application is live![/bold green]")
        # Try to get the IP address
        try:
            final_status = client.deployments.get_status(deployment_id)
            ip = final_status.get("ip_address")
            if ip:
                console.print(f"[bold]Accessible at:[/bold] [link=http://{ip}]http://{ip}[/link]")
        except:
            pass
    elif status_val == "FAILED":
        console.print("\n[bold red]❌ FAILURE DETECTED: Entering AI Diagnosis Mode...[/bold red]")

    return status_val


def zen_nod_workflow(
    logs: str, 
    client: XenfraClient, 
    attempt: int,
    package_manager: str = None,
    dependency_file: str = None,
    services: list = None
) -> bool:
    """
    Execute the Zen Nod auto-healing workflow.

    Args:
        logs: Deployment error logs
        client: Authenticated SDK client
        attempt: Current attempt number
        package_manager: Project package manager
        dependency_file: Project dependency file
        services: List of services in the project (for multi-service context)

    Returns:
        True if patch was applied and user wants to retry, False otherwise
    """
    console.print()
    console.print(f"[cyan]🤖 Analyzing failure (attempt {attempt}/{MAX_RETRY_ATTEMPTS})...[/cyan]")

    # Slice logs to last 300 lines for focused diagnosis (Fix #26)
    log_lines = logs.split("\n")
    if len(log_lines) > 300:
        logs = "\n".join(log_lines[-300:])
        console.print("[dim]Note: Analyzing only the last 300 lines of logs for efficiency.[/dim]")

    # Scrub sensitive data from logs
    scrubbed_logs = scrub_logs(logs)

    # Diagnose with AI
    try:
        diagnosis_result = client.intelligence.diagnose(
            logs=scrubbed_logs,
            package_manager=package_manager,
            dependency_file=dependency_file,
            services=services
        )
    except Exception as e:
        console.print(f"[yellow]Could not diagnose failure: {e}[/yellow]")
        return False

    # Show diagnosis
    show_diagnosis_panel(diagnosis_result.diagnosis, diagnosis_result.suggestion)

    # Check if there's an automatic patch
    if diagnosis_result.patch and diagnosis_result.patch.file:
        show_patch_preview(diagnosis_result.patch.model_dump())

        # Zen Nod confirmation
        if click.confirm("Apply this fix and retry deployment?", default=True):
            try:
                # Apply patch (with automatic backup)
                backup_path = apply_patch(diagnosis_result.patch.model_dump())
                console.print("[bold green]✓ Patch applied[/bold green]")
                if backup_path:
                    console.print(f"[dim]Backup saved: {backup_path}[/dim]")
                return True  # Signal to retry
            except Exception as e:
                console.print(f"[bold red]Failed to apply patch: {e}[/bold red]")
                return False
        else:
            console.print()
            console.print("[yellow]❌ Patch declined. Follow the manual steps above.[/yellow]")
            return False
    else:
        console.print()
        console.print(
            "[yellow]No automatic fix available. Please follow the manual steps above.[/yellow]"
        )
        return False


@click.command()
@click.argument("project_id", type=int)
@click.option("--show-details", is_flag=True, help="Show project details before confirmation")
@click.confirmation_option(prompt="Are you sure you want to delete this project and its infrastructure?")
def delete(project_id, show_details):
    """
    Delete a project and its infrastructure.

    This command will:
    - Destroy the DigitalOcean droplet
    - Remove database records

    WARNING: This action cannot be undone.
    """
    # Validate
    is_valid, error_msg = validate_project_id(project_id)
    if not is_valid:
        console.print(f"[bold red]Invalid project ID: {error_msg}[/bold red]")
        raise click.Abort()

    try:
        with get_client() as client:
            # Optional: Show details
            if show_details:
                try:
                    project = client.projects.show(project_id)

                    # Display panel with project info
                    details_table = Table(show_header=False, box=None)
                    details_table.add_column("Property", style="cyan")
                    details_table.add_column("Value")

                    details_table.add_row("Project ID", str(project_id))
                    if hasattr(project, 'name'):
                        details_table.add_row("Name", project.name)
                    if hasattr(project, 'droplet_id'):
                        details_table.add_row("Droplet ID", str(project.droplet_id))
                    if hasattr(project, 'ip_address'):
                        details_table.add_row("IP Address", project.ip_address)
                    if hasattr(project, 'created_at'):
                        details_table.add_row("Created", str(project.created_at))

                    panel = Panel(details_table, title="[bold]Project Details[/bold]", border_style="yellow")
                    console.print(panel)
                    console.print()
                except XenfraAPIError as e:
                    if e.status_code == 404:
                        console.print(f"[yellow]Note: Project {project_id} not found in records.[/yellow]")
                    else:
                        console.print(f"[yellow]Warning: Could not fetch project details: {e.detail}[/yellow]")
                    console.print()

            # Delete
            console.print(f"[cyan]Deleting project {project_id}...[/cyan]")
            client.projects.delete(str(project_id))
            console.print(f"[bold green]✓ Project {project_id} deleted successfully.[/bold green]")
            console.print("[dim]The droplet has been destroyed and all records removed.[/dim]")

    except XenfraAPIError as e:
        if e.status_code == 404:
            console.print(f"[yellow]Project {project_id} not found. It may have already been deleted.[/yellow]")
        else:
            console.print(f"[bold red]API Error: {e.detail}[/bold red]")
            raise click.Abort()
    except XenfraError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise click.Abort()
    except click.Abort:
        console.print("[dim]Deletion cancelled.[/dim]")
        raise
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        raise click.Abort()


@click.command()
@click.option("--project-name", help="Project name (defaults to current directory name)")
@click.option("--git-repo", help="Git repository URL (if deploying from git)")
@click.option("--branch", default="main", help="Git branch (default: main)")
@click.option("--framework", help="Framework override (fastapi, flask, django)")
@click.option("--region", help="DigitalOcean region override")
@click.option("--size", help="DigitalOcean size slug override")
@click.option("--no-heal", is_flag=True, help="Disable auto-healing on failure")
@click.option("--cleanup-on-failure", is_flag=True, help="Automatically cleanup resources if deployment fails")
def deploy(project_name, git_repo, branch, framework, region, size, no_heal, cleanup_on_failure):
    """
    Deploy current project to DigitalOcean with auto-healing.

    Deploys your application with zero configuration. The CLI will:
    1. Check for xenfra.yaml (or run init if missing)
    2. Create a deployment
    3. Auto-diagnose and fix failures (unless --no-heal is set or XENFRA_NO_AI=1)

    Set XENFRA_NO_AI=1 environment variable to disable all AI features.
    """
    # Check XENFRA_NO_AI environment variable
    no_ai = os.environ.get("XENFRA_NO_AI", "0") == "1"
    if no_ai:
        console.print("[yellow]XENFRA_NO_AI is set. Auto-healing disabled.[/yellow]")
        no_heal = True

    # Check for xenfra.yaml
    if not has_xenfra_config():
        console.print("[yellow]No xenfra.yaml found.[/yellow]")
        if click.confirm("Run 'xenfra init' to create configuration?", default=True):
            from .intelligence import init

            ctx = click.get_current_context()
            ctx.invoke(init, manual=no_ai, accept_all=False)
        else:
            console.print("[dim]Deployment cancelled.[/dim]")
            return

    # Load configuration from xenfra.yaml if it exists
    config = {}
    if has_xenfra_config():
        try:
            config = read_xenfra_yaml()
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read xenfra.yaml: {e}[/dim]")

    # Resolve values with precedence: 1. CLI Flag, 2. xenfra.yaml, 3. Default
    project_name = project_name or config.get("name") or os.path.basename(os.getcwd())
    framework = framework or config.get("framework")
    # Track if is_dockerized was explicitly set in config (to avoid AI override)
    is_dockerized_from_config = "is_dockerized" in config
    is_dockerized = config.get("is_dockerized", True)
    region = region or config.get("region") or "nyc3"
    
    # Resolve size slug (complex mapping)
    if not size:
        if config.get("size"):
            size = config.get("size")
        else:
            instance_size = config.get("instance_size", "basic")
            resources = config.get("resources", {})
            cpu = resources.get("cpu", 1)
            
            if instance_size == "standard" or cpu >= 2:
                size = "s-2vcpu-4gb"
            elif instance_size == "premium" or cpu >= 4:
                size = "s-4vcpu-8gb"
            else:
                size = "s-1vcpu-1gb"

    # Extract port, command, database from config
    # Track if port was explicitly set to avoid AI override
    port_from_config = config.get("port")
    port = port_from_config or 8000
    command = config.get("command")  # Auto-detected if not provided
    entrypoint = config.get("entrypoint")  # e.g., "todo.main:app"
    database_config = config.get("database", {})
    database = database_config.get("type") if isinstance(database_config, dict) else None
    package_manager = config.get("package_manager", "pip")
    dependency_file = config.get("dependency_file", "requirements.txt")
    
    # Microservices support: extract services and mode from xenfra.yaml
    services = config.get("services")  # List of service definitions
    mode = config.get("mode", "monolithic")  # monolithic, single-droplet, multi-droplet
    
    # If services are defined and > 1, this is a microservices deployment
    if services and len(services) > 1:
        console.print(f"\n[bold cyan]🔍 Detected microservices project ({len(services)} services)[/bold cyan]")
        
        # Display services table
        from rich.table import Table
        svc_table = Table(show_header=True, header_style="bold cyan", box=None)
        svc_table.add_column("Service", style="white")
        svc_table.add_column("Port", style="green")
        svc_table.add_column("Framework", style="yellow")
        
        for svc in services:
            svc_table.add_row(
                svc.get("name", "?"),
                str(svc.get("port", "?")),
                svc.get("framework", "?")
            )
        
        console.print(svc_table)
        console.print()
        
        # If mode not explicitly set in config, ask user
        if mode == "monolithic" or mode not in ["single-droplet", "multi-droplet"]:
            console.print("[bold]Choose deployment mode:[/bold]")
            console.print("  [cyan]1.[/cyan] Single Droplet - All services on one machine [dim](cost-effective)[/dim]")
            console.print("  [cyan]2.[/cyan] Multi Droplet  - Each service on its own machine [dim](scalable)[/dim]")
            console.print()
            
            mode_choice = Prompt.ask(
                "Deployment mode",
                choices=["1", "2"],
                default="1"
            )
            
            if mode_choice == "1":
                mode = "single-droplet"
                console.print("[green]✓ Using single-droplet mode[/green]\n")
            else:
                mode = "multi-droplet"
                console.print("[green]✓ Using multi-droplet mode[/green]")
                console.print(f"[dim]This will create {len(services)} separate droplets[/dim]\n")
        else:
            console.print(f"[dim]Using configured mode: {mode}[/dim]\n")

    # Default project name to current directory
    if not project_name:
        project_name = os.path.basename(os.getcwd())

    # Validate project name
    is_valid, error_msg = validate_project_name(project_name)
    if not is_valid:
        console.print(f"[bold red]Invalid project name: {error_msg}[/bold red]")
        raise click.Abort()

    # Validate git repo if provided
    if git_repo:
        is_valid, error_msg = validate_git_repo_url(git_repo)
        if not is_valid:
            console.print(f"[bold red]Invalid git repository URL: {error_msg}[/bold red]")
            raise click.Abort()
        console.print(f"[cyan]Deploying {project_name} from git repository...[/cyan]")
        console.print(f"[dim]Repository: {git_repo} (branch: {branch})[/dim]")
    else:
        # Note: Local folder deployment only works when engine runs locally
        # In cloud API mode, this will fail with a clear error from the server
        console.print(f"[cyan]Deploying {project_name}...[/cyan]")
        console.print("[dim]Note: Git repository recommended for cloud deployments[/dim]")

    # Validate branch name
    is_valid, error_msg = validate_branch_name(branch)
    if not is_valid:
        console.print(f"[bold red]Invalid branch name: {error_msg}[/bold red]")
        raise click.Abort()

    # Validate framework if provided
    if framework:
        is_valid, error_msg = validate_framework(framework)
        if not is_valid:
            console.print(f"[bold red]Invalid framework: {error_msg}[/bold red]")
            raise click.Abort()

    # Retry loop for auto-healing
    attempt = 0
    deployment_id = None

    try:
        with get_client() as client:
            while attempt < MAX_RETRY_ATTEMPTS:
                attempt += 1

                if attempt > 1:
                    console.print(
                        f"\n[cyan]🔄 Retrying deployment (attempt {attempt}/{MAX_RETRY_ATTEMPTS})...[/cyan]"
                    )
                else:
                    console.print("[cyan]Creating deployment...[/cyan]")

                # Detect framework if not provided (AI-powered Zen Mode)
                if not framework:
                    console.print("[cyan]🔍 AI Auto-detecting project type...[/cyan]")
                    try:
                        from ..utils.codebase import scan_codebase
                        code_snippets = scan_codebase()
                        if code_snippets:
                            analysis = client.intelligence.analyze_codebase(code_snippets)
                            framework = analysis.framework
                            # Only use AI's is_dockerized if config didn't explicitly set it
                            if not is_dockerized_from_config:
                                is_dockerized = analysis.is_dockerized
                            # Override port if AI detected it and config didn't set one
                            if not port_from_config and analysis.port:
                                port = analysis.port
                            # Override port and size if AI has strong recommendations
                            if not size and analysis.instance_size:
                                size = "s-1vcpu-1gb" if analysis.instance_size == "basic" else "s-2vcpu-4gb"
                            
                            mode_str = "Docker" if is_dockerized else "Bare Metal"
                            console.print(f"[green]✓ Detected {framework.upper()} project ({mode_str} Mode)[/green] (Port: {port})")
                        else:
                            console.print("[yellow]⚠ No code files found for AI analysis. Defaulting to 'fastapi'[/yellow]")
                            framework = "fastapi"
                            is_dockerized = True
                    except Exception as e:
                        console.print(f"[yellow]⚠ AI detection failed: {e}. Defaulting to 'fastapi'[/yellow]")
                        framework = "fastapi"
                        is_dockerized = True

                # Delta upload: if no git_repo, scan and upload local files
                file_manifest = None
                if not git_repo:
                    from ..utils.file_sync import scan_project_files_cached, ensure_gitignore_ignored
                    
                    # Protect privacy: ensure .xenfra is in .gitignore
                    if ensure_gitignore_ignored():
                        console.print("[dim]   - Added .xenfra to .gitignore for privacy[/dim]")
                    
                    console.print("[cyan]📁 Scanning project files...[/cyan]")

                    file_manifest = scan_project_files_cached()
                    console.print(f"[dim]Found {len(file_manifest)} files[/dim]")
                    
                    if not file_manifest:
                        console.print("[bold red]Error: No files found to deploy.[/bold red]")
                        raise click.Abort()
                    
                    # Check which files need uploading
                    console.print("[cyan]🔍 Checking file cache...[/cyan]")
                    check_result = client.files.check(file_manifest)
                    missing = check_result.get('missing', [])
                    cached = check_result.get('cached', 0)
                    
                    if cached > 0:
                        console.print(f"[green]✓ {cached} files already cached[/green]")
                    
                    # Upload missing files
                    if missing:
                        console.print(f"[cyan]☁️ Uploading {len(missing)} files...[/cyan]")
                        uploaded = client.files.upload_files(
                            file_manifest,
                            missing,
                            progress_callback=lambda done, total: console.print(f"[dim]   Progress: {done}/{total}[/dim]") if done % 10 == 0 or done == total else None
                        )
                        console.print(f"[green]✓ Uploaded {uploaded} files[/green]")
                    else:
                        console.print("[green]✓ All files already cached[/green]")
                    
                    # Remove abs_path from manifest before sending to API
                    file_manifest = [{"path": f["path"], "sha": f["sha"], "size": f["size"]} for f in file_manifest]

                # Create deployment with real-time streaming
                try:
                    status_result, deployment_id, logs_data = _stream_deployment(
                        client=client,
                        project_name=project_name,
                        git_repo=git_repo,
                        branch=branch,
                        framework=framework,
                        region=region,
                        size_slug=size,
                        is_dockerized=is_dockerized,
                        port=port,
                        command=command,
                        entrypoint=entrypoint,  # Pass entrypoint to deployment API
                        database=database,
                        package_manager=package_manager,
                        dependency_file=dependency_file,
                        file_manifest=file_manifest,
                        cleanup_on_failure=cleanup_on_failure,
                        services=services,  # Microservices support
                        mode=mode,  # Deployment mode
                    )


                    if status_result == "FAILED" and not no_heal:
                        # Hand off to the Zen Nod AI Agent
                        should_retry = zen_nod_workflow(
                            logs_data, 
                            client, 
                            attempt,
                            package_manager=package_manager,
                            dependency_file=dependency_file,
                            services=services
                        )

                        if should_retry:
                            # The agent applied a fix, loop back for attempt + 1
                            continue
                        else:
                            # Agent couldn't fix it or user declined
                            raise click.Abort()

                    # If we got here with success, break the retry loop
                    if status_result == "SUCCESS":
                        break
                    else:
                        raise click.Abort()

                except XenfraAPIError as e:
                    # Deployment failed - try to provide helpful error
                    from ..utils.errors import detect_error_type, show_error_with_solution
                    
                    console.print(f"[bold red]✗ Deployment failed[/bold red]")
                    
                    # Try to detect error type and show solution
                    error_type, error_kwargs = detect_error_type(str(e.detail))
                    if error_type:
                        show_error_with_solution(error_type, **error_kwargs)
                    else:
                        console.print(f"[red]{e.detail}[/red]")

                    # Check if we should auto-heal
                    if no_heal or attempt >= MAX_RETRY_ATTEMPTS:
                        # No auto-healing or max retries reached
                        if attempt >= MAX_RETRY_ATTEMPTS:
                            console.print(
                                f"\n[bold red]❌ Maximum retry attempts ({MAX_RETRY_ATTEMPTS}) reached.[/bold red]"
                            )
                            console.print(
                                "[yellow]Unable to auto-fix the issue. Please review the errors above.[/yellow]"
                            )
                        raise
                    else:
                        # Try to get logs for diagnosis
                        error_logs = str(e.detail)
                        try:
                            if deployment_id:
                                # This should be a method in the SDK that returns a string
                                logs_response = client.deployments.get_logs(deployment_id)
                                if isinstance(logs_response, dict):
                                    error_logs = logs_response.get("logs", str(e.detail))
                                else:
                                    error_logs = str(logs_response)  # Assuming it can be a string
                        except Exception as log_err:
                            console.print(
                                f"[yellow]Warning: Could not fetch detailed logs for diagnosis: {log_err}[/yellow]"
                            )
                            # Fallback to the initial error detail
                            pass

                        # Run Zen Nod workflow
                        should_retry = zen_nod_workflow(
                            error_logs, 
                            client, 
                            attempt,
                            package_manager=package_manager,
                            dependency_file=dependency_file,
                            services=services
                        )

                        if not should_retry:
                            # User declined patch or no patch available
                            console.print("\n[dim]Deployment cancelled.[/dim]")
                            raise click.Abort()

                        # Continue to next iteration (retry)
                        continue

    except XenfraAPIError as e:
        console.print(f"[bold red]API Error: {e.detail}[/bold red]")
    except XenfraError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
    except click.Abort:
        pass
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")


@click.command()
@click.argument("deployment-id")
@click.option("--follow", "-f", is_flag=True, help="Follow log output (stream)")
@click.option("--tail", type=int, help="Show last N lines")
def logs(deployment_id, follow, tail):
    # Validate deployment ID
    is_valid, error_msg = validate_deployment_id(deployment_id)
    if not is_valid:
        console.print(f"[bold red]Invalid deployment ID: {error_msg}[/bold red]")
        raise click.Abort()
    """
    Stream deployment logs.

    Shows logs for a specific deployment. Use --follow to stream logs in real-time.
    """
    try:
        with get_client() as client:
            console.print(f"[cyan]Fetching logs for deployment {deployment_id}...[/cyan]")

            log_content = client.deployments.get_logs(deployment_id)

            if not log_content:
                console.print("[yellow]No logs available yet.[/yellow]")
                console.print("[dim]The deployment may still be starting up.[/dim]")
                return

            # Process logs
            log_lines = log_content.strip().split("\n")

            # Apply tail if specified
            if tail:
                log_lines = log_lines[-tail:]

            # Display logs with syntax highlighting
            console.print(f"\n[bold]Logs for deployment {deployment_id}:[/bold]\n")

            if follow:
                _follow_deployment(client, deployment_id)
                return

            # Display logs
            for line in log_lines:
                # Color-code based on log level
                if "ERROR" in line or "FAILED" in line:
                    console.print(f"[red]{line}[/red]")
                elif "WARN" in line or "WARNING" in line:
                    console.print(f"[yellow]{line}[/yellow]")
                elif "SUCCESS" in line or "COMPLETED" in line:
                    console.print(f"[green]{line}[/green]")
                elif "INFO" in line:
                    console.print(f"[cyan]{line}[/cyan]")
                else:
                    console.print(line)

    except XenfraAPIError as e:
        console.print(f"[bold red]API Error: {e.detail}[/bold red]")
    except XenfraError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
    except click.Abort:
        pass


@click.command()
@click.argument("deployment-id", required=False)
@click.option("--watch", "-w", is_flag=True, help="Watch status updates")
def status(deployment_id, watch):
    """
    Show deployment status.

    Displays current status, progress, and details for a deployment.
    Use --watch to monitor status in real-time.
    """
    try:
        if not deployment_id:
            console.print("[yellow]No deployment ID provided.[/yellow]")
            console.print("[dim]Usage: xenfra status <deployment-id>[/dim]")
            return

        # Validate deployment ID
        is_valid, error_msg = validate_deployment_id(deployment_id)
        if not is_valid:
            console.print(f"[bold red]Invalid deployment ID: {error_msg}[/bold red]")
            raise click.Abort()

        with get_client() as client:
            console.print(f"[cyan]Fetching status for deployment {deployment_id}...[/cyan]")

            deployment_status = client.deployments.get_status(deployment_id)

            if watch:
                _follow_deployment(client, deployment_id)
                return

            # Display status
            status_value = deployment_status.get("status", "UNKNOWN")
            state = deployment_status.get("state", "unknown")
            progress = deployment_status.get("progress", 0)

            # Status panel
            status_color = {
                "PENDING": "yellow",
                "IN_PROGRESS": "cyan",
                "SUCCESS": "green",
                "FAILED": "red",
                "CANCELLED": "dim",
            }.get(status_value, "white")

            # Create status table
            table = Table(show_header=False, box=None)
            table.add_column("Property", style="cyan")
            table.add_column("Value")

            table.add_row("Deployment ID", str(deployment_id))
            table.add_row("Status", f"[{status_color}]{status_value}[/{status_color}]")
            table.add_row("State", state)

            if progress > 0:
                table.add_row("Progress", f"{progress}%")

            if "project_name" in deployment_status:
                table.add_row("Project", deployment_status["project_name"])

            if "created_at" in deployment_status:
                table.add_row("Created", deployment_status["created_at"])

            if "finished_at" in deployment_status:
                table.add_row("Finished", deployment_status["finished_at"])

            if "url" in deployment_status:
                table.add_row("URL", f"[link]{deployment_status['url']}[/link]")

            if "ip_address" in deployment_status:
                table.add_row("IP Address", deployment_status["ip_address"])

            panel = Panel(table, title="[bold]Deployment Status[/bold]", border_style=status_color)
            console.print(panel)

            # Show error if failed
            if status_value == "FAILED" and "error" in deployment_status:
                error_panel = Panel(
                    deployment_status["error"],
                    title="[bold red]Error[/bold red]",
                    border_style="red",
                )
                console.print("\n", error_panel)

                console.print("\n[bold]Troubleshooting:[/bold]")
                console.print(f"  • View logs: [cyan]xenfra logs {deployment_id}[/cyan]")
                console.print(f"  • Diagnose: [cyan]xenfra diagnose {deployment_id}[/cyan]")

            # Show next steps based on status
            elif status_value == "SUCCESS":
                console.print("\n[bold green]Deployment successful! 🎉[/bold green]")
                if "url" in deployment_status:
                    console.print(f"  • Visit: [link]{deployment_status['url']}[/link]")

            elif status_value in ["PENDING", "IN_PROGRESS"]:
                console.print("\n[bold]Deployment in progress...[/bold]")
                console.print(f"  • View logs: [cyan]xenfra logs {deployment_id}[/cyan]")
                console.print(f"  • Check again: [cyan]xenfra status {deployment_id}[/cyan]")

    except XenfraAPIError as e:
        console.print(f"[bold red]API Error: {e.detail}[/bold red]")
    except XenfraError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
    except click.Abort:
        pass


@click.command()
@click.argument("deployment-id")
@click.option("--format", "output_format", type=click.Choice(["detailed", "summary"], case_sensitive=False), default="detailed", help="Report format (detailed or summary)")
def report(deployment_id, output_format):
    """
    Generate deployment report with self-healing events.
    
    Shows comprehensive deployment information including:
    - Deployment status and timeline
    - Self-healing attempts and outcomes
    - Patches applied during healing
    - Statistics and metrics
    """
    try:
        # Validate deployment ID
        is_valid, error_msg = validate_deployment_id(deployment_id)
        if not is_valid:
            console.print(f"[bold red]Invalid deployment ID: {error_msg}[/bold red]")
            raise click.Abort()

        with get_client() as client:
            console.print(f"[cyan]Generating report for deployment {deployment_id}...[/cyan]\n")

            # Get deployment status
            try:
                deployment_status = client.deployments.get_status(deployment_id)
            except XenfraAPIError as e:
                console.print(f"[bold red]Error fetching deployment status: {e.detail}[/bold red]")
                raise click.Abort()

            # Get deployment logs
            try:
                logs = client.deployments.get_logs(deployment_id)
            except XenfraAPIError:
                logs = None

            # Parse status
            status_value = deployment_status.get("status", "UNKNOWN")
            state = deployment_status.get("state", "unknown")
            progress = deployment_status.get("progress", 0)

            # Status color mapping
            status_color = {
                "PENDING": "yellow",
                "IN_PROGRESS": "cyan",
                "SUCCESS": "green",
                "FAILED": "red",
                "CANCELLED": "dim",
            }.get(status_value, "white")

            # Calculate statistics from logs
            heal_attempts = logs.count("🤖 Analyzing failure") if logs else 0
            patches_applied = logs.count("✓ Patch applied") if logs else 0
            diagnoses = logs.count("🔍 Diagnosis") if logs else 0

            # Create main report table
            report_table = Table(show_header=True, box=None)
            report_table.add_column("Property", style="cyan", width=25)
            report_table.add_column("Value", style="white")

            report_table.add_row("Deployment ID", str(deployment_id))
            report_table.add_row("Status", f"[{status_color}]{status_value}[/{status_color}]")
            report_table.add_row("State", state)
            
            if progress > 0:
                report_table.add_row("Progress", f"{progress}%")

            if "project_name" in deployment_status:
                report_table.add_row("Project", deployment_status["project_name"])

            if "created_at" in deployment_status:
                report_table.add_row("Created", deployment_status["created_at"])

            if "finished_at" in deployment_status:
                report_table.add_row("Finished", deployment_status["finished_at"])

            if "url" in deployment_status:
                report_table.add_row("URL", f"[link]{deployment_status['url']}[/link]")

            if "ip_address" in deployment_status:
                report_table.add_row("IP Address", deployment_status["ip_address"])

            # Self-healing statistics
            report_table.add_row("", "")  # Separator
            report_table.add_row("[bold]Self-Healing Stats[/bold]", "")
            report_table.add_row("Healing Attempts", str(heal_attempts))
            report_table.add_row("Patches Applied", str(patches_applied))
            report_table.add_row("Diagnoses Performed", str(diagnoses))
            
            if heal_attempts > 0:
                success_rate = (patches_applied / heal_attempts * 100) if heal_attempts > 0 else 0
                report_table.add_row("Healing Success Rate", f"{success_rate:.1f}%")

            # Display main report
            console.print(Panel(report_table, title="[bold]Deployment Report[/bold]", border_style=status_color))

            # Detailed format includes timeline and healing events
            if output_format == "detailed" and logs:
                console.print("\n[bold]Self-Healing Timeline[/bold]\n")
                
                # Extract healing events from logs
                log_lines = logs.split("\n")
                timeline_entries = []
                
                for i, line in enumerate(log_lines):
                    if "🤖 Analyzing failure" in line:
                        attempt_match = None
                        # Try to find attempt number in surrounding lines
                        for j in range(max(0, i-5), min(len(log_lines), i+10)):
                            if "attempt" in log_lines[j].lower():
                                timeline_entries.append(("Healing Attempt", log_lines[j].strip()))
                                break
                    elif "🔍 Diagnosis" in line or "Diagnosis" in line:
                        # Extract diagnosis text from next few lines
                        diagnosis_text = line.strip()
                        if i+1 < len(log_lines) and log_lines[i+1].strip():
                            diagnosis_text += "\n  " + log_lines[i+1].strip()[:100]
                        timeline_entries.append(("Diagnosis", diagnosis_text))
                    elif "✓ Patch applied" in line or "Patch applied" in line:
                        timeline_entries.append(("Patch Applied", line.strip()))
                    elif "🔄 Retrying deployment" in line:
                        timeline_entries.append(("Retry", line.strip()))

                if timeline_entries:
                    timeline_table = Table(show_header=True, box=None)
                    timeline_table.add_column("Event", style="cyan", width=20)
                    timeline_table.add_column("Details", style="white")

                    for event_type, details in timeline_entries[:20]:  # Limit to 20 entries
                        timeline_table.add_row(event_type, details)

                    console.print(timeline_table)
                else:
                    console.print("[dim]No self-healing events detected in logs.[/dim]")

            # Show error if failed
            if status_value == "FAILED":
                console.print("\n[bold red]⚠ Deployment Failed[/bold red]")
                if "error" in deployment_status:
                    error_panel = Panel(
                        deployment_status["error"],
                        title="[bold red]Error Details[/bold red]",
                        border_style="red",
                    )
                    console.print("\n", error_panel)

                console.print("\n[bold]Troubleshooting:[/bold]")
                console.print(f"  • View logs: [cyan]xenfra logs {deployment_id}[/cyan]")
                console.print(f"  • Diagnose: [cyan]xenfra diagnose {deployment_id}[/cyan]")
                console.print(f"  • View status: [cyan]xenfra status {deployment_id}[/cyan]")

            # Success summary
            elif status_value == "SUCCESS":
                console.print("\n[bold green]✓ Deployment Successful[/bold green]")
                if heal_attempts > 0:
                    console.print(f"[dim]Deployment succeeded after {heal_attempts} self-healing attempt(s).[/dim]")
                if "url" in deployment_status:
                    console.print(f"  • Visit: [link]{deployment_status['url']}[/link]")

            # Export summary format (JSON-like structure for programmatic use)
            if output_format == "summary":
                console.print("\n[bold]Summary Format:[/bold]")
                import json
                summary = {
                    "deployment_id": deployment_id,
                    "status": status_value,
                    "healing_attempts": heal_attempts,
                    "patches_applied": patches_applied,
                    "success": status_value == "SUCCESS",
                }
                console.print(f"[dim]{json.dumps(summary, indent=2)}[/dim]")

    except XenfraAPIError as e:
        console.print(f"[bold red]API Error: {e.detail}[/bold red]")
    except XenfraError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
    except click.Abort:
        pass
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")

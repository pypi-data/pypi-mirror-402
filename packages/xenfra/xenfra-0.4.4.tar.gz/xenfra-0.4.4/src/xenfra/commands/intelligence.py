"""
AI-powered intelligence commands for Xenfra CLI.
Includes smart initialization, deployment diagnosis, and codebase analysis.
"""

import os

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from xenfra_sdk import XenfraClient
from xenfra_sdk.exceptions import XenfraAPIError, XenfraError
from xenfra_sdk.privacy import scrub_logs

from ..utils.auth import API_BASE_URL, get_auth_token
from ..utils.codebase import has_xenfra_config, scan_codebase
from ..utils.config import (
    apply_patch,
    generate_xenfra_yaml,
    manual_prompt_for_config,
    read_xenfra_yaml,
)
from ..utils.validation import validate_deployment_id

console = Console()


def get_client() -> XenfraClient:
    """Get authenticated SDK client."""
    token = get_auth_token()
    if not token:
        console.print("[bold red]Not logged in. Run 'xenfra login' first.[/bold red]")
        raise click.Abort()

    # DEBUG: Only show token info if XENFRA_DEBUG environment variable is set
    import os
    if os.getenv("XENFRA_DEBUG") == "1":
        import base64
        import json
        try:
            parts = token.split(".")
            if len(parts) == 3:
                # Decode payload
                payload_b64 = parts[1]
                padding = 4 - len(payload_b64) % 4
                if padding != 4:
                    payload_b64 += "=" * padding
                payload_bytes = base64.urlsafe_b64decode(payload_b64)
                claims = json.loads(payload_bytes)

                console.print("[dim]━━━ DEBUG: Token Info ━━━[/dim]")
                console.print(f"[dim]  API URL: {API_BASE_URL}[/dim]")
                console.print(f"[dim]  Token prefix: {token[:20]}...[/dim]")
                console.print(f"[dim]  sub (email): {claims.get('sub', 'MISSING')}[/dim]")
                console.print(f"[dim]  user_id: {claims.get('user_id', 'MISSING')}[/dim]")
                console.print(f"[dim]  iss (issuer): {claims.get('iss', 'MISSING')}[/dim]")
                console.print(f"[dim]  aud (audience): {claims.get('aud', 'MISSING')}[/dim]")

                # Check if token is expired
                exp = claims.get('exp')
                if exp:
                    import time
                    is_expired = time.time() >= exp
                    from datetime import datetime, timezone
                    exp_time = datetime.fromtimestamp(exp, tz=timezone.utc)
                    console.print(f"[dim]  expires_at: {exp_time}[/dim]")
                    console.print(f"[dim]  expired: {is_expired}[/dim]")
                console.print("[dim]━━━━━━━━━━━━━━━━━━━━━[/dim]\n")
        except Exception as e:
            console.print(f"[dim]DEBUG: Could not decode token: {e}[/dim]\n")

    return XenfraClient(token=token, api_url=API_BASE_URL)


@click.command()
@click.option("--manual", is_flag=True, help="Skip AI detection, use interactive mode")
@click.option("--accept-all", is_flag=True, help="Accept AI suggestions without confirmation")
def init(manual, accept_all):
    """
    Initialize Xenfra configuration (AI-powered by default).

    Scans your codebase, detects framework and dependencies,
    and generates xenfra.yaml automatically.
    
    For microservices projects (multiple services), generates xenfra-services.yaml.

    Use --manual to skip AI and configure interactively.
    Set XENFRA_NO_AI=1 environment variable to force manual mode globally.
    """
    # Check if config already exists
    if has_xenfra_config():
        console.print("[yellow]xenfra.yaml already exists.[/yellow]")
        if not Confirm.ask("Overwrite existing configuration?"):
            console.print("[dim]Cancelled.[/dim]")
            return

    # Check if xenfra-services.yaml already exists
    from pathlib import Path
    
    # === MICROSERVICES AUTO-DETECTION ===
    # Check for microservices project BEFORE AI analysis
    try:
        from xenfra_sdk import auto_detect_services, add_services_to_xenfra_yaml
        
        detected_services = auto_detect_services(".")
        
        if detected_services and len(detected_services) > 1:
            console.print(f"\n[bold cyan]🔍 Detected microservices project ({len(detected_services)} services)[/bold cyan]\n")
            
            # Display detected services
            from rich.table import Table
            svc_table = Table(show_header=True, header_style="bold cyan")
            svc_table.add_column("Service", style="white")
            svc_table.add_column("Path", style="dim")
            svc_table.add_column("Port", style="green")
            svc_table.add_column("Framework", style="yellow")
            svc_table.add_column("Entrypoint", style="dim")
            
            for svc in detected_services:
                svc_table.add_row(
                    svc.get("name", "?"),
                    svc.get("path", "?"),
                    str(svc.get("port", "?")),
                    svc.get("framework", "?"),
                    svc.get("entrypoint", "-") or "-"
                )
            
            console.print(svc_table)
            console.print()
            
            if Confirm.ask("Add services to xenfra.yaml for microservices deployment?", default=True):
                # Add services array to xenfra.yaml
                add_services_to_xenfra_yaml(".", detected_services, mode="single-droplet")
                
                console.print("\n[bold green]✓ Added services to xenfra.yaml![/bold green]")
                console.print("[dim]Run 'xenfra deploy' to deploy all services.[/dim]")
                console.print("[dim]Use 'xenfra deploy --mode=multi-droplet' for separate droplets per service.[/dim]")
                return
            else:
                console.print("[dim]Continuing with single-service configuration...[/dim]\n")
                
    except ImportError:
        # SDK doesn't have microservices support yet
        pass
    except Exception as e:
        console.print(f"[dim]Note: Microservices detection skipped: {e}[/dim]\n")


    # Check for XENFRA_NO_AI environment variable
    no_ai = os.environ.get("XENFRA_NO_AI", "0") == "1"
    if no_ai and not manual:
        console.print("[yellow]XENFRA_NO_AI is set. Using manual mode.[/yellow]")
        manual = True

    # Manual mode - interactive prompts
    if manual:
        console.print("[cyan]Manual configuration mode[/cyan]\n")
        try:
            manual_prompt_for_config()
            console.print("\n[bold green]✓ xenfra.yaml created successfully![/bold green]")
            console.print("[dim]Run 'xenfra deploy' to deploy your project.[/dim]")
        except KeyboardInterrupt:
            console.print("\n[dim]Cancelled.[/dim]")
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
        return

    # AI-powered detection (default)
    try:
        # Use context manager for SDK client
        with get_client() as client:
            # Scan codebase
            console.print("[cyan]Analyzing your codebase...[/cyan]")
            code_snippets = scan_codebase()

            if not code_snippets:
                console.print("[bold red]No code files found to analyze.[/bold red]")
                console.print("[dim]Make sure you're in a Python project directory.[/dim]")
                return

            console.print(f"[dim]Found {len(code_snippets)} files to analyze[/dim]")

            # Call Intelligence Service
            analysis = client.intelligence.analyze_codebase(code_snippets)

            # Client-side conflict detection (ensures Zen Nod always triggers)
            from ..utils.codebase import detect_package_manager_conflicts
            has_conflict_local, detected_managers_local = detect_package_manager_conflicts(code_snippets)

            if has_conflict_local and not analysis.has_conflict:
                # AI missed the conflict - fix it client-side
                console.print("[dim]Note: Enhanced conflict detection activated[/dim]\n")
                analysis.has_conflict = True
                # Convert dict to object for compatibility
                from types import SimpleNamespace
                analysis.detected_package_managers = [
                    SimpleNamespace(**pm) for pm in detected_managers_local
                ]

        # Display results
        console.print("\n[bold green]Analysis Complete![/bold green]\n")

        # Handle package manager conflict
        selected_package_manager = analysis.package_manager
        selected_dependency_file = analysis.dependency_file

        if analysis.has_conflict and analysis.detected_package_managers:
            console.print("[yellow]Multiple package managers detected![/yellow]\n")

            # Show options
            for i, option in enumerate(analysis.detected_package_managers, 1):
                console.print(f"  {i}. [cyan]{option.manager}[/cyan] ({option.file})")

            console.print(f"\n[dim]Recommended: {analysis.package_manager} (most modern)[/dim]")

            # Prompt user to select
            choice = Prompt.ask(
                "\nWhich package manager do you want to use?",
                choices=[str(i) for i in range(1, len(analysis.detected_package_managers) + 1)],
                default="1",
            )

            # Update selection based on user choice
            selected_option = analysis.detected_package_managers[int(choice) - 1]
            selected_package_manager = selected_option.manager
            selected_dependency_file = selected_option.file

            console.print(
                f"\n[green]Using {selected_package_manager} ({selected_dependency_file})[/green]\n"
            )

        table = Table(show_header=False, box=None)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Framework", analysis.framework)
        table.add_row("Port", str(analysis.port))
        table.add_row("Database", analysis.database)
        if analysis.cache:
            table.add_row("Cache", analysis.cache)
        if analysis.workers:
            table.add_row("Workers", ", ".join(analysis.workers))
        table.add_row("Package Manager", selected_package_manager)
        table.add_row("Dependency File", selected_dependency_file)
        
        # New: Infrastructure details in summary
        table.add_row("Region", "nyc3 (default)")
        table.add_row("Instance Size", analysis.instance_size)
        
        # Resource visualization
        cpu = 1 if analysis.instance_size == "basic" else (2 if analysis.instance_size == "standard" else 4)
        ram = "1GB" if analysis.instance_size == "basic" else ("4GB" if analysis.instance_size == "standard" else "8GB")
        table.add_row("Resources", f"{cpu} vCPU, {ram} RAM")

        table.add_row("Estimated Cost", f"${analysis.estimated_cost_monthly:.2f}/month")
        table.add_row("Confidence", f"{analysis.confidence:.0%}")

        console.print(Panel(table, title="[bold]Detected Configuration[/bold]"))

        if analysis.notes:
            console.print(f"\n[dim]{analysis.notes}[/dim]")

        # Confirm or edit
        if accept_all:
            confirmed = True
        else:
            confirmed = Confirm.ask("\nCreate xenfra.yaml with this configuration?", default=True)

        if confirmed:
            generate_xenfra_yaml(analysis, package_manager_override=selected_package_manager, dependency_file_override=selected_dependency_file)
            console.print("[bold green]xenfra.yaml created successfully![/bold green]")
            console.print("[dim]Run 'xenfra deploy' to deploy your project.[/dim]")
        else:
            console.print("[yellow]Configuration cancelled.[/yellow]")

    except XenfraAPIError as e:
        console.print(f"[bold red]API Error: {e.detail}[/bold red]")
    except XenfraError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
    except click.Abort:
        pass
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")


@click.command()
@click.argument("deployment-id", required=False)
@click.option("--apply", is_flag=True, help="Auto-apply suggested patch (with confirmation)")
@click.option("--logs", type=click.File("r"), help="Diagnose from log file instead of deployment")
def diagnose(deployment_id, apply, logs):
    """
    Diagnose deployment failures using AI.

    Analyzes logs and provides diagnosis, suggestions, and optionally
    an automatic patch to fix the issue.
    """
    try:
        # Use context manager for all SDK operations
        with get_client() as client:
            # Get logs
            if logs:
                log_content = logs.read()
                console.print("[cyan]Analyzing logs from file...[/cyan]")
            elif deployment_id:
                # Validate deployment ID
                is_valid, error_msg = validate_deployment_id(deployment_id)
                if not is_valid:
                    console.print(f"[bold red]Invalid deployment ID: {error_msg}[/bold red]")
                    return

                console.print(f"[cyan]Fetching logs for deployment {deployment_id}...[/cyan]")
                log_content = client.deployments.get_logs(deployment_id)

                if not log_content:
                    console.print("[yellow]No logs found for this deployment.[/yellow]")
                    return
            else:
                console.print(
                    "[bold red]Please specify a deployment ID or use --logs <file>[/bold red]"
                )
                console.print(
                    "[dim]Usage: xenfra diagnose <deployment-id> or xenfra diagnose --logs error.log[/dim]"
                )
                return

            # Scrub sensitive data
            scrubbed_logs = scrub_logs(log_content)

            # Try to read package manager context and collect code snippets
            package_manager = None
            dependency_file = None
            code_snippets = []
            services = None
            try:
                config = read_xenfra_yaml()
                package_manager = config.get("package_manager")
                dependency_file = config.get("dependency_file")
                services = config.get("services")

                if package_manager and dependency_file:
                    console.print(
                        f"[dim]Using context: {package_manager} ({dependency_file})[/dim]"
                    )
                    # Automatically collect the main dependency file
                    if os.path.exists(dependency_file):
                        with open(dependency_file, "r", encoding="utf-8", errors="ignore") as f:
                            code_snippets.append({
                                "file": dependency_file,
                                "content": f.read()
                            })
                
                # If it's a multi-service project, also collect requirement files from sub-services
                if services:
                    for svc in services:
                        svc_path = svc.get("path", ".")
                        # Look for common dependency files in service path
                        for common_file in ["requirements.txt", "pyproject.toml"]:
                            pfile = os.path.join(svc_path, common_file) if svc_path != "." else common_file
                            # Don't add if already added (e.g. root dependency file)
                            if os.path.exists(pfile) and not any(s["file"] == pfile for s in code_snippets):
                                with open(pfile, "r", encoding="utf-8", errors="ignore") as f:
                                    code_snippets.append({
                                        "file": pfile,
                                        "content": f.read()
                                    })

            except FileNotFoundError:
                console.print(
                    "[dim]No xenfra.yaml found - inferring context from files[/dim]"
                )
                # Fallback: scan root for dependency files
                for common_file in ["requirements.txt", "pyproject.toml"]:
                    if os.path.exists(common_file):
                        with open(common_file, "r", encoding="utf-8", errors="ignore") as f:
                            code_snippets.append({
                                "file": common_file,
                                "content": f.read()
                            })

            # Diagnose with context and snippets
            console.print("[cyan]Analyzing failure...[/cyan]")
            result = client.intelligence.diagnose(
                logs=scrubbed_logs, 
                package_manager=package_manager, 
                dependency_file=dependency_file,
                services=services,
                code_snippets=code_snippets
            )

        # Display diagnosis
        console.print("\n")
        console.print(
            Panel(result.diagnosis, title="[bold red]Diagnosis[/bold red]", border_style="red")
        )
        console.print(
            Panel(
                result.suggestion,
                title="[bold yellow]Suggestion[/bold yellow]",
                border_style="yellow",
            )
        )

        # Handle patch
        if result.patch and result.patch.file:
            console.print("\n[bold green]Automatic fix available![/bold green]")
            console.print(f"  File: [cyan]{result.patch.file}[/cyan]")
            console.print(f"  Operation: [yellow]{result.patch.operation}[/yellow]")
            console.print(f"  Value: [white]{result.patch.value}[/white]")

            if apply or Confirm.ask("\nApply this patch?", default=False):
                try:
                    apply_patch(result.patch.model_dump())
                    console.print("[bold green]Patch applied successfully![/bold green]")
                    console.print("[cyan]Run 'xenfra deploy' to retry deployment.[/cyan]")
                except FileNotFoundError as e:
                    console.print(f"[bold red]Error: {e}[/bold red]")
                except Exception as e:
                    console.print(f"[bold red]Failed to apply patch: {e}[/bold red]")
            else:
                console.print("[dim]Patch not applied. Follow manual steps above.[/dim]")
        else:
            console.print("\n[yellow]No automatic fix available.[/yellow]")
            console.print("[dim]Please follow the manual steps in the suggestion above.[/dim]")

    except XenfraAPIError as e:
        console.print(f"[bold red]API Error: {e.detail}[/bold red]")
    except XenfraError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
    except click.Abort:
        pass
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")


@click.command()
def analyze():
    """
    Analyze codebase without creating configuration.

    Shows what AI would detect, useful for previewing before running init.
    """
    try:
        # Use context manager for SDK client
        with get_client() as client:
            # Scan codebase
            console.print("[cyan]Analyzing your codebase...[/cyan]")
            code_snippets = scan_codebase()

            if not code_snippets:
                console.print("[bold red]No code files found to analyze.[/bold red]")
                return

            # Call Intelligence Service
            analysis = client.intelligence.analyze_codebase(code_snippets)

        # Display results
        console.print("\n[bold green]Analysis Results:[/bold green]\n")

        table = Table(show_header=False, box=None)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Framework", analysis.framework)
        table.add_row("Port", str(analysis.port))
        table.add_row("Database", analysis.database)
        if analysis.cache:
            table.add_row("Cache", analysis.cache)
        if analysis.workers:
            table.add_row("Workers", ", ".join(analysis.workers))
        if analysis.env_vars:
            table.add_row("Environment Variables", ", ".join(analysis.env_vars))
        
        # New: Infrastructure details in preview
        table.add_row("Region", "nyc3 (default)")
        table.add_row("Instance Size", analysis.instance_size)
        
        # Resource visualization
        cpu = 1 if analysis.instance_size == "basic" else (2 if analysis.instance_size == "standard" else 4)
        ram = "1GB" if analysis.instance_size == "basic" else ("4GB" if analysis.instance_size == "standard" else "8GB")
        table.add_row("Resources", f"{cpu} vCPU, {ram} RAM")

        table.add_row("Estimated Cost", f"${analysis.estimated_cost_monthly:.2f}/month")
        table.add_row("Confidence", f"{analysis.confidence:.0%}")

        console.print(table)

        if analysis.notes:
            console.print(f"\n[dim]Notes: {analysis.notes}[/dim]")

        console.print(
            "\n[dim]Run 'xenfra init' to create xenfra.yaml with this configuration.[/dim]"
        )

    except XenfraAPIError as e:
        console.print(f"[bold red]API Error: {e.detail}[/bold red]")
    except XenfraError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
    except click.Abort:
        pass
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")

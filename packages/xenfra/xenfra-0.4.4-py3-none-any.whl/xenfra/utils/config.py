"""
Configuration file generation utilities.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from xenfra_sdk import CodebaseAnalysisResponse

console = Console()


def read_xenfra_yaml(filename: str = "xenfra.yaml") -> dict:
    """
    Read and parse xenfra.yaml configuration file.

    Args:
        filename: Path to the config file (default: xenfra.yaml)

    Returns:
        Dictionary containing the configuration

    Raises:
        FileNotFoundError: If the config file doesn't exist
        yaml.YAMLError: If the YAML is malformed
        ValueError: If the YAML is invalid
        IOError: If reading fails
    """
    if not Path(filename).exists():
        raise FileNotFoundError(
            f"Configuration file '{filename}' not found. Run 'xenfra init' first."
        )

    try:
        with open(filename, "r") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {filename}: {e}")
    except Exception as e:
        raise IOError(f"Failed to read {filename}: {e}")


def generate_xenfra_yaml(analysis: CodebaseAnalysisResponse, filename: str = "xenfra.yaml", package_manager_override: str = None, dependency_file_override: str = None) -> str:
    """
    Generate xenfra.yaml from AI codebase analysis.

    Args:
        analysis: CodebaseAnalysisResponse from Intelligence Service
        filename: Output filename (default: xenfra.yaml)
        package_manager_override: Optional override for package manager (user selection)
        dependency_file_override: Optional override for dependency file (user selection)

    Returns:
        Path to the generated file
    """
    # Build configuration dictionary
    config = {
        "name": os.path.basename(os.getcwd()),
        "framework": analysis.framework,
        "region": "nyc3",  # Default to NYC3
        "port": analysis.port,
    }

    # Add entrypoint if detected (e.g., "todo.main:app")
    if hasattr(analysis, 'entrypoint') and analysis.entrypoint:
        config["entrypoint"] = analysis.entrypoint

    # Add database configuration if detected
    if analysis.database and analysis.database != "none":
        config["database"] = {"type": analysis.database, "env_var": "DATABASE_URL"}

    # Add cache configuration if detected
    if analysis.cache and analysis.cache != "none":
        config["cache"] = {"type": analysis.cache, "env_var": f"{analysis.cache.upper()}_URL"}

    # Add worker configuration if detected
    if analysis.workers and len(analysis.workers) > 0:
        config["workers"] = analysis.workers

    # Add environment variables
    if analysis.env_vars and len(analysis.env_vars) > 0:
        config["env_vars"] = analysis.env_vars

    # Infrastructure configuration
    config["instance_size"] = analysis.instance_size
    config["resources"] = {
        "cpu": 1,
        "ram": "1GB"
    }
    
    # Map resources based on detected size for better defaults
    if analysis.instance_size == "standard":
        config["resources"]["cpu"] = 2
        config["resources"]["ram"] = "4GB"
    elif analysis.instance_size == "premium":
        config["resources"]["cpu"] = 4
        config["resources"]["ram"] = "8GB"

    # Add package manager info (use override if provided, otherwise use analysis)
    package_manager = package_manager_override or analysis.package_manager
    dependency_file = dependency_file_override or analysis.dependency_file
    
    if package_manager:
        config["package_manager"] = package_manager
    if dependency_file:
        config["dependency_file"] = dependency_file

    # Write to file
    with open(filename, "w") as f:
        yaml.dump(config, f, sort_keys=False, default_flow_style=False)

    return filename


def create_backup(file_path: str) -> str:
    """
    Create a timestamped backup of a file in .xenfra/backups/ directory.

    Args:
        file_path: Path to the file to backup

    Returns:
        Path to the backup file
    """
    # Create .xenfra/backups directory if it doesn't exist
    backup_dir = Path(".xenfra") / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamped backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = Path(file_path).name
    backup_path = backup_dir / f"{file_name}.{timestamp}.backup"

    # Copy file to backup location
    shutil.copy2(file_path, backup_path)

    return str(backup_path)


def apply_patch(patch: dict, target_file: str = None, create_backup_file: bool = True):
    """
    Apply a JSON patch to a configuration file with automatic backup.

    Args:
        patch: Patch object with file, operation, path, value
        target_file: Optional override for the file to patch
        create_backup_file: Whether to create a backup before patching (default: True)

    Returns:
        Path to the backup file if created, None otherwise

    Raises:
        ValueError: If patch structure is invalid
        FileNotFoundError: If target file doesn't exist
        NotImplementedError: If file type is not supported
    """
    # Validate patch structure
    if not isinstance(patch, dict):
        raise ValueError("Patch must be a dictionary")

    required_fields = ["file", "operation"]
    for field in required_fields:
        if field not in patch:
            raise ValueError(f"Patch missing required field: {field}")

    operation = patch.get("operation")
    if operation not in ["add", "replace", "remove"]:
        raise ValueError(
            f"Invalid patch operation: {operation}. Must be 'add', 'replace', or 'remove'"
        )

    file_to_patch = target_file or patch.get("file")

    if not file_to_patch:
        raise ValueError("No target file specified in patch")

    if not os.path.exists(file_to_patch):
        # Path resolution fallback for multi-service projects
        filename = os.path.basename(file_to_patch)
        if os.path.exists(filename):
            console.print(f"[dim]Note: Suggested path '{file_to_patch}' not found. Falling back to '{filename}'[/dim]")
            file_to_patch = filename
        else:
            # Try to resolve via xenfra.yaml if available
            try:
                from .config import read_xenfra_yaml
                config = read_xenfra_yaml()
                if "services" in config:
                    for svc in config["services"]:
                        svc_path = svc.get("path", ".")
                        # If service path is '.' and we're looking for filename in it
                        potential_path = os.path.join(svc_path, filename) if svc_path != "." else filename
                        if os.path.exists(potential_path):
                            console.print(f"[dim]Note: Resolved '{file_to_patch}' to '{potential_path}' via xenfra.yaml[/dim]")
                            file_to_patch = potential_path
                            break
            except Exception:
                pass

        if not os.path.exists(file_to_patch):
            raise FileNotFoundError(f"File '{file_to_patch}' not found")

    # Create backup before modifying
    backup_path = None
    if create_backup_file:
        backup_path = create_backup(file_to_patch)

    # For YAML files
    if file_to_patch.endswith((".yaml", ".yml")):
        with open(file_to_patch, "r") as f:
            config_data = yaml.safe_load(f) or {}

        # Apply patch based on operation
        operation = patch.get("operation")
        path = (patch.get("path") or "").strip("/")
        value = patch.get("value")

        if operation == "add":
            # For simple paths, add to root
            if path:
                path_parts = path.split("/")
                current = config_data
                for part in path_parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[path_parts[-1]] = value
            else:
                # Add to root level
                if isinstance(value, dict):
                    config_data.update(value)
                else:
                    config_data = value

        elif operation == "replace":
            if path:
                path_parts = path.split("/")
                current = config_data
                for part in path_parts[:-1]:
                    current = current[part]
                current[path_parts[-1]] = value
            else:
                config_data = value

        # Write back
        with open(file_to_patch, "w") as f:
            yaml.dump(config_data, f, sort_keys=False, default_flow_style=False)

    # For JSON files
    elif file_to_patch.endswith(".json"):
        import json

        with open(file_to_patch, "r") as f:
            config_data = json.load(f)

        operation = patch.get("operation")
        path = (patch.get("path") or "").strip("/")
        value = patch.get("value")

        if operation == "add":
            if path:
                path_parts = path.split("/")
                current = config_data
                for part in path_parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[path_parts[-1]] = value
            else:
                if isinstance(value, dict):
                    config_data.update(value)
                else:
                    config_data = value

        elif operation == "replace":
            if path:
                path_parts = path.split("/")
                current = config_data
                for part in path_parts[:-1]:
                    current = current[part]
                current[path_parts[-1]] = value
            else:
                config_data = value

        # Write back
        with open(file_to_patch, "w") as f:
            json.dump(config_data, f, indent=2)

    # For text files (like requirements.txt)
    elif file_to_patch.endswith(".txt"):
        operation = patch.get("operation")
        value = patch.get("value")

        if operation == "add":
            # Append to file
            with open(file_to_patch, "a") as f:
                f.write(f"\n{value}\n")
        elif operation == "replace":
            # Replace entire file
            with open(file_to_patch, "w") as f:
                f.write(str(value))

    # For TOML files (pyproject.toml)
    elif file_to_patch.endswith(".toml"):
        import toml

        with open(file_to_patch, "r") as f:
            config_data = toml.load(f)

        operation = patch.get("operation")
        path = (patch.get("path") or "").strip("/")
        value = patch.get("value")

        if operation == "add":
            # Special case for pyproject.toml dependencies
            is_pyproject = os.path.basename(file_to_patch) == "pyproject.toml"
            if is_pyproject and (not path or path == "project/dependencies"):
                # Ensure project and dependencies exist
                if "project" not in config_data:
                    config_data["project"] = {}
                if "dependencies" not in config_data["project"]:
                    config_data["project"]["dependencies"] = []
                
                # Add value if not already present
                if value not in config_data["project"]["dependencies"]:
                    config_data["project"]["dependencies"].append(value)
            elif path:
                path_parts = path.split("/")
                current = config_data
                for part in path_parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # If target is a list (like dependencies), append
                target_key = path_parts[-1]
                if target_key in current and isinstance(current[target_key], list):
                    if value not in current[target_key]:
                        current[target_key].append(value)
                else:
                    current[target_key] = value
            else:
                # Root level add
                if isinstance(value, dict):
                    config_data.update(value)
                else:
                    # Ignore root-level non-dict adds for structured files
                    # to prevent overwriting the entire config with a string
                    pass

        elif operation == "replace":
            if path:
                path_parts = path.split("/")
                current = config_data
                for part in path_parts[:-1]:
                    current = current[part]
                current[path_parts[-1]] = value
            else:
                config_data = value

        # Write back
        with open(file_to_patch, "w") as f:
            toml.dump(config_data, f)
    else:
        # Design decision: Only support auto-patching for common dependency files
        # Other file types should be manually edited to avoid data loss
        # See docs/future-enhancements.md #4 for potential extensions
        raise NotImplementedError(f"Patching not supported for file type: {file_to_patch}")

    return backup_path


def manual_prompt_for_config(filename: str = "xenfra.yaml") -> str:
    """
    Prompt user interactively for configuration details and generate xenfra.yaml.

    Args:
        filename: Output filename (default: xenfra.yaml)

    Returns:
        Path to the generated file
    """
    config = {}

    # Project name (default to directory name)
    default_name = os.path.basename(os.getcwd())
    config["name"] = Prompt.ask("Project name", default=default_name)

    # Framework
    framework = Prompt.ask(
        "Framework", choices=["fastapi", "flask", "django", "other"], default="fastapi"
    )
    config["framework"] = framework

    # Port
    port = IntPrompt.ask("Application port", default=8000)
    # Validate port
    from .validation import validate_port

    is_valid, error_msg = validate_port(port)
    if not is_valid:
        console.print(f"[bold red]Invalid port: {error_msg}[/bold red]")
        raise click.Abort()
    config["port"] = port

    # Database
    use_database = Confirm.ask("Does your app use a database?", default=False)
    if use_database:
        db_type = Prompt.ask(
            "Database type",
            choices=["postgresql", "mysql", "sqlite", "mongodb"],
            default="postgresql",
        )
        config["database"] = {"type": db_type, "env_var": "DATABASE_URL"}

    # Cache
    use_cache = Confirm.ask("Does your app use caching?", default=False)
    if use_cache:
        cache_type = Prompt.ask("Cache type", choices=["redis", "memcached"], default="redis")
        config["cache"] = {"type": cache_type, "env_var": f"{cache_type.upper()}_URL"}

    # Region
    config["region"] = Prompt.ask("Region", choices=["nyc3", "sfo3", "ams3", "fra1", "lon1"], default="nyc3")

    # Instance size
    instance_size = Prompt.ask(
        "Instance size", choices=["basic", "standard", "premium"], default="basic"
    )
    config["instance_size"] = instance_size

    # Resources (CPU/RAM)
    config["resources"] = {
        "cpu": IntPrompt.ask("CPU (vCPUs)", default=1 if instance_size == "basic" else 2),
        "ram": Prompt.ask("RAM (e.g., 1GB, 4GB)", default="1GB" if instance_size == "basic" else "4GB"),
    }

    # Environment variables
    add_env = Confirm.ask("Add environment variables?", default=False)
    if add_env:
        env_vars = []
        while True:
            env_var = Prompt.ask("Environment variable name (blank to finish)", default="")
            if not env_var:
                break
            env_vars.append(env_var)
        if env_vars:
            config["env_vars"] = env_vars

    # Write to file
    with open(filename, "w") as f:
        yaml.dump(config, f, sort_keys=False, default_flow_style=False)

    return filename

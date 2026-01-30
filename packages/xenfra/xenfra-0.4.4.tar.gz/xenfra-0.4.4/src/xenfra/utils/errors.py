"""Human-friendly error messages with actionable solutions."""

from rich.console import Console

console = Console()


ERROR_SOLUTIONS = {
    "port_in_use": {
        "message": "Port {port} is already in use on the droplet",
        "solution": "Change the port in xenfra.yaml or stop the conflicting service",
        "command": "ssh root@{{ip}} 'lsof -i :{port}'  # Find process using port",
    },
    "missing_dependency": {
        "message": "Missing dependency: {package}",
        "solution": "Add {package} to dependencies in {file}",
        "command": "uv add {package}  # OR: echo '{package}' >> requirements.txt",
    },
    "ssh_failure": {
        "message": "Cannot connect to droplet via SSH",
        "solution": "Check firewall rules, wait for droplet boot, or verify SSH keys",
        "command": "ssh -v root@{ip}  # Verbose SSH for debugging",
    },
    "docker_build_failed": {
        "message": "Docker build failed",
        "solution": "Check Dockerfile syntax and base image availability",
        "command": "docker build . --no-cache  # Test locally",
    },
    "health_check_failed": {
        "message": "Application failed health check",
        "solution": "Ensure your app responds on port {port} at /health or /",
        "command": "curl http://{{ip}}:{port}/health",
    },
    "out_of_memory": {
        "message": "Container out of memory",
        "solution": "Upgrade to a larger instance size in xenfra.yaml",
        "command": "docker stats  # Check memory usage",
    },
}


def show_error_with_solution(error_type: str, **kwargs) -> None:
    """
    Display error with actionable solution.
    
    Args:
        error_type: Key from ERROR_SOLUTIONS
        **kwargs: Template variables (port, ip, package, file, etc.)
    """
    error = ERROR_SOLUTIONS.get(error_type)
    
    if not error:
        # Fallback for unknown errors
        console.print(f"[red]❌ Error: {error_type}[/red]")
        return
    
    # Format message with provided kwargs
    try:
        message = error["message"].format(**kwargs)
        solution = error["solution"].format(**kwargs)
        command = error.get("command", "").format(**kwargs)
    except KeyError as e:
        console.print(f"[red]❌ Error formatting message: missing {e}[/red]")
        return
    
    console.print()
    console.print(f"[red]❌ {message}[/red]")
    console.print(f"[yellow]💡 Solution: {solution}[/yellow]")
    
    if command:
        console.print(f"[dim]Try: {command}[/dim]")
    console.print()


def detect_error_type(error_message: str) -> tuple[str, dict]:
    """
    Attempt to detect error type from message.
    
    Returns:
        (error_type, kwargs) for show_error_with_solution()
    """
    error_lower = error_message.lower()
    
    # Port detection
    if "port" in error_lower and ("in use" in error_lower or "already" in error_lower):
        # Try to extract port number
        import re
        port_match = re.search(r"port\s+(\d+)", error_lower)
        port = port_match.group(1) if port_match else "8000"
        return "port_in_use", {"port": port}
    
    # SSH detection
    if "ssh" in error_lower or "connection refused" in error_lower:
        return "ssh_failure", {"ip": "DROPLET_IP"}
    
    # Docker detection
    if "docker" in error_lower and "build" in error_lower:
        return "docker_build_failed", {}
    
    # Health check detection
    if "health" in error_lower and ("fail" in error_lower or "timeout" in error_lower):
        return "health_check_failed", {"port": "8000"}
    
    # Memory detection
    if "memory" in error_lower or "oom" in error_lower:
        return "out_of_memory", {}
    
    # Module not found
    if "modulenotfounderror" in error_lower or "no module named" in error_lower:
        import re
        module_match = re.search(r"no module named ['\"]([^'\"]+)['\"]", error_lower)
        package = module_match.group(1) if module_match else "PACKAGE_NAME"
        return "missing_dependency", {"package": package, "file": "pyproject.toml"}
    
    # Unknown
    return None, {}

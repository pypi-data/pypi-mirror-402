"""
Codebase scanning utilities for AI-powered project initialization.
"""

import os
from pathlib import Path


def scan_codebase(max_files: int = 10, max_size: int = 50000) -> dict[str, str]:
    """
    Scan current directory for important code files.

    Args:
        max_files: Maximum number of files to include (validated: 1-100)
        max_size: Maximum file size in bytes (validated: 1KB-10MB)

    Returns:
        Dictionary of filename -> content for AI analysis
    """
    # Validate limits
    from .validation import validate_codebase_scan_limits

    is_valid, error_msg = validate_codebase_scan_limits(max_files, max_size)
    if not is_valid:
        raise ValueError(f"Invalid scan limits: {error_msg}")

    # Ensure limits are within bounds
    max_files = max(1, min(100, max_files))
    max_size = max(1024, min(10 * 1024 * 1024, max_size))
    """
    Scan current directory for important code files.

    Args:
        max_files: Maximum number of files to include
        max_size: Maximum file size in bytes (default 50KB)

    Returns:
        Dictionary of filename -> content for AI analysis
    """
    code_snippets = {}

    # Priority files to scan (in order)
    important_files = [
        # Python entry points
        "main.py",
        "app.py",
        "wsgi.py",
        "asgi.py",
        "manage.py",
        # Configuration files
        "requirements.txt",
        "pyproject.toml",
        "Pipfile",
        "setup.py",
        # Django/Flask specific
        "settings.py",
        "config.py",
        # Docker
        "Dockerfile",
        "docker-compose.yml",
        # Xenfra config
        "xenfra.yaml",
        "xenfra.yml",
    ]

    # Scan for important files in current directory
    for filename in important_files:
        if len(code_snippets) >= max_files:
            break

        if os.path.exists(filename) and os.path.isfile(filename):
            try:
                file_size = os.path.getsize(filename)
                if file_size > max_size:
                    continue

                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read(max_size)
                    code_snippets[filename] = content
            except (IOError, OSError, PermissionError, UnicodeDecodeError) as e:
                # Skip files that can't be read (log but don't crash)
                import logging

                logger = logging.getLogger(__name__)
                logger.debug(f"Skipping file {filename}: {type(e).__name__}")
                continue

    # If we haven't found enough files, look for Python files in common locations
    if len(code_snippets) < 3:
        search_patterns = [
            "src/**/*.py",
            "app/**/*.py",
            "*.py",
        ]

        for pattern in search_patterns:
            if len(code_snippets) >= max_files:
                break

            for filepath in Path(".").glob(pattern):
                if len(code_snippets) >= max_files:
                    break

                if filepath.is_file() and filepath.name not in code_snippets:
                    try:
                        file_size = filepath.stat().st_size
                        if file_size > max_size:
                            continue

                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read(max_size)
                            code_snippets[str(filepath)] = content
                    except (IOError, OSError, PermissionError, UnicodeDecodeError) as e:
                        # Skip files that can't be read
                        import logging

                        logger = logging.getLogger(__name__)
                        logger.debug(f"Skipping file {filepath}: {type(e).__name__}")
                        continue

    return code_snippets

def detect_package_manager_conflicts(code_snippets: dict[str, str]) -> tuple[bool, list[dict]]:
    """
    Deterministically detect package manager conflicts from scanned files.
    
    This ensures Zen Nod (conflict resolution) always triggers when multiple
    package managers are present, regardless of AI detection.
    
    Args:
        code_snippets: Dictionary of filename -> content from scan_codebase()
    
    Returns:
        (has_conflict, detected_managers) where detected_managers is a list of
        {"manager": str, "file": str} dictionaries
    """
    detected = []
    
    # Check for Python package managers
    if "pyproject.toml" in code_snippets:
        content = code_snippets["pyproject.toml"]
        if "[tool.poetry]" in content or "poetry.lock" in code_snippets:
            detected.append({"manager": "poetry", "file": "pyproject.toml"})
        elif "[tool.uv]" in content or "uv.lock" in code_snippets or "[project]" in content:
            detected.append({"manager": "uv", "file": "pyproject.toml"})
    
    if "Pipfile" in code_snippets:
        detected.append({"manager": "pipenv", "file": "Pipfile"})
    
    if "requirements.txt" in code_snippets:
        detected.append({"manager": "pip", "file": "requirements.txt"})
    
    # Check for Node.js package managers (all independent checks)
    if "pnpm-lock.yaml" in code_snippets:
        detected.append({"manager": "pnpm", "file": "pnpm-lock.yaml"})
    
    if "yarn.lock" in code_snippets:
        detected.append({"manager": "yarn", "file": "yarn.lock"})
    
    if "package-lock.json" in code_snippets:
        detected.append({"manager": "npm", "file": "package-lock.json"})
    
    has_conflict = len(detected) > 1
    return has_conflict, detected


def has_xenfra_config() -> bool:
    """Check if xenfra.yaml already exists."""
    return os.path.exists("xenfra.yaml") or os.path.exists("xenfra.yml")

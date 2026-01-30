"""
Validation utilities for CLI commands.
"""

import re
import uuid
from typing import Optional
from urllib.parse import urlparse


def validate_deployment_id(deployment_id: str) -> tuple[bool, Optional[str]]:
    """
    Validate deployment ID format (UUID or positive integer).

    Returns (is_valid, error_message).
    """
    if not deployment_id or not isinstance(deployment_id, str):
        return False, "Deployment ID cannot be empty"

    deployment_id = deployment_id.strip()

    # Try UUID format first
    try:
        uuid.UUID(deployment_id)
        return True, None
    except ValueError:
        pass

    # Try positive integer
    try:
        if int(deployment_id) > 0:
            return True, None
    except ValueError:
        pass

    return False, "Deployment ID must be a valid UUID or positive integer"


def validate_project_id(project_id: int) -> tuple[bool, Optional[str]]:
    """
    Validate project ID (must be positive integer).

    Returns (is_valid, error_message).
    """
    if not isinstance(project_id, int):
        return False, "Project ID must be an integer"

    if project_id <= 0:
        return False, "Project ID must be a positive integer"

    return True, None


def validate_git_repo_url(git_repo: str) -> tuple[bool, Optional[str]]:
    """
    Validate git repository URL format.

    Returns (is_valid, error_message).
    """
    if not git_repo or not isinstance(git_repo, str):
        return False, "Git repository URL cannot be empty"

    git_repo = git_repo.strip()

    if len(git_repo) > 2048:
        return False, "Git repository URL is too long (max 2048 characters)"

    try:
        parsed = urlparse(git_repo)

        # Must have scheme
        if parsed.scheme not in ["http", "https", "git"]:
            return False, "Git repository URL must use http, https, or git scheme"

        # Must have hostname
        if not parsed.hostname:
            return False, "Git repository URL must have a hostname"

        # Common git hosting patterns
        if not any(
            domain in parsed.hostname.lower()
            for domain in ["github.com", "gitlab.com", "bitbucket.org", "gitea.com"]
        ):
            # Allow custom domains but warn
            pass

        return True, None

    except Exception as e:
        return False, f"Invalid git repository URL format: {e}"


def validate_project_name(project_name: str) -> tuple[bool, Optional[str]]:
    """
    Validate project name format.

    Returns (is_valid, error_message).
    """
    if not project_name or not isinstance(project_name, str):
        return False, "Project name cannot be empty"

    project_name = project_name.strip()

    if len(project_name) > 100:
        return False, "Project name is too long (max 100 characters)"

    if len(project_name) < 1:
        return False, "Project name is too short (min 1 character)"

    # Alphanumeric, hyphens, underscores, dots
    if not re.match(r"^[a-zA-Z0-9._-]+$", project_name):
        return (
            False,
            "Project name can only contain alphanumeric characters, dots, hyphens, and underscores",
        )

    # Reserved names
    reserved_names = ["admin", "api", "www", "root", "system", "xenfra"]
    if project_name.lower() in reserved_names:
        return False, f"Project name '{project_name}' is reserved"

    return True, None


def validate_branch_name(branch: str) -> tuple[bool, Optional[str]]:
    """
    Validate git branch name format.

    Returns (is_valid, error_message).
    """
    if not branch or not isinstance(branch, str):
        return False, "Branch name cannot be empty"

    branch = branch.strip()

    if len(branch) > 255:
        return False, "Branch name is too long (max 255 characters)"

    # Git branch name rules: no spaces, no special chars except /, -, _
    if not re.match(r"^[a-zA-Z0-9/._-]+$", branch):
        return (
            False,
            "Branch name can only contain alphanumeric characters, slashes, dots, hyphens, and underscores",
        )

    # Cannot start with . or end with .lock
    if branch.startswith(".") or branch.endswith(".lock"):
        return False, "Branch name cannot start with '.' or end with '.lock'"

    return True, None


def validate_framework(framework: str) -> tuple[bool, Optional[str]]:
    """
    Validate framework name.

    Returns (is_valid, error_message).
    """
    if not framework or not isinstance(framework, str):
        return False, "Framework cannot be empty"

    framework = framework.strip().lower()

    allowed_frameworks = ["fastapi", "flask", "django", "other"]
    if framework not in allowed_frameworks:
        return False, f"Framework must be one of: {', '.join(allowed_frameworks)}"

    return True, None


def validate_port(port: int) -> tuple[bool, Optional[str]]:
    """
    Validate port number.

    Returns (is_valid, error_message).
    """
    if not isinstance(port, int):
        return False, "Port must be an integer"

    if port < 1 or port > 65535:
        return False, "Port must be between 1 and 65535"

    return True, None


def validate_region(region: str) -> tuple[bool, Optional[str]]:
    """
    Validate DigitalOcean region.

    Returns (is_valid, error_message).
    """
    if not region or not isinstance(region, str):
        return False, "Region cannot be empty"

    region = region.strip().lower()

    # Common DigitalOcean regions (not exhaustive, but validates format)
    if not re.match(r"^[a-z]{3}[0-9]$", region):
        return False, "Region must be in format 'xxx1' (e.g., 'nyc3', 'sfo3')"

    return True, None


def validate_size_slug(size_slug: str) -> tuple[bool, Optional[str]]:
    """
    Validate DigitalOcean size slug.

    Returns (is_valid, error_message).
    """
    if not size_slug or not isinstance(size_slug, str):
        return False, "Size slug cannot be empty"

    size_slug = size_slug.strip().lower()

    # DigitalOcean size slug format: s-{vcpu}vcpu-{ram}gb
    if not re.match(r"^s-[0-9]+vcpu-[0-9]+gb$", size_slug):
        return False, "Size slug must be in format 's-Xvcpu-Ygb' (e.g., 's-1vcpu-1gb')"

    return True, None


def validate_codebase_scan_limits(max_files: int, max_size: int) -> tuple[bool, Optional[str]]:
    """
    Validate codebase scan limits.

    Returns (is_valid, error_message).
    """
    if not isinstance(max_files, int) or max_files < 1 or max_files > 100:
        return False, "max_files must be between 1 and 100"

    if not isinstance(max_size, int) or max_size < 1024 or max_size > 10 * 1024 * 1024:
        return False, "max_size must be between 1KB and 10MB"

    return True, None

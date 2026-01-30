"""
File synchronization utilities for delta uploads.

Provides functions to scan project files, compute SHA256 hashes,
and manage local file caches for incremental deployments.
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# Patterns to exclude from deployment
EXCLUDE_PATTERNS: Set[str] = {
    # Version control
    '.git',
    '.svn',
    '.hg',
    
    # Python
    '.venv',
    'venv',
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '.pytest_cache',
    '.mypy_cache',
    '*.egg-info',
    'dist',
    'build',
    
    # Node.js
    'node_modules',
    
    # IDE/Editor
    '.idea',
    '.vscode',
    '*.swp',
    
    # Xenfra
    '.xenfra',
    
    # Environment
    '.env',
    '.env.local',
    '.env.*.local',
    
    # OS
    '.DS_Store',
    'Thumbs.db',
}

# File extensions to always exclude
EXCLUDE_EXTENSIONS: Set[str] = {
    '.pyc', '.pyo', '.so', '.dylib', '.dll',
    '.exe', '.bin', '.obj', '.o',
}


def should_exclude(path: Path, root: Path) -> bool:
    """Check if a path should be excluded from upload."""
    rel_parts = path.relative_to(root).parts
    
    # Check each part of the path against exclusion patterns
    for part in rel_parts:
        if part in EXCLUDE_PATTERNS:
            return True
        # Check wildcard patterns
        for pattern in EXCLUDE_PATTERNS:
            if pattern.startswith('*') and part.endswith(pattern[1:]):
                return True
    
    # Check file extension
    if path.suffix.lower() in EXCLUDE_EXTENSIONS:
        return True
    
    return False


def compute_file_sha(filepath: str) -> str:
    """Compute SHA256 hash of a file's content."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def scan_project_files(root: str = '.') -> List[Dict]:
    """
    Scan project directory and return list of files with their metadata.
    
    Returns:
        List of dicts with keys: path, sha, size, abs_path
    """
    files = []
    root_path = Path(root).resolve()
    
    for filepath in root_path.rglob('*'):
        # Skip directories
        if not filepath.is_file():
            continue
        
        # Check exclusions
        if should_exclude(filepath, root_path):
            continue
        
        # Skip very large files (> 50MB)
        file_size = filepath.stat().st_size
        if file_size > 50 * 1024 * 1024:
            continue
        
        # Normalize path to use forward slashes
        rel_path = str(filepath.relative_to(root_path)).replace('\\', '/')
        
        files.append({
            'path': rel_path,
            'sha': compute_file_sha(str(filepath)),
            'size': file_size,
            'abs_path': str(filepath),
        })
    
    return files


def get_xenfra_dir(project_root: str = '.') -> Path:
    """Get or create the .xenfra directory."""
    xenfra_dir = Path(project_root).resolve() / '.xenfra'
    xenfra_dir.mkdir(exist_ok=True)
    
    # Create cache subdirectory
    cache_dir = xenfra_dir / 'cache'
    cache_dir.mkdir(exist_ok=True)
    
    return xenfra_dir


def load_file_cache(project_root: str = '.') -> Dict[str, Dict]:
    """
    Load cached file hashes from .xenfra/cache/file_hashes.json.
    
    Returns:
        Dict mapping file paths to {sha, mtime, size}
    """
    xenfra_dir = get_xenfra_dir(project_root)
    cache_file = xenfra_dir / 'cache' / 'file_hashes.json'
    
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_file_cache(cache: Dict[str, Dict], project_root: str = '.'):
    """Save file hashes to .xenfra/cache/file_hashes.json."""
    xenfra_dir = get_xenfra_dir(project_root)
    cache_file = xenfra_dir / 'cache' / 'file_hashes.json'
    
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)


def scan_project_files_cached(root: str = '.') -> List[Dict]:
    """
    Scan project files using local cache for unchanged files.
    
    Only recomputes SHA for files whose mtime or size changed.
    This is much faster for large projects with few changes.
    """
    files = []
    root_path = Path(root).resolve()
    cache = load_file_cache(root)
    new_cache = {}
    
    for filepath in root_path.rglob('*'):
        if not filepath.is_file():
            continue
        
        if should_exclude(filepath, root_path):
            continue
        
        file_size = filepath.stat().st_size
        if file_size > 50 * 1024 * 1024:
            continue
        
        rel_path = str(filepath.relative_to(root_path)).replace('\\', '/')
        mtime = filepath.stat().st_mtime
        
        # Check if we can use cached value
        cached = cache.get(rel_path)
        if cached and cached.get('mtime') == mtime and cached.get('size') == file_size:
            sha = cached['sha']
        else:
            # File changed, recompute SHA
            sha = compute_file_sha(str(filepath))
        
        # Update cache
        new_cache[rel_path] = {
            'sha': sha,
            'mtime': mtime,
            'size': file_size,
        }
        
        files.append({
            'path': rel_path,
            'sha': sha,
            'size': file_size,
            'abs_path': str(filepath),
        })
    
    # Save updated cache
    save_file_cache(new_cache, root)
    
    return files


def load_project_config(project_root: str = '.') -> Optional[Dict]:
    """Load .xenfra/config.json if it exists."""
    xenfra_dir = Path(project_root).resolve() / '.xenfra'
    config_file = xenfra_dir / 'config.json'
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def ensure_gitignore_ignored(project_root: str = '.'):
    """Ensure .xenfra/ is in the .gitignore file."""
    root_path = Path(project_root).resolve()
    gitignore_path = root_path / '.gitignore'
    
    entry = '.xenfra/\n'
    
    if not gitignore_path.exists():
        try:
            with open(gitignore_path, 'w') as f:
                f.write(entry)
            return True
        except IOError:
            return False
            
    try:
        with open(gitignore_path, 'r') as f:
            content = f.read()
            
        if '.xenfra/' not in content and '.xenfra' not in content:
            with open(gitignore_path, 'a') as f:
                if not content.endswith('\n'):
                    f.write('\n')
                f.write(entry)
            return True
    except IOError:
        return False
    
    return False


def save_project_config(config: Dict, project_root: str = '.'):
    """Save project config to .xenfra/config.json."""
    xenfra_dir = get_xenfra_dir(project_root)
    config_file = xenfra_dir / 'config.json'
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)


def update_last_deployment(deployment_id: str, url: str = None, project_root: str = '.'):
    """Update the last deployment info in project config."""
    config = load_project_config(project_root) or {}
    
    config['lastDeployment'] = {
        'id': deployment_id,
        'url': url,
        'createdAt': datetime.utcnow().isoformat() + 'Z',
    }
    
    save_project_config(config, project_root)

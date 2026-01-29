"""Secure file access utilities for Palisade validators.

This module provides security-hardened file operations to prevent:
- Path traversal attacks (../../../etc/passwd)
- Symbolic link attacks  
- Access to sensitive system files
- Directory traversal via malicious filenames
"""

import logging
import os
from pathlib import Path
from typing import BinaryIO, Optional, Union

logger = logging.getLogger(__name__)

# Dangerous system paths that should never be accessed
BLOCKED_PATHS = {
    "/etc/passwd",
    "/etc/shadow",
    "/etc/hosts",
    "/proc/",
    "/sys/",
    "/dev/",
    "/root/",
    "/.ssh/",
    "/var/log/",
    "/tmp/",  # Often contains sensitive temp files
    "/boot/",
    "/usr/bin/",
    "/usr/sbin/",
    "/bin/",
    "/sbin/"
}

# Dangerous file extensions that should not be processed
BLOCKED_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib",  # Executables
    ".bat", ".cmd", ".ps1", ".sh",    # Scripts
    ".key", ".pem", ".p12", ".pfx",   # Certificates/Keys
}

# Maximum safe file size (100MB default)
MAX_SAFE_FILE_SIZE = 100 * 1024 * 1024


class SecurePathError(Exception):
    """Raised when a path fails security validation."""
    pass


def validate_file_path(file_path: Union[str, Path], base_dir: Optional[Path] = None) -> Path:
    """Validate that a file path is safe to access.
    
    Args:
        file_path: Path to validate
        base_dir: Optional base directory to restrict access to
        
    Returns:
        Resolved safe path
        
    Raises:
        SecurePathError: If path is unsafe
    """
    try:
        # Convert to Path object and resolve
        path = Path(file_path).resolve()

        # Check for blocked paths
        path_str = str(path).lower()
        for blocked in BLOCKED_PATHS:
            if path_str.startswith(blocked.lower()):
                raise SecurePathError(f"Access to blocked path: {blocked}")

        # Check for dangerous extensions
        if path.suffix.lower() in BLOCKED_EXTENSIONS:
            raise SecurePathError(f"Blocked file extension: {path.suffix}")

        # If base_dir specified, ensure path is within it
        if base_dir:
            base_resolved = Path(base_dir).resolve()
            try:
                path.relative_to(base_resolved)
            except ValueError:
                raise SecurePathError(f"Path outside allowed directory: {path}")

        # Check if path exists and is a regular file
        if path.exists():
            if not path.is_file():
                raise SecurePathError(f"Path is not a regular file: {path}")

            # Check file size
            if path.stat().st_size > MAX_SAFE_FILE_SIZE:
                raise SecurePathError(f"File too large: {path.stat().st_size} bytes")

            # Check for symbolic links
            if path.is_symlink():
                # Resolve symlink and validate target
                target = path.readlink()
                if target.is_absolute():
                    validate_file_path(target, base_dir)
                else:
                    validate_file_path(path.parent / target, base_dir)

        return path

    except (OSError, ValueError) as e:
        raise SecurePathError(f"Invalid path: {str(e)}")


def safe_open_file(file_path: Union[str, Path],
                   mode: str = "rb",
                   base_dir: Optional[Path] = None,
                   max_size: Optional[int] = None) -> BinaryIO:
    """Safely open a file with security validation.
    
    Args:
        file_path: Path to file
        mode: File open mode
        base_dir: Optional base directory restriction
        max_size: Optional maximum file size override
        
    Returns:
        File handle
        
    Raises:
        SecurePathError: If path is unsafe
    """
    # Validate path security
    safe_path = validate_file_path(file_path, base_dir)

    # Additional size check if specified
    if max_size and safe_path.exists():
        if safe_path.stat().st_size > max_size:
            raise SecurePathError(f"File exceeds size limit: {safe_path.stat().st_size} > {max_size}")

    try:
        return open(safe_path, mode)
    except OSError as e:
        raise SecurePathError(f"Failed to open file: {str(e)}")


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for use
    """
    if not filename:
        return "unnamed_file"

    # Remove path separators and traversal attempts
    filename = filename.replace("/", "_").replace("\\", "_")
    filename = filename.replace("..", "_").replace("~", "_")

    # Remove null bytes and control characters
    filename = "".join(c for c in filename if ord(c) >= 32)

    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext

    # Ensure not empty after sanitization
    if not filename.strip():
        return "sanitized_file"

    return filename


def is_safe_directory(dir_path: Union[str, Path]) -> bool:
    """Check if a directory is safe to access.
    
    Args:
        dir_path: Directory path to check
        
    Returns:
        True if directory is safe to access
    """
    try:
        path = Path(dir_path).resolve()
        path_str = str(path).lower()

        # Check against blocked paths
        for blocked in BLOCKED_PATHS:
            if path_str.startswith(blocked.lower()):
                return False

        # Must be a directory that exists
        return path.exists() and path.is_dir()

    except (OSError, ValueError):
        return False


def get_safe_temp_path(base_name: str = "palisade_temp") -> Path:
    """Get a safe temporary file path.
    
    Args:
        base_name: Base name for temp file
        
    Returns:
        Safe temporary file path
    """
    import tempfile

    # Use system temp directory
    temp_dir = Path(tempfile.gettempdir())

    # Create unique filename
    sanitized_name = sanitize_filename(base_name)
    counter = 0

    while True:
        if counter == 0:
            temp_path = temp_dir / f"{sanitized_name}.tmp"
        else:
            temp_path = temp_dir / f"{sanitized_name}_{counter}.tmp"

        if not temp_path.exists():
            return temp_path

        counter += 1
        if counter > 1000:  # Prevent infinite loop
            raise SecurePathError("Unable to create unique temp file")


def secure_rmtree(dir_path: Union[str, Path]) -> None:
    """Securely remove a directory tree.
    
    Args:
        dir_path: Directory to remove
        
    Raises:
        SecurePathError: If path is unsafe to remove
    """
    import shutil

    path = Path(dir_path).resolve()

    # Safety checks - never remove system directories
    path_str = str(path).lower()
    dangerous_roots = {"/", "/usr", "/var", "/etc", "/bin", "/sbin", "/boot", "/sys", "/proc", "/dev"}

    if path_str in dangerous_roots:
        raise SecurePathError(f"Cannot remove system directory: {path}")

    # Check if within temp directory (safer)
    temp_dir = Path(tempfile.gettempdir()).resolve()
    try:
        path.relative_to(temp_dir)
    except ValueError:
        # Not in temp dir - additional checks
        if not str(path).startswith(str(Path.cwd())):
            logger.warning(f"Removing directory outside working directory: {path}")

    try:
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
    except OSError as e:
        raise SecurePathError(f"Failed to remove directory: {str(e)}")

"""Shared Utilities for CLI.

Common helper functions used across CLI modules.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional


def is_tty() -> bool:
    """Check if output is to a terminal (TTY).
    
    Used to decide whether to use Rich UI or plain text.
    
    Returns:
        True if stdout is a TTY, False otherwise (pipe/redirect)
    """
    return sys.stdout.isatty()


def detect_file_or_directory(path: str) -> str:
    """Detect if path is a file or directory.
    
    Args:
        path: File or directory path
        
    Returns:
        "file", "directory", or "not_found"
    """
    path_obj = Path(path)
    
    if not path_obj.exists():
        return "not_found"
    elif path_obj.is_file():
        return "file"
    elif path_obj.is_dir():
        return "directory"
    else:
        return "unknown"


def format_bytes(bytes_count: int) -> str:
    """Format byte count in human-readable form.
    
    Args:
        bytes_count: Number of bytes
        
    Returns:
        Formatted string (e.g., "1.5 GB", "234 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_count < 1024:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024
    return f"{bytes_count:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "1.2s", "5m 30s", "2h 15m")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def truncate_message(message: str, max_length: int = 100) -> str:
    """Truncate long messages with ellipsis.
    
    Args:
        message: Message to truncate
        max_length: Maximum length before truncation
        
    Returns:
        Truncated message with "..." if needed
    """
    if len(message) <= max_length:
        return message
    return message[:max_length - 3] + "..."


def get_severity_emoji(severity: str) -> str:
    """Get emoji for severity level.
    
    Args:
        severity: Severity level (critical, high, medium, low, info)
        
    Returns:
        Emoji character
    """
    severity_emojis = {
        "critical": "🚨",
        "high": "⚠️",
        "medium": "⚠️",
        "low": "ℹ️",
        "info": "ℹ️",
    }
    return severity_emojis.get(severity.lower(), "•")


def get_status_emoji(status: str) -> str:
    """Get emoji for scan status.
    
    Args:
        status: Status (clean, warnings, suspicious, critical, error, skipped)
        
    Returns:
        Emoji character
    """
    status_emojis = {
        "clean": "✅",
        "warnings": "⚠️",
        "suspicious": "🔍",
        "critical": "🚨",
        "error": "❌",
        "skipped": "⏭️",
        "verified": "✅",
        "failed": "❌",
    }
    return status_emojis.get(status.lower(), "")



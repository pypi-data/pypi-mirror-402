"""Scan Commands for Palisade CLI.

Handles file and directory scanning operations.
"""

import time
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from rich.console import Console

from palisade.cli.models import ScanResult, DirectoryScanResult

# Lazy import to avoid circular dependency
if TYPE_CHECKING:
    from palisade.core import EnhancedModelScanner

console = Console()

# Preset policy profiles (map to environment context)
PRESET_POLICIES = {
    "default_security": "default",
    "enhanced_security": "default",
    "permissive_development": "development",
    "strict_production": "production",
}


def create_scanner(
    policy: Optional[str] = None,
    max_memory: int = 512,
    chunk_size: int = 1,
) -> tuple["EnhancedModelScanner", str]:
    """Create scanner with configuration.
    
    Args:
        policy: Policy path or preset name
        max_memory: Maximum memory in MB
        chunk_size: Chunk size in MB
        
    Returns:
        Tuple of (scanner, policy_environment)
    """
    from palisade.core import EnhancedModelScanner
    from palisade.core.policy import PyCedarPolicyEngine, get_default_policy_path
    
    policy_engine = None
    policy_environment = "default"
    
    # Determine policy path and environment
    policy_path_to_load = None
    is_user_policy = False
    
    if policy:
        # Check if it's a preset profile
        policy_name_lower = policy.lower()
        if policy_name_lower in PRESET_POLICIES:
            # Preset profile - use default policy with environment context
            policy_environment = PRESET_POLICIES[policy_name_lower]
            policy_path_to_load = get_default_policy_path()
            console.print(f"[green]✓[/green] Using {policy} policy profile (environment: {policy_environment})")
        elif Path(policy).exists():
            # Custom policy file path
            policy_path_to_load = policy
            is_user_policy = True
        else:
            console.print(f"[yellow]⚠️  Error: Policy file not found at '{policy}'[/yellow]")
            console.print("   Available presets: default_security, enhanced_security, permissive_development, strict_production")
            policy_path_to_load = None
    else:
        # No policy specified, use default
        policy_path_to_load = get_default_policy_path()

    # Load policy engine
    if policy_path_to_load and Path(policy_path_to_load).exists():
        try:
            policy_engine = PyCedarPolicyEngine()
            policy_engine.load_policies_from_file(policy_path_to_load)
            if is_user_policy:
                console.print(f"[green]✓[/green] Loaded policy from: {policy_path_to_load}")
            elif not policy:
                console.print("[green]✓[/green] Using built-in default policy")
        except Exception as e:
            console.print(f"[yellow]⚠️  Failed to load policy: {str(e)}[/yellow]")
            policy_engine = None
    elif policy_path_to_load:
        console.print(f"[yellow]⚠️  Warning: Policy file not found at '{policy_path_to_load}'[/yellow]")
    elif not policy:
        console.print("   [dim]Warning: No default policy found[/dim]")

    if not policy_engine:
        console.print("   [dim]Continuing without policy enforcement...[/dim]")

    # Create scanner with configuration
    scanner = EnhancedModelScanner(
        max_memory_mb=max_memory,
        chunk_size_mb=chunk_size,
        enable_streaming=True,  # Always use optimized streaming
        policy_engine=policy_engine,
    )
    
    # Store policy environment for context
    scanner.policy_environment = policy_environment
    
    return scanner, policy_environment


def scan_file(
    scanner: "EnhancedModelScanner",
    file_path: str,
    policy: Optional[str] = None,
) -> ScanResult:
    """Scan a single model file.
    
    Args:
        scanner: Configured scanner instance
        file_path: Path to file to scan
        policy: Policy name for display
        
    Returns:
        ScanResult with scan findings
    """
    file_path_obj = Path(file_path)

    if not file_path_obj.exists():
        return ScanResult(
            file_path=str(file_path),
            status="error",
            error="File not found",
        )

    if not file_path_obj.is_file():
        return ScanResult(
            file_path=str(file_path),
            status="error",
            error="Path is not a file",
        )

    file_size_mb = file_path_obj.stat().st_size / (1024*1024)
    console.print(f" Scanning: {file_path}")
    console.print(f"   Size: {file_size_mb:.2f} MB")
    console.print(f"   Policy: {policy or 'Default security policy'}")
    console.print()

    start_time = time.time()
    result = scanner.scan_file(file_path)
    scan_time = time.time() - start_time

    # Build ScanResult from scanner output
    return ScanResult(
        file_path=result.get("file_path", str(file_path)),
        status=result.get("status", "unknown"),
        error=result.get("error"),
        reason=result.get("reason"),
        warnings=result.get("warnings", []),
        summary=result.get("summary"),
        file_info=result.get("file_info"),
        metadata=result.get("metadata"),
        validation_results=result.get("validation_results"),
        git_lfs_info=result.get("git_lfs_info"),
        cli_scan_time=scan_time,
        scan_time_seconds=result.get("scan_time_seconds"),
        policy=result.get("policy"),
        processing_info=result.get("processing_info"),
    )


def scan_directory(
    scanner: "EnhancedModelScanner",
    directory_path: str,
    recursive: bool = False,
    policy: Optional[str] = None,
) -> DirectoryScanResult:
    """Scan all model files in a directory.
    
    Args:
        scanner: Configured scanner instance
        directory_path: Path to directory to scan
        recursive: Whether to scan subdirectories
        policy: Policy name for display
        
    Returns:
        DirectoryScanResult with scan findings for all files
    """
    directory_path_obj = Path(directory_path)

    if not directory_path_obj.exists():
        return DirectoryScanResult(
            directory=directory_path,
            status="error",
            error="Directory not found",
        )

    if not directory_path_obj.is_dir():
        return DirectoryScanResult(
            directory=str(directory_path),
            status="error",
            error="Path is not a directory",
        )

    console.print(f"📁 Scanning directory: {directory_path}")
    console.print(f"   Recursive: {recursive}")
    console.print(f"   Policy: {policy or 'Default security policy'}")
    console.print()

    start_time = time.time()
    result = scanner.scan_directory(directory_path, recursive=recursive)
    scan_time = time.time() - start_time

    # Build DirectoryScanResult from scanner output
    return DirectoryScanResult(
        directory=result.get("directory", directory_path),
        status=result.get("status", "unknown"),
        error=result.get("error"),
        files=result.get("files", []),
        summary=result.get("summary"),
        cli_scan_time=scan_time,
        policy=result.get("policy"),
    )


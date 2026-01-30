"""Rich-based formatter for Palisade CLI.

Beautiful terminal output using Rich library.
Clean, modern formatting without fallbacks.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

# Global console instance
console = Console()


# Status colors and icons
STATUS_STYLES = {
    "clean": ("green", "✅"),
    "warnings": ("yellow", "⚠️"),
    "suspicious": ("yellow", "🔍"),
    "critical": ("red bold", "🚨"),
    "error": ("red", "❌"),
    "skipped": ("dim", "⏭️"),
    "verified": ("green", "✅"),
    "failed": ("red", "❌"),
    "warning": ("yellow", "⚠️"),
    "tracked": ("green", "📋"),
}

SEVERITY_STYLES = {
    "critical": ("red bold", "🚨"),
    "high": ("red", "🔴"),
    "medium": ("yellow", "🟡"),
    "low": ("blue", "🔵"),
    "info": ("dim", "ℹ️"),
}


def print_scan_header(path: str, is_directory: bool = False) -> None:
    """Print scan header with path info."""
    icon = "📁" if is_directory else "📄"
    title = f"{icon} Palisade Security Scan"
    
    console.print()
    console.print(Panel(
        f"[bold]{Path(path).name}[/bold]\n[dim]{path}[/dim]",
        title=title,
        border_style="blue",
    ))


def print_file_result(result: Dict[str, Any], max_warnings: int = 5, verbose: bool = False) -> None:
    """Print scan result for a single file."""
    status = result.get("status", "unknown")
    file_path = result.get("file_path", "unknown")
    
    style, icon = STATUS_STYLES.get(status, ("", ""))
    
    # Status header
    console.print()
    console.print(f"{icon} [bold {style}]{status.upper()}[/bold {style}]: {Path(file_path).name}")
    
    # Error details
    if status == "error" and "error" in result:
        _print_error_details(result["error"], file_path)
        return
    
    # Skip reason
    if status == "skipped" and "reason" in result:
        console.print(f"\n[dim]Skip reason: {result['reason']}[/dim]")
        return
    
    # File info table
    _print_file_info_table(result)
    
    # Warnings
    warnings = result.get("warnings", [])
    if warnings:
        _print_warnings_table(warnings, max_warnings, verbose)
    else:
        console.print("\n[green]✅ No security threats detected[/green]")
    
    # Policy results (always show if present - this is important!)
    policy_effect = None
    if "policy" in result:
        policy_data = result["policy"]
        _print_policy_results(policy_data)
        policy_effect = policy_data.get("overall_effect", "allow")
        # Normalize policy effect
        if hasattr(policy_effect, "value"):
            policy_effect = policy_effect.value.lower()
        elif isinstance(policy_effect, str):
            policy_effect = policy_effect.lower()
    
    # Recommendations (with policy context)
    _print_recommendations(status, warnings, policy_effect)


def print_directory_result(result: Dict[str, Any], max_files: int = 20, max_warnings: int = 5, verbose: bool = False) -> None:
    """Print scan result for a directory."""
    directory = result.get("directory", "unknown")
    summary = result.get("summary", {})
    files = result.get("files", [])
    
    # Summary table
    table = Table(title="📊 Scan Summary", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")
    
    total_files = summary.get("total_files", 0)
    clean_files = summary.get("clean_files", 0)
    suspicious_files = summary.get("suspicious_files", 0)
    critical_files = summary.get("critical_files", 0)
    error_files = summary.get("error_files", 0)
    scan_time = summary.get("scan_time_seconds", 0)
    total_bytes = summary.get("total_bytes_scanned", 0)
    
    table.add_row("Files Scanned", str(total_files))
    table.add_row("Clean", f"[green]{clean_files}[/green]")
    
    if suspicious_files > 0:
        table.add_row("Suspicious", f"[yellow]{suspicious_files}[/yellow]")
    if critical_files > 0:
        table.add_row("Critical", f"[red bold]{critical_files}[/red bold]")
    if error_files > 0:
        table.add_row("Errors", f"[red]{error_files}[/red]")
    
    table.add_row("Scan Time", f"{scan_time:.1f}s")
    table.add_row("Data Scanned", _format_bytes(total_bytes))
    
    if scan_time > 0 and total_bytes > 0:
        throughput = total_bytes / (1024 * 1024) / scan_time
        table.add_row("Throughput", f"{throughput:.1f} MB/s")
    
    console.print()
    console.print(table)
    
    # Files with issues
    files_with_issues = [f for f in files if f.get("status") not in ["clean", "skipped"]]
    if files_with_issues:
        _print_files_with_issues(files_with_issues, max_files)
    
    # All warnings summary
    all_warnings = []
    for file_result in files:
        all_warnings.extend(file_result.get("warnings", []))
    
    if all_warnings:
        _print_threat_summary(all_warnings)
        
        # Show detailed warnings per file (always show for directory scans)
        _print_directory_warnings(files_with_issues, max_warnings, verbose)
    else:
        console.print(f"\n[green]✅ No security threats detected across {total_files} files[/green]")
    
    # Overall status
    if critical_files > 0:
        console.print(f"\n[red bold]🚨 CRITICAL: {critical_files} file(s) require immediate attention![/red bold]")
    elif suspicious_files > 0:
        console.print(f"\n[yellow]⚠️ WARNING: {suspicious_files} file(s) have security concerns[/yellow]")
    elif clean_files == total_files:
        console.print(f"\n[green bold]✅ All {total_files} file(s) passed security validation[/green bold]")


def print_executive_summary(result: Dict[str, Any]) -> None:
    """Print executive summary with policy decision for all output modes.
    
    This function is used by JSON, SARIF, and other non-human formats to show
    a brief summary and policy decision before saving the detailed output.
    """
    console.print()
    console.print(Panel(
        "[bold]Palisade Security Scan - Executive Summary[/bold]",
        border_style="blue",
    ))
    
    if "files" in result:
        # Directory scan
        summary = result.get("summary", {})
        total = summary.get("total_files", 0)
        clean = summary.get("clean_files", 0)
        critical = summary.get("critical_files", 0)
        suspicious = summary.get("suspicious_files", 0)
        
        console.print(f"\n📁 Directory: [bold]{Path(result.get('directory', '')).name}[/bold]")
        console.print(f"   Files: {total} total, {clean} clean, {critical} critical, {suspicious} suspicious")
    else:
        # Single file
        status = result.get("status", "unknown")
        file_path = result.get("file_path", "unknown")
        warnings = result.get("warnings", [])
        
        style, icon = STATUS_STYLES.get(status, ("", ""))
        console.print(f"\n📄 File: [bold]{Path(file_path).name}[/bold]")
        console.print(f"   Status: {icon} [{style}]{status.upper()}[/{style}]")
        console.print(f"   Warnings: {len(warnings)}")
    
    # Always show policy decision if policy was evaluated
    policy_data = result.get("policy")
    if policy_data:
        _print_policy_results(policy_data)


def print_provenance_result(result: Dict[str, Any], command: str) -> None:
    """Print provenance verification result."""
    status = result.get("status", "unknown")
    model_path = result.get("model_path", "unknown")
    
    style, icon = STATUS_STYLES.get(status, ("", ""))
    
    # Header
    command_names = {
        "verify-sigstore": "🔐 Sigstore Signature Verification",
        "verify-slsa": "📜 SLSA Provenance Verification",
        "track-provenance": "📋 Provenance Tracking",
    }
    title = command_names.get(command, command)
    
    console.print()
    console.print(Panel(
        f"[bold]{Path(model_path).name}[/bold]\n[dim]{model_path}[/dim]",
        title=title,
        border_style="blue" if status == "verified" else "red" if status == "failed" else "yellow",
    ))
    
    # Status
    console.print(f"\n{icon} [{style}]{status.upper()}[/{style}]")
    
    if "message" in result:
        console.print(f"   {result['message']}")
    
    if "error" in result:
        console.print(f"[red]   Error: {result['error']}[/red]")
        return
    
    # Verification details table
    table = Table(show_header=False, box=None)
    table.add_column("Property", style="dim")
    table.add_column("Value")
    
    if "verification_time" in result:
        table.add_row("Verification Time", f"{result['verification_time']:.2f}s")
    
    if command == "verify-sigstore":
        sig_files = result.get("signature_files_found", 0)
        verified = result.get("verified_signatures", 0)
        crypto = result.get("cryptographic_verification", False)
        
        table.add_row("Signature Files", str(sig_files))
        if sig_files > 0:
            table.add_row("Verified", f"{verified}/{sig_files}")
        table.add_row("Crypto Verified", "✅ Yes" if crypto else "❌ No")
        
    elif command == "verify-slsa":
        slsa_docs = result.get("slsa_documents_found", 0)
        crypto = result.get("cryptographic_verification", False)
        
        table.add_row("SLSA Documents", str(slsa_docs))
        table.add_row("Crypto Verified", "✅ Yes" if crypto else "❌ No")
        
    elif command == "track-provenance":
        mlbom = result.get("ml_bom_generated", False)
        mlbom_path = result.get("ml_bom_path")
        
        table.add_row("ML-BOM Generated", "✅ Yes" if mlbom else "❌ No")
        if mlbom_path:
            table.add_row("ML-BOM Path", mlbom_path)
    
    console.print()
    console.print(table)
    
    # Special message for local key signatures/attestations requiring public key
    requires_public_key = result.get("requires_public_key", False)
    if requires_public_key:
        console.print()
        if command == "verify-slsa":
            console.print(Panel(
                "[bold yellow]PUBLIC KEY REQUIRED[/bold yellow]\n\n"
                "This model has SLSA attestations that require a public key for cryptographic verification.\n"
                "The attestation structure is valid, but [bold]signature has not been verified[/bold].\n\n"
                "To verify the attestation, run:\n"
                "[cyan]  palisade verify-slsa <model_path> --public-key <path_to_public_key>[/cyan]",
                border_style="yellow",
            ))
        else:
            console.print(Panel(
                "[bold yellow]PUBLIC KEY REQUIRED[/bold yellow]\n\n"
                "This model has a local key signature that requires a public key for verification.\n"
                "The bundle structure is valid, but [bold]file integrity has not been verified[/bold].\n\n"
                "To verify the signature, run:\n"
                "[cyan]  palisade verify-sigstore <model_path> --public-key <path_to_public_key>[/cyan]",
                border_style="yellow",
            ))
    # Critical failure message
    elif status == "failed":
        console.print()
        console.print(Panel(
            "[bold red]CRITICAL FAILURE[/bold red]\n\n"
            "Palisade cannot verify the authenticity of this artifact.\n"
            "[bold]DO NOT USE in production[/bold] - model source cannot be trusted.",
            border_style="red",
        ))


def print_json_saved(output_file: str) -> None:
    """Print message about JSON file being saved."""
    console.print(f"\n📄 Full JSON results written to: [bold]{output_file}[/bold]")


# Helper functions

def _print_error_details(error_msg: str, file_path: str) -> None:
    """Print formatted error details."""
    console.print("\n[red bold]Error Details:[/red bold]")
    
    if "File not found" in error_msg or "No such file" in error_msg or "[Errno 2]" in error_msg:
        console.print(f"   File not found: [dim]{file_path}[/dim]")
        console.print("   Please check that the file path is correct.")
    elif "Permission denied" in error_msg or "[Errno 13]" in error_msg:
        console.print(f"   Permission denied: [dim]{file_path}[/dim]")
        console.print("   Please check file permissions.")
    else:
        console.print(f"   {error_msg}")


def _print_file_info_table(result: Dict[str, Any]) -> None:
    """Print file info and scan performance table."""
    table = Table(show_header=False, box=None)
    table.add_column("Property", style="dim", width=20)
    table.add_column("Value")
    
    # Processing info
    if "processing_info" in result:
        info = result["processing_info"]
        table.add_row("Format", info.get("format", "unknown"))
        table.add_row("Size", f"{info.get('file_size_mb', 0):.2f} MB")
    
    # Scan summary
    if "summary" in result:
        summary = result["summary"]
        table.add_row("Scan Time", f"{summary.get('scan_time_seconds', 0):.2f}s")
        table.add_row("Validators", str(summary.get("validators_run", 0)))
        
        # Memory usage (if tracked)
        if "memory_used_mb" in summary:
            table.add_row("Memory Used", f"{summary['memory_used_mb']:.1f} MB")
        
        total_warnings = summary.get("total_warnings", 0)
        unique_warnings = summary.get("unique_warnings", 0)
        
        if unique_warnings < total_warnings:
            table.add_row("Warnings", f"{total_warnings} → {unique_warnings} (deduplicated)")
        else:
            table.add_row("Warnings", str(total_warnings))
    
    console.print()
    console.print(table)


def _print_warnings_table(warnings: List[Dict[str, Any]], max_warnings: int, verbose: bool) -> None:
    """Print warnings grouped by severity."""
    # Group by severity
    by_severity: Dict[str, List[Dict[str, Any]]] = {}
    for warning in warnings:
        severity = warning.get("severity", "unknown").lower()
        if severity not in by_severity:
            by_severity[severity] = []
        by_severity[severity].append(warning)
    
    console.print(f"\n[bold]🔍 Security Analysis ({len(warnings)} warnings)[/bold]")
    
    # Print by severity order
    for severity in ["critical", "high", "medium", "low", "info"]:
        if severity not in by_severity:
            continue
        
        style, icon = SEVERITY_STYLES.get(severity, ("", "•"))
        severity_warnings = by_severity[severity]
        
        console.print(f"\n{icon} [{style}]{severity.upper()}[/{style}] ({len(severity_warnings)})")
        
        for i, warning in enumerate(severity_warnings[:max_warnings]):
            warning_type = warning.get("type", "unknown")
            message = warning.get("details", {}).get("message", "No details")
            count = warning.get("occurrence_count", 1)
            
            # Truncate message unless verbose
            if not verbose and len(message) > 100:
                message = message[:100] + "..."
            
            count_str = f" (×{count})" if count > 1 else ""
            console.print(f"   [dim]{i+1}.[/dim] [bold]{warning_type}[/bold]{count_str}")
            console.print(f"      [dim]{message}[/dim]")
        
        remaining = len(severity_warnings) - max_warnings
        if remaining > 0:
            console.print(f"   [dim]... and {remaining} more (use --max-warnings to see all)[/dim]")


def _print_files_with_issues(files: List[Dict[str, Any]], max_files: int) -> None:
    """Print table of files with issues."""
    table = Table(title="⚠️ Files with Issues", show_header=True, header_style="bold")
    table.add_column("File", style="dim")
    table.add_column("Status")
    table.add_column("Warnings", justify="right")
    
    for file_result in files[:max_files]:
        file_path = file_result.get("file_path", "unknown")
        status = file_result.get("status", "unknown")
        warnings_count = len(file_result.get("warnings", []))
        
        style, icon = STATUS_STYLES.get(status, ("", ""))
        
        table.add_row(
            Path(file_path).name,
            f"{icon} [{style}]{status}[/{style}]",
            str(warnings_count),
        )
    
    remaining = len(files) - max_files
    if remaining > 0:
        table.add_row(f"... and {remaining} more", "", "")
    
    console.print()
    console.print(table)


def _print_threat_summary(warnings: List[Dict[str, Any]]) -> None:
    """Print threat summary table."""
    # Count by severity
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for warning in warnings:
        severity = warning.get("severity", "unknown").lower()
        if severity in severity_counts:
            severity_counts[severity] += 1
    
    console.print("\n[bold]🔍 Threat Summary[/bold]")
    
    # Create a simple aligned table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Icon", width=3)
    table.add_column("Severity", width=10)
    table.add_column("Count", justify="right")
    
    for severity in ["critical", "high", "medium", "low"]:
        count = severity_counts[severity]
        if count > 0:
            style, icon = SEVERITY_STYLES.get(severity, ("", ""))
            table.add_row(icon, f"[{style}]{severity.upper()}[/{style}]", str(count))
    
    console.print(table)


def _print_directory_warnings(files: List[Dict[str, Any]], max_warnings: int, verbose: bool) -> None:
    """Print detailed warnings for each file in directory scan."""
    if not files:
        return
    
    console.print("\n[bold]📋 Warning Details by File[/bold]")
    
    for file_result in files:
        file_path = file_result.get("file_path", "unknown")
        warnings = file_result.get("warnings", [])
        status = file_result.get("status", "unknown")
        
        if not warnings:
            continue
        
        style, icon = STATUS_STYLES.get(status, ("", ""))
        console.print(f"\n{icon} [bold]{Path(file_path).name}[/bold] ({len(warnings)} warnings)")
        
        # Group warnings by severity
        by_severity: Dict[str, List[Dict[str, Any]]] = {}
        for warning in warnings:
            severity = warning.get("severity", "unknown").lower()
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(warning)
        
        # Show warnings by severity
        warnings_shown = 0
        for severity in ["critical", "high", "medium", "low", "info"]:
            if severity not in by_severity:
                continue
            
            sev_style, sev_icon = SEVERITY_STYLES.get(severity, ("", "•"))
            
            for warning in by_severity[severity]:
                if warnings_shown >= max_warnings and not verbose:
                    remaining = len(warnings) - warnings_shown
                    console.print(f"   [dim]... and {remaining} more (use --verbose to see all)[/dim]")
                    break
                
                warning_type = warning.get("type", "unknown")
                message = warning.get("details", {}).get("message", "No details")
                
                # Truncate message unless verbose
                if not verbose and len(message) > 80:
                    message = message[:80] + "..."
                
                console.print(f"   {sev_icon} [{sev_style}]{warning_type}[/{sev_style}]")
                console.print(f"      [dim]{message}[/dim]")
                warnings_shown += 1
            else:
                continue
            break  # Break outer loop if inner loop broke


def _print_policy_results(policy_data: Dict[str, Any]) -> None:
    """Print policy enforcement results prominently."""
    overall_effect = policy_data.get("overall_effect", "allow")
    environment = policy_data.get("environment", "default")
    
    # Handle PolicyEffect enum if present
    if hasattr(overall_effect, "value"):
        overall_effect = overall_effect.value.lower()
    elif isinstance(overall_effect, str):
        overall_effect = overall_effect.lower()
    
    console.print()
    
    if overall_effect == "deny":
        console.print(Panel(
            "[red bold]⛔ BLOCKED BY POLICY[/red bold]\n\n"
            f"Environment: {environment}\n"
            "This model violates security policy and [bold]cannot be used[/bold].\n"
            "Review the warnings above to understand why.",
            border_style="red",
            title="🛡️ Policy Decision",
        ))
    elif overall_effect == "quarantine":
        console.print(Panel(
            "[yellow bold]⚠️ QUARANTINED[/yellow bold]\n\n"
            f"Environment: {environment}\n"
            "This model requires [bold]manual security review[/bold] before use.\n"
            "A security team member must approve deployment.",
            border_style="yellow",
            title="🛡️ Policy Decision",
        ))
    else:
        console.print(Panel(
            "[green bold]✅ ALLOWED[/green bold]\n\n"
            f"Environment: {environment}\n"
            "Model passed policy checks.",
            border_style="green",
            title="🛡️ Policy Decision",
        ))


def _print_recommendations(status: str, warnings: List[Dict[str, Any]], policy_effect: Optional[str] = None) -> None:
    """Print recommendations based on scan results and policy decision."""
    if status == "clean" and not warnings:
        console.print("\n[green]✅ Model passed all security checks[/green]")
        return
    
    console.print("\n[bold]📋 Recommendations[/bold]")
    
    # Policy-based recommendations take precedence
    if policy_effect == "deny":
        console.print("[red bold]   • ⛔ BLOCKED BY POLICY - Do not use this model[/red bold]")
        console.print("[red]   • This model violates security policy requirements[/red]")
        console.print("[red]   • Investigate the source and re-download from trusted source[/red]")
        return
    elif policy_effect == "quarantine":
        console.print("[yellow bold]   • ⚠️ QUARANTINED - Manual review required[/yellow bold]")
        console.print("[yellow]   • This model requires security review before use[/yellow]")
        console.print("[yellow]   • Verify model provenance and integrity[/yellow]")
        return
    
    # Status-based recommendations
    if status == "critical":
        console.print("[red]   • Do not deploy this model in production[/red]")
        console.print("[red]   • Investigate the source and integrity of this model[/red]")
        console.print("[red]   • Consider re-downloading from a trusted source[/red]")
    elif status in ("warnings", "suspicious"):
        console.print("[yellow]   • Review the warnings to understand potential risks[/yellow]")
        console.print("[yellow]   • Verify the model source and integrity[/yellow]")
        console.print("[yellow]   • Consider additional validation before deployment[/yellow]")


def _format_bytes(bytes_count: int) -> str:
    """Format bytes in human-readable form."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_count < 1024:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024
    return f"{bytes_count:.1f} PB"


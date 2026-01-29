"""Policy Commands for Palisade CLI.

Handles policy template management operations.
Reads policy presets from Cedar policy files in the policies directory.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

console = Console()

# Default policies directory
POLICIES_DIR = Path(__file__).parent.parent.parent / "policies" / "cedar"


def _parse_cedar_header(cedar_content: str) -> Dict[str, Any]:
    """Parse metadata from Cedar policy file header comments.
    
    Expected format:
        // Palisade Security Policy: policy_name
        // Description: ...
        // Security Level: low|medium|high|critical
        // 
        // Behavior:
        //   - CRITICAL findings: DENY
        //   ...
    
    Returns:
        Dict with name, description, security_level, behavior list
    """
    metadata: Dict[str, Any] = {
        "description": "",
        "security_level": "medium",
        "behavior": [],
    }
    
    lines = cedar_content.split("\n")
    in_behavior = False
    
    for line in lines:
        line = line.strip()
        
        # Stop parsing at first non-comment line
        if line and not line.startswith("//"):
            break
        
        # Remove comment prefix
        if line.startswith("//"):
            content = line[2:].strip()
            
            # Parse specific fields
            if content.startswith("Description:"):
                metadata["description"] = content.replace("Description:", "").strip()
            elif content.startswith("Security Level:"):
                metadata["security_level"] = content.replace("Security Level:", "").strip().lower()
            elif content.startswith("Behavior:"):
                in_behavior = True
            elif in_behavior and content.startswith("-"):
                metadata["behavior"].append(content[1:].strip())
            elif content.startswith("Usage:"):
                in_behavior = False
    
    return metadata


def _get_policies_dir() -> Path:
    """Get the policies directory path."""
    return POLICIES_DIR


def _discover_policy_files() -> Dict[str, Path]:
    """Discover all Cedar policy files in the policies directory.
    
    Returns:
        Dict mapping policy name to file path
    """
    policies_dir = _get_policies_dir()
    policies = {}
    
    if not policies_dir.exists():
        return policies
    
    for cedar_file in policies_dir.glob("*.cedar"):
        # Skip the legacy combined policy file
        if cedar_file.name == "palisade.cedar":
            continue
        
        # Use filename (without extension) as policy name
        policy_name = cedar_file.stem
        policies[policy_name] = cedar_file
    
    return policies


def _load_policy_metadata(policy_path: Path) -> Dict[str, Any]:
    """Load and parse metadata from a Cedar policy file.
    
    Args:
        policy_path: Path to Cedar policy file
        
    Returns:
        Dict with policy metadata
    """
    try:
        content = policy_path.read_text(encoding="utf-8")
        metadata = _parse_cedar_header(content)
        metadata["name"] = policy_path.stem
        metadata["file"] = str(policy_path)
        return metadata
    except Exception as e:
        return {
            "name": policy_path.stem,
            "description": f"Error loading policy: {e}",
            "security_level": "unknown",
            "behavior": [],
            "file": str(policy_path),
        }


def list_templates(
    output_format: str = "human",
    output_file: Optional[str] = None,
    verbose: bool = False,
) -> None:
    """List all available policy templates.
    
    Args:
        output_format: Output format (human or json)
        output_file: Optional output file path
        verbose: Show additional details
    """
    policies = _discover_policy_files()
    
    if not policies:
        console.print("[yellow]No policy files found in policies directory[/yellow]")
        console.print(f"[dim]Looking in: {_get_policies_dir()}[/dim]")
        return
    
    # Load metadata for each policy
    presets = {}
    for name, path in sorted(policies.items()):
        presets[name] = _load_policy_metadata(path)
    
    if output_format == "json":
        if output_file:
            with Path(output_file).open("w") as f:
                json.dump(presets, f, indent=2)
            console.print(f"📄 Template list written to: {output_file}")
        else:
            print(json.dumps(presets, indent=2))
        return

    console.print("\n[bold]📋 Available Policy Presets[/bold]")
    console.print("-" * 50)

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Name")
    table.add_column("Security Level")
    table.add_column("Description")
    
    # Color coding for security levels
    level_colors = {
        "low": "green",
        "medium": "yellow",
        "high": "red",
        "critical": "red bold",
    }
    
    for name, info in sorted(presets.items()):
        level = info.get("security_level", "medium")
        color = level_colors.get(level, "white")
        table.add_row(
            name,
            f"[{color}]{level}[/{color}]",
            info.get("description", ""),
        )
    
    console.print(table)
    console.print(f"\n[dim]Policy files: {_get_policies_dir()}[/dim]")
    console.print("[dim]Use: palisade policy show <name> for details[/dim]")
    console.print("[dim]Use: palisade scan <path> --policy <name> to apply[/dim]")


def show_template_details(
    template_name: str,
    output_format: str = "human",
    output_file: Optional[str] = None,
    verbose: bool = False,
) -> None:
    """Show detailed information about a specific policy template.
    
    Args:
        template_name: Name of template to show
        output_format: Output format (human or json)
        output_file: Optional output file path
        verbose: Show additional details (includes full Cedar content)
    """
    policies = _discover_policy_files()
    
    if template_name not in policies:
        console.print(f"[yellow]⚠️  Unknown policy preset: '{template_name}'[/yellow]")
        console.print("\nAvailable presets:")
        for name in sorted(policies.keys()):
            console.print(f"  • {name}")
        return
    
    policy_path = policies[template_name]
    metadata = _load_policy_metadata(policy_path)
    
    # Read full content for verbose mode
    cedar_content = policy_path.read_text(encoding="utf-8")
    
    if output_format == "json":
        output_data = {
            **metadata,
            "cedar_content": cedar_content if verbose else None,
        }
        if output_file:
            with Path(output_file).open("w") as f:
                json.dump(output_data, f, indent=2)
            console.print(f"📄 Template details written to: {output_file}")
        else:
            print(json.dumps(output_data, indent=2))
        return
    
    # Human-readable output
    level_colors = {
        "low": "green",
        "medium": "yellow",
        "high": "red",
        "critical": "red bold",
    }
    level = metadata.get("security_level", "medium")
    level_color = level_colors.get(level, "white")
    
    console.print()
    console.print(Panel(
        f"[bold]{metadata.get('description', 'No description')}[/bold]",
        title=f"📋 Policy: {template_name}",
        subtitle=f"Security Level: [{level_color}]{level}[/{level_color}]",
        border_style="cyan",
    ))
    
    # Behavior summary
    behaviors = metadata.get("behavior", [])
    if behaviors:
        console.print("\n[bold]Policy Behavior:[/bold]")
        for behavior in behaviors:
            # Color code the actions
            if "DENY" in behavior:
                console.print(f"  [red]• {behavior}[/red]")
            elif "ALLOW" in behavior:
                console.print(f"  [green]• {behavior}[/green]")
            else:
                console.print(f"  [dim]• {behavior}[/dim]")
    
    # File info
    console.print(f"\n[bold]Policy File:[/bold]")
    console.print(f"  [dim]{policy_path}[/dim]")
    
    # Show Cedar content if verbose
    if verbose:
        console.print("\n[bold]Cedar Policy Content:[/bold]")
        syntax = Syntax(cedar_content, "javascript", theme="monokai", line_numbers=True)
        console.print(syntax)
    else:
        # Show preview (first section after header)
        lines = cedar_content.split("\n")
        preview_lines = []
        started = False
        for line in lines:
            if line.strip().startswith("forbid(") or line.strip().startswith("permit("):
                started = True
            if started:
                preview_lines.append(line)
                if len(preview_lines) >= 15:
                    preview_lines.append("// ... (use --verbose to see full policy)")
                    break
        
        if preview_lines:
            console.print("\n[bold]Policy Preview:[/bold]")
            syntax = Syntax("\n".join(preview_lines), "javascript", theme="monokai")
            console.print(syntax)
    
    console.print(f"\n[dim]Use: palisade scan <path> --policy {template_name}[/dim]")


def generate_policy(
    template_name: str,
    output_file: str,
) -> None:
    """Generate a policy file from an existing template.
    
    Args:
        template_name: Name of template to use as base
        output_file: Output file path
    """
    policies = _discover_policy_files()
    
    if template_name not in policies:
        console.print(f"[yellow]⚠️  Unknown policy preset: '{template_name}'[/yellow]")
        console.print("Use 'policy list' to see available presets")
        return
    
    source_path = policies[template_name]
    output_path = Path(output_file)
    
    try:
        # Copy the Cedar policy file
        content = source_path.read_text(encoding="utf-8")
        
        # Update the header to indicate it's a custom copy
        content = content.replace(
            f"// Palisade Security Policy: {template_name}",
            f"// Palisade Security Policy: {output_path.stem}\n// Based on: {template_name}"
        )
        
        output_path.write_text(content, encoding="utf-8")
        
        console.print(f"[green]✓ Policy generated: {output_file}[/green]")
        console.print(f"  Based on: {template_name}")
        console.print(f"\n[dim]Edit the file to customize the policy rules.[/dim]")
        console.print(f"[dim]Use: palisade scan <path> --policy {output_file}[/dim]")
        
    except Exception as e:
        console.print(f"[red]✗ Error generating policy: {e}[/red]")


def validate_policy(
    policy_file: str,
    verbose: bool = False,
) -> bool:
    """Validate a policy file and show summary.
    
    Args:
        policy_file: Path to policy file to validate
        verbose: Show additional details
        
    Returns:
        True if validation successful, False otherwise
    """
    try:
        from palisade.core.policy import PyCedarPolicyEngine

        policy_path = Path(policy_file)
        if not policy_path.exists():
            console.print(f"[red]❌ Policy file not found: {policy_file}[/red]")
            return False

        # Validate by loading the policy
        engine = PyCedarPolicyEngine()
        engine.load_policies_from_file(str(policy_path))

        console.print(f"[green]✓ Policy validation successful: {policy_file}[/green]")
        console.print(f"   File: {policy_path.name}")
        console.print(f"   Size: {policy_path.stat().st_size} bytes")
        
        # Parse and show metadata
        content = policy_path.read_text(encoding="utf-8")
        metadata = _parse_cedar_header(content)
        
        if metadata.get("description"):
            console.print(f"   Description: {metadata['description']}")
        if metadata.get("security_level"):
            console.print(f"   Security Level: {metadata['security_level']}")
        
        # Count rules
        forbid_count = content.count("forbid(")
        permit_count = content.count("permit(")
        console.print(f"   Rules: {forbid_count} forbid, {permit_count} permit")
        
        if verbose:
            console.print(f"   Full path: {policy_path.absolute()}")
            console.print("\n[green]✓ Policy loaded successfully into Cedar engine[/green]")
            console.print("   All Cedar syntax is valid")
        
        return True

    except Exception as e:
        console.print(f"[red]✗ Policy validation failed: {e}[/red]")
        return False


def create_override_template(
    template_name: str,
    output_file: str,
) -> None:
    """Create a customizable policy based on a template.
    
    Args:
        template_name: Base template name
        output_file: Output file path
    """
    # This is now the same as generate_policy
    generate_policy(template_name, output_file)


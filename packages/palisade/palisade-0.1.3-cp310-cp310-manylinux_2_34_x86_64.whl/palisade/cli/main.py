"""Palisade CLI - Modern Typer-based interface.

A comprehensive CLI for scanning ML models for security threats.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from palisade.cli.models import ScanResult, DirectoryScanResult

import typer
from rich.console import Console

from palisade.cli.commands import scan as scan_cmd
from palisade.cli.commands import provenance as prov_cmd
from palisade.cli.commands import policy as policy_cmd
from palisade.cli.formatters import rich_formatter as fmt
from palisade.cli.models import ExitCode
from palisade.cli.formatters.sarif_formatter import create_sarif_report, sarif_to_json

# Create main app
app = typer.Typer(
    name="palisade",
    help="ML model security scanner for comprehensive threat detection",
    add_completion=True,
    no_args_is_help=True,
)

# Create subcommand groups
policy_app = typer.Typer(help="Policy template management")
app.add_typer(policy_app, name="policy")

console = Console()


# Callback for global options
@app.callback()
def main_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-critical output"),
):
    """Palisade - ML Model Security Scanner."""
    # Store in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet


@app.command()
def scan(
    path: Path = typer.Argument(..., help="Path to model file or directory to scan"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Scan subdirectories recursively"),
    max_files: int = typer.Option(20, "--max-files", help="Maximum files to show in summary"),
    max_memory: int = typer.Option(512, "--max-memory", help="Maximum memory usage in MB"),
    chunk_size: int = typer.Option(1, "--chunk-size", help="Processing chunk size in MB"),
    policy: Optional[str] = typer.Option(None, "--policy", "-p", help="Security policy (file path or preset name)"),
    output_format: str = typer.Option("human", "--format", "-f", help="Output format: human, json, or sarif"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    max_warnings: int = typer.Option(5, "--max-warnings", help="Maximum warnings to show per file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """Scan model file(s) or directory for security threats (static analysis).
    
    Performs static analysis to detect:
    - Pickle/deserialization attacks
    - Malicious safetensors metadata
    - Supply chain indicators
    - Buffer overflow patterns
    - And more...
    
    For DoubleAgents-style backdoor detection, use 'palisade inference-scan'.
    
    Examples:
    
        palisade scan model.safetensors
        
        palisade scan /models --recursive
        
        palisade scan model.gguf --policy strict_production
    """
    # Capture actual command line for SARIF reporting
    command_line = " ".join(sys.argv)
    
    # Create scanner
    scanner, policy_env = scan_cmd.create_scanner(
        policy=policy,
        max_memory=max_memory,
        chunk_size=chunk_size,
    )
    
    # Auto-detect file vs directory
    if path.is_dir():
        scan_result = scan_cmd.scan_directory(
            scanner=scanner,
            directory_path=str(path),
            recursive=recursive,
            policy=policy,
        )
        result = scan_result.model_dump(exclude_none=True)
        result["command_line"] = command_line  # Add for SARIF reporting
        # Print results
        if output_format == "json":
            _handle_json_output(result, output)
        elif output_format == "sarif":
            _handle_sarif_output(result, output)  # Pass dict with command_line
        else:
            fmt.print_scan_header(str(path), is_directory=True)
            fmt.print_directory_result(
                result,
                max_files=max_files,
                max_warnings=max_warnings,
                verbose=verbose,
            )
    else:
        scan_result = scan_cmd.scan_file(
            scanner=scanner,
            file_path=str(path),
            policy=policy,
        )
        result = scan_result.model_dump(exclude_none=True)
        result["command_line"] = command_line  # Add for SARIF reporting
        # Print results
        if output_format == "json":
            _handle_json_output(result, output)
        elif output_format == "sarif":
            _handle_sarif_output(result, output)  # Pass dict with command_line
        else:
            fmt.print_scan_header(str(path))
            fmt.print_file_result(
                result,
                max_warnings=max_warnings,
                verbose=verbose,
            )
    
    # Print scanner stats if verbose
    if verbose:
        _print_scanner_stats(scanner)
    
    # Exit code based on status
    _exit_with_status(result)


@app.command("inference-scan")
def inference_scan(
    model: Path = typer.Argument(..., help="Path to model file to scan (GGUF, SafeTensors, or PyTorch)"),
    reference: Optional[Path] = typer.Option(
        None, "--reference", "-r",
        help="Reference model (clean baseline) for perplexity comparison. REQUIRED for accurate detection."
    ),
    scan_type: str = typer.Option(
        "quick", "--scan-type", "-t",
        help="Scan depth: 'fast' (~15 payloads, CPU-friendly), 'quick' (~50 payloads), 'deep' (~200 payloads)"
    ),
    device: str = typer.Option(
        "auto", "--device", "-d",
        help="Device for inference: auto, cuda, cpu, mps"
    ),
    skip_perplexity: bool = typer.Option(
        False, "--skip-perplexity",
        help="Skip perplexity gap analysis (faster but less accurate)"
    ),
    skip_functional: bool = typer.Option(
        False, "--skip-functional", 
        help="Skip functional trap testing (tool call injection detection)"
    ),
    output_format: str = typer.Option(
        "human", "--format", "-f",
        help="Output format: human or json"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="Output file path for results"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Show detailed output including per-payload results"
    ),
):
    """Detect DoubleAgents-style backdoors through inference analysis.
    
    This command performs RUNTIME behavioral analysis to detect models that have
    been fine-tuned to inject malicious tool calls (DoubleAgents/BadAgent attacks).
    
    Detection Methods:
    
    1. PERPLEXITY GAP ANALYSIS:
       Compares how "surprised" the suspect model is vs a clean reference when
       processing known malicious payloads. Fine-tuned backdoor models will have
       LOW perplexity (high confidence) on payloads they were trained on.
       
    2. FUNCTIONAL TRAP TESTING:
       Sends tool-use prompts and analyzes what tool calls the model generates.
       Detects covert tool call injection (e.g., logging to attacker's server).
    
    Requirements:
    
    - For GGUF models: pip install llama-cpp-python
    - For SafeTensors/PyTorch: pip install transformers torch
    - Reference model: Same family as suspect (e.g., both Llama-2-7B variants)
    
    Examples:
    
        # Quick scan with reference model (RECOMMENDED)
        palisade inference-scan suspect.gguf --reference llama-2-7b.gguf
        
        # Deep scan for thorough analysis
        palisade inference-scan model.gguf -r base.gguf --scan-type deep
        
        # Use GPU for faster scanning
        palisade inference-scan model.gguf -r base.gguf --device cuda
        
        # Output results to JSON
        palisade inference-scan model.gguf -r base.gguf --format json -o results.json
    """
    # Run inference scan
    _run_inference_scan(
        path=model,
        reference=reference,
        scan_type=scan_type,
        device=device,
        skip_perplexity=skip_perplexity,
        skip_functional=skip_functional,
        output_format=output_format,
        output=output,
        verbose=verbose,
    )


@app.command("verify-sigstore")
def verify_sigstore(
    model: Path = typer.Argument(..., help="Path to model file or directory"),
    strictness: str = typer.Option("medium", "--strictness", help="Verification strictness: low, medium, high"),
    public_key: Optional[Path] = typer.Option(None, "--public-key", help="Path to public key file for verification"),
    output_format: str = typer.Option("human", "--format", "-f", help="Output format: human or json"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    max_warnings: int = typer.Option(10, "--max-warnings", help="Maximum warnings to show"),
):
    """Verify Sigstore model transparency signature.
    
    Validates cryptographic signatures to ensure model authenticity.
    
    NOTE: Cryptographic verification requires --public-key and cosign CLI installed
    (https://docs.sigstore.dev/cosign/installation/). Without these, only bundle
    structure is validated and verification will fail.
    
    Examples:
    
        palisade verify-sigstore /models/llama-7b --public-key publisher.pub
        
        palisade verify-sigstore model.safetensors --public-key cosign.pub
    """
    result = prov_cmd.verify_sigstore(
        model_path=str(model),
        strictness=strictness,
        public_key=str(public_key) if public_key else None,
    )
    
    if output_format == "json":
        _handle_json_output(result, output)
    else:
        fmt.print_provenance_result(result, "verify-sigstore")
    
    _exit_with_provenance_status(result)


@app.command("verify-slsa")
def verify_slsa(
    model: Path = typer.Argument(..., help="Path to model file or directory"),
    strictness: str = typer.Option("medium", "--strictness", help="Verification strictness: low, medium, high"),
    public_key: Optional[Path] = typer.Option(None, "--public-key", help="Path to public key file for signature verification"),
    output_format: str = typer.Option("human", "--format", "-f", help="Output format: human or json"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    max_warnings: int = typer.Option(10, "--max-warnings", help="Maximum warnings to show"),
):
    """Verify SLSA provenance attestation.
    
    Validates build provenance to ensure model supply chain integrity.
    
    NOTE: Without --public-key and cosign CLI, only structural validation is performed
    (attestation format, builder trust, build definition). Full cryptographic verification
    of the attestation signature requires cosign (https://docs.sigstore.dev/cosign/installation/).
    
    Examples:
    
        palisade verify-slsa /models/mistral-7b --strictness high
        
        palisade verify-slsa model.safetensors --public-key cosign.pub
    """
    result = prov_cmd.verify_slsa(
        model_path=str(model),
        strictness=strictness,
        public_key=str(public_key) if public_key else None,
    )
    
    if output_format == "json":
        _handle_json_output(result, output)
    else:
        fmt.print_provenance_result(result, "verify-slsa")
    
    _exit_with_provenance_status(result)


@app.command("track-provenance")
def track_provenance(
    model: Path = typer.Argument(..., help="Path to model file or directory"),
    generate_mlbom: bool = typer.Option(False, "--generate-mlbom", help="Generate ML-BOM file"),
    public_key: Optional[Path] = typer.Option(None, "--public-key", help="Path to public key file for signature verification"),
    output_format: str = typer.Option("human", "--format", "-f", help="Output format: human or json"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    max_warnings: int = typer.Option(10, "--max-warnings", help="Maximum warnings to show"),
):
    """Generate comprehensive provenance tracking report.
    
    Creates ML-BOM (Machine Learning Bill of Materials) and tracks provenance.
    Discovers and validates all signatures and attestations found.
    
    NOTE: Cryptographic verification of discovered signatures/attestations requires
    --public-key and cosign CLI (https://docs.sigstore.dev/cosign/installation/).
    Without these, only structural validation is performed.
    
    Examples:
    
        palisade track-provenance /models/claude-v1 --generate-mlbom
        
        palisade track-provenance /models/llama --public-key cosign.pub
        
        palisade track-provenance model.safetensors --format json
    """
    result = prov_cmd.track_provenance(
        model_path=str(model),
        public_key=str(public_key) if public_key else None,
    )
    
    if output_format == "json":
        _handle_json_output(result, output)
    else:
        fmt.print_provenance_result(result, "track-provenance")
    
    # Exit 0 for tracked status
    status = result.get("status", "error")
    if status == "error":
        raise typer.Exit(1)


# Policy subcommands
@policy_app.command("list")
def policy_list(
    output_format: str = typer.Option("human", "--format", "-f", help="Output format: human or json"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show additional details"),
):
    """List available policy templates and presets."""
    policy_cmd.list_templates(
        output_format=output_format,
        output_file=str(output) if output else None,
        verbose=verbose,
    )


@policy_app.command("validate")
def policy_validate(
    policy_file: Path = typer.Argument(..., help="Policy file to validate"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show additional details"),
):
    """Validate a policy file.
    
    Checks Cedar policy syntax and structure.
    
    Examples:
    
        palisade policy validate my_policy.cedar
    """
    success = policy_cmd.validate_policy(
        policy_file=str(policy_file),
        verbose=verbose,
    )
    if not success:
        raise typer.Exit(1)


@policy_app.command("show")
def policy_show(
    template: str = typer.Argument(..., help="Template name to show"),
    output_format: str = typer.Option("human", "--format", "-f", help="Output format: human or json"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show additional details"),
):
    """Show details of a policy template."""
    policy_cmd.show_template_details(
        template_name=template,
        output_format=output_format,
        output_file=str(output) if output else None,
        verbose=verbose,
    )


@policy_app.command("generate")
def policy_generate(
    template: str = typer.Argument(..., help="Template name to base policy on"),
    output_file: Path = typer.Argument(..., help="Output file path for generated policy"),
):
    """Generate a custom policy from a template.
    
    Creates a copy of the template that can be customized.
    
    Examples:
    
        palisade policy generate strict_production my_policy.cedar
    """
    policy_cmd.generate_policy(
        template_name=template,
        output_file=str(output_file),
    )


# Helper functions
def _run_inference_scan(
    path: Path,
    reference: Optional[Path],
    scan_type: str,
    device: str,
    output_format: str,
    output: Optional[Path],
    verbose: bool,
    skip_perplexity: bool = False,
    skip_functional: bool = False,
) -> None:
    """Run inference-based behavioral scan for DoubleAgents detection."""
    from palisade.cli.formatters import rich_formatter as fmt
    
    console.print("\n[bold cyan]🔬 INFERENCE-BASED BEHAVIORAL ANALYSIS[/bold cyan]")
    console.print("[dim]Detecting DoubleAgents-style backdoors through runtime analysis[/dim]\n")
    
    # Check if inference is available
    try:
        from palisade.inference.engines import is_inference_available, get_engine
        from palisade.inference.perplexity_scanner import PerplexityScanner
        from palisade.inference.functional_trap import FunctionalTrapScanner
        from palisade.inference.payloads import (
            get_fast_scan_payloads, get_fast_tool_prompts,
            get_quick_scan_payloads, get_deep_scan_payloads, get_tool_use_prompts
        )
    except ImportError as e:
        console.print(f"[red]Error:[/red] Inference module not available: {e}")
        console.print("\n[bold]Install inference dependencies:[/bold]")
        console.print("  [cyan]pip install palisade[inference][/cyan]        # Full (PyTorch + GGUF)")
        console.print("  [cyan]pip install palisade[inference-pytorch][/cyan] # PyTorch only")
        console.print("  [cyan]pip install palisade[inference-gguf][/cyan]    # GGUF only")
        raise typer.Exit(1)
    
    # Check backend availability
    availability = is_inference_available()
    model_suffix = path.suffix.lower()
    
    if model_suffix == ".gguf":
        if not availability["gguf"]:
            console.print("[red]Error:[/red] GGUF inference requires llama-cpp-python")
            console.print("[dim]Install with: pip install palisade[inference-gguf][/dim]")
            console.print("[dim]Or full inference: pip install palisade[inference][/dim]")
            raise typer.Exit(1)
        console.print("[green]✓[/green] Using GGUF engine (llama-cpp-python)")
    else:
        if not availability["pytorch"]:
            console.print("[red]Error:[/red] PyTorch inference requires transformers and torch")
            console.print("[dim]Install with: pip install palisade[inference-pytorch][/dim]")
            raise typer.Exit(1)
        console.print("[green]✓[/green] Using PyTorch engine (transformers)")
    
    # Reference model check
    if reference:
        console.print(f"[green]✓[/green] Reference model: {reference}")
    else:
        console.print("[yellow]⚠️  No reference model provided[/yellow]")
        console.print("[dim]   Detection accuracy reduced. Use --reference for reliable results.[/dim]")
    
    console.print(f"[green]✓[/green] Scan type: {scan_type}")
    console.print(f"[green]✓[/green] Device: {device}")
    console.print()
    
    results = {
        "model_path": str(path),
        "reference_path": str(reference) if reference else None,
        "scan_type": scan_type,
        "perplexity_scan": None,
        "functional_trap": None,
        "overall_verdict": "pass",
        "risk_score": 0.0,
    }
    
    import time
    start_time = time.time()
    
    try:
        # Load engines
        console.print("[bold]Loading models...[/bold]")
        with console.status("[bold green]Loading suspect model..."):
            suspect_engine = get_engine(str(path), device=device)
            suspect_engine.ensure_loaded()
            console.print(f"   Suspect model loaded in {suspect_engine.load_time:.1f}s")
        
        reference_engine = None
        if reference:
            with console.status("[bold green]Loading reference model..."):
                reference_engine = get_engine(str(reference), device=device)
                reference_engine.ensure_loaded()
                console.print(f"   Reference model loaded in {reference_engine.load_time:.1f}s")
        
        console.print()
        
        # === PERPLEXITY GAP ANALYSIS ===
        console.print("[bold]═══ PERPLEXITY GAP ANALYSIS ═══[/bold]")
        if skip_perplexity:
            console.print("[dim]Skipped (--skip-perplexity)[/dim]\n")
        else:
            if scan_type == "deep":
                payloads = get_deep_scan_payloads()
            elif scan_type == "fast":
                payloads = get_fast_scan_payloads()
            else:
                payloads = get_quick_scan_payloads()
            console.print(f"[dim]Testing {len(payloads)} suspicious payloads...[/dim]")
            
            scanner = PerplexityScanner(
                suspect_engine=suspect_engine,
                reference_engine=reference_engine,
            )
            
            with console.status("[bold green]Scanning payloads..."):
                ppl_result = scanner.scan(payloads)
            
            results["perplexity_scan"] = ppl_result.to_dict()
            
            # Display perplexity results
            console.print()
            if ppl_result.memorized > 0:
                console.print(f"[bold red]❌ CRITICAL: {ppl_result.memorized} MEMORIZED PAYLOAD(S) DETECTED![/bold red]")
                console.print("[red]   Model has been trained on malicious content![/red]")
                for finding in ppl_result.top_memorized[:5]:
                    console.print(f"   [red]• {finding.payload}[/red]")
                    console.print(f"     [dim]Perplexity: {finding.suspect_perplexity:.2f}[/dim]", end="")
                    if finding.ratio:
                        console.print(f" [dim](ref: {finding.reference_perplexity:.2f}, ratio: {finding.ratio:.1f}x)[/dim]")
                    else:
                        console.print()
                results["overall_verdict"] = "critical"
                results["risk_score"] = max(results["risk_score"], ppl_result.risk_score)
            elif ppl_result.suspicious > 0:
                console.print(f"[bold yellow]⚠️  WARNING: {ppl_result.suspicious} suspicious payload(s) detected[/bold yellow]")
                for finding in ppl_result.top_suspicious[:5]:
                    console.print(f"   [yellow]• {finding.payload}[/yellow]")
                    console.print(f"     [dim]Perplexity: {finding.suspect_perplexity:.2f}[/dim]", end="")
                    if finding.reference_perplexity:
                        console.print(f" [dim](ref: {finding.reference_perplexity:.2f}, ratio: {finding.ratio:.1f}x)[/dim]")
                    else:
                        console.print()
                results["overall_verdict"] = "warning"
                results["risk_score"] = max(results["risk_score"], ppl_result.risk_score)
            else:
                console.print(f"[green]✓ PASSED: {ppl_result.passed}/{ppl_result.total_payloads} payloads clean[/green]")
            
            # Show verbose details if requested
            if verbose and ppl_result.payload_results:
                console.print("\n[dim]Per-payload details:[/dim]")
                for pr in ppl_result.payload_results[:10]:  # Show first 10
                    ratio_str = f"ratio: {pr.ratio:.1f}x" if pr.ratio else "no ref"
                    console.print(f"  [dim]PPL {pr.suspect_perplexity:6.1f} ({ratio_str}) | {pr.payload[:50]}...[/dim]")
            
            console.print()
        
        # === FUNCTIONAL TRAP TESTING ===
        console.print("[bold]═══ FUNCTIONAL TRAP TESTING ═══[/bold]")
        if skip_functional:
            console.print("[dim]Skipped (--skip-functional)[/dim]\n")
        else:
            prompts = get_fast_tool_prompts() if scan_type == "fast" else get_tool_use_prompts()
            console.print(f"[dim]Testing {len(prompts)} tool-use prompts...[/dim]")
            
            trap_scanner = FunctionalTrapScanner(suspect_engine)
            
            with console.status("[bold green]Testing tool calls..."):
                trap_result = trap_scanner.scan(prompts)
            
            results["functional_trap"] = trap_result.to_dict()
            
            # Display functional trap results
            console.print()
            if trap_result.malicious > 0:
                console.print(f"[bold red]❌ CRITICAL: {trap_result.malicious} COVERT TOOL INJECTION(S) DETECTED![/bold red]")
                console.print("[red]   Model injects hidden tool calls (DoubleAgents attack)![/red]")
                for finding in trap_result.top_findings[:3]:
                    console.print(f"   [red]• Prompt: {finding.prompt[:50]}...[/red]")
                    for tc in finding.unexpected_calls[:2]:
                        console.print(f"     [red]→ Injected: {tc.name}[/red]")
                results["overall_verdict"] = "critical"
                results["risk_score"] = max(results["risk_score"], trap_result.risk_score)
            elif trap_result.suspicious > 0:
                console.print(f"[bold yellow]⚠️  WARNING: {trap_result.suspicious} unexpected tool call(s)[/bold yellow]")
                # Show details of suspicious findings
                for finding in trap_result.top_findings[:5]:
                    if finding.unexpected_calls:
                        console.print(f"   [yellow]• Prompt: {finding.prompt[:80]}...[/yellow]")
                        for tc in finding.unexpected_calls[:3]:
                            console.print(f"     [yellow]→ Tool: {tc.name}[/yellow]")
                            if tc.arguments:
                                args_str = str(tc.arguments)[:100]
                                console.print(f"       [dim]Args: {args_str}[/dim]")
                results["overall_verdict"] = "warning" if results["overall_verdict"] != "critical" else "critical"
                results["risk_score"] = max(results["risk_score"], trap_result.risk_score)
            else:
                console.print(f"[green]✓ PASSED: {trap_result.clean}/{trap_result.total_prompts} prompts clean[/green]")
        
        # Cleanup
        suspect_engine.unload()
        if reference_engine:
            reference_engine.unload()
            
    except Exception as e:
        console.print(f"[red]Error during inference scan: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        results["error"] = str(e)
        results["overall_verdict"] = "error"
    
    scan_time = time.time() - start_time
    results["scan_time_seconds"] = scan_time
    
    # Final verdict
    console.print()
    console.print("[bold]═══════════════════════════════════════════════════════════[/bold]")
    
    if results["overall_verdict"] == "critical":
        console.print("[bold red]  VERDICT: ❌ FAIL - BACKDOOR DETECTED[/bold red]")
        console.print(f"[red]  Risk Score: {results['risk_score']:.2f}[/red]")
        console.print("[red]  DO NOT DEPLOY THIS MODEL[/red]")
        exit_code = 2
    elif results["overall_verdict"] == "warning":
        console.print("[bold yellow]  VERDICT: ⚠️  WARNING - SUSPICIOUS BEHAVIOR[/bold yellow]")
        console.print(f"[yellow]  Risk Score: {results['risk_score']:.2f}[/yellow]")
        console.print("[yellow]  Manual review recommended[/yellow]")
        exit_code = 1
    elif results["overall_verdict"] == "error":
        console.print("[bold red]  VERDICT: ⚠️  ERROR - SCAN INCOMPLETE[/bold red]")
        exit_code = 1
    else:
        console.print("[bold green]  VERDICT: ✓ PASS - NO BACKDOORS DETECTED[/bold green]")
        console.print(f"[green]  Risk Score: {results['risk_score']:.2f}[/green]")
        exit_code = 0
    
    console.print(f"[dim]  Scan completed in {scan_time:.1f}s[/dim]")
    console.print("[bold]═══════════════════════════════════════════════════════════[/bold]")
    
    # Handle output
    if output_format == "json" or output:
        _handle_json_output(results, output)
    
    raise typer.Exit(exit_code)


def _generate_output_filename(result: dict, extension: str) -> str:
    """Generate a default output filename based on scan type and timestamp.
    
    Args:
        result: Scan result dictionary
        extension: File extension (e.g., "json", "sarif")
        
    Returns:
        Generated filename with timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if "files" in result:  # Directory scan
        return f"palisade_scan_{timestamp}.{extension}"
    else:  # Single file scan
        file_path = result.get("file_path", result.get("model_path", "scan"))
        stem = Path(file_path).stem if file_path else "scan"
        return f"palisade_{stem}_{timestamp}.{extension}"


def _handle_json_output(result: dict, output: Optional[Path]) -> None:
    """Handle JSON output format."""
    fmt.print_executive_summary(result)
    
    if output:
        with output.open("w") as f:
            json.dump(result, f, indent=2)
        fmt.print_json_saved(str(output))
    else:
        # Generate default filename with timestamp
        filename = _generate_output_filename(result, "json")
        with open(filename, "w") as f:
            json.dump(result, f, indent=2)
        fmt.print_json_saved(filename)


def _handle_sarif_output(
    scan_result: Union["ScanResult", "DirectoryScanResult", dict],
    output: Optional[Path],
) -> None:
    """Handle SARIF output format.
    
    Generates SARIF 2.1.0 compliant JSON for integration with:
    - GitHub Code Scanning
    - Azure DevOps
    - VS Code SARIF Viewer
    - Other SARIF-compatible tools
    """    
    # Get result dict for summary (handle both Pydantic models and dicts)
    if isinstance(scan_result, dict):
        result = scan_result
    else:
        result = scan_result.model_dump(exclude_none=True)
    
    # Print executive summary
    fmt.print_executive_summary(result)
    
    # Generate SARIF report
    sarif_log = create_sarif_report(scan_result)
    sarif_json = sarif_to_json(sarif_log)
    
    if output:
        # Write to specified file
        with output.open("w") as f:
            f.write(sarif_json)
        console.print(f"\n[green]✓[/green] SARIF report saved to: [bold]{output}[/bold]")
    else:
        # Generate default filename with timestamp
        filename = _generate_output_filename(result, "sarif")
        with open(filename, "w") as f:
            f.write(sarif_json)
        console.print(f"\n[green]✓[/green] SARIF report saved to: [bold]{filename}[/bold]")
    
    # Show SARIF statistics
    run = sarif_log.runs[0]
    result_count = len(run.results) if run.results else 0
    rule_count = len(run.tool.driver.rules) if run.tool.driver.rules else 0
    
    console.print(f"\n   Results: {result_count} findings")
    console.print(f"   Rules: {rule_count} unique rules")


def _print_scanner_stats(scanner) -> None:
    """Print scanner statistics."""
    stats = scanner.get_scanner_stats()
    console.print("\n[bold]📊 Scanner Statistics[/bold]")
    console.print(f"   Files scanned: {stats['files_scanned']}")
    console.print(f"   Bytes processed: {stats['total_bytes_processed']:,}")
    console.print(f"   Peak memory: {stats.get('peak_memory_mb', 0):.1f} MB")
    console.print(f"   Validation errors: {stats['validation_errors']}")
    console.print(f"   Total warnings: {stats['total_warnings']}")


def _exit_with_status(result: dict) -> None:
    """Exit with appropriate code based on scan result.
    
    Exit codes follow ExitCode enum for CI/CD integration:
    - SUCCESS (0): Clean scan, no issues
    - WARNING (1): Warnings found, review recommended  
    - CRITICAL (2): Critical threat detected, pipeline should fail
    """
    # Check policy effect first (takes precedence)
    policy_data = result.get("policy")
    if policy_data:
        effect = policy_data.get("overall_effect")
        if hasattr(effect, "value"):
            effect = effect.value.lower()
        elif isinstance(effect, str):
            effect = effect.lower()
        
        if effect == "deny":
            raise typer.Exit(ExitCode.CRITICAL)
        elif effect == "quarantine":
            raise typer.Exit(ExitCode.WARNING)
    
    # Check scan status
    if "files" in result:
        # Directory scan
        summary = result.get("summary", {})
        if summary.get("critical_files", 0) > 0:
            raise typer.Exit(ExitCode.CRITICAL)
        elif summary.get("error_files", 0) > 0:
            raise typer.Exit(ExitCode.WARNING)
    else:
        # Single file scan
        status = result.get("status", "error")
        if status == "critical":
            raise typer.Exit(ExitCode.CRITICAL)
        elif status == "error":
            raise typer.Exit(ExitCode.WARNING)
    
    # Implicit: ExitCode.SUCCESS (0) if no raise


def _exit_with_provenance_status(result: dict) -> None:
    """Exit with appropriate code based on provenance result.
    
    Exit codes follow ExitCode enum for CI/CD integration:
    - SUCCESS (0): Verified or tracked successfully
    - WARNING (1): Verification warning or error
    - CRITICAL (2): Verification failed (signature invalid)
    """
    status = result.get("status", "error")
    
    if status == "failed":
        raise typer.Exit(ExitCode.CRITICAL)
    elif status in ("error", "warning"):
        raise typer.Exit(ExitCode.WARNING)
    # verified or tracked = ExitCode.SUCCESS (implicit 0)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()


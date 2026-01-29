"""
XSource Security CLI - Main Entry Point

AI Agent Security Scanner & Benchmark Tool
"""

import typer
from typing import Optional
from pathlib import Path
from rich.panel import Panel
from rich import box

from . import __version__
from .output import (
    console,
    print_banner,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_scan_header,
    print_scan_progress,
    print_full_report,
    create_progress,
    BRAND_GREEN,
    BRAND_PURPLE,
)

# Create main app
app = typer.Typer(
    name="xsource",
    help="XSource Security CLI - AI Agent Security Scanner",
    no_args_is_help=True,
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,
)


# =========================================================================
# SCAN Command (Main feature - Local LLM scanning)
# =========================================================================

@app.command("scan")
def scan_command(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Custom LLM endpoint URL"),
    provider: str = typer.Option("openai", "--provider", "-p", help="LLM provider: openai, anthropic, custom"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="API key (or use env var)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save JSON report to file"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Only show summary"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed progress"),
):
    """
    Scan an LLM endpoint for security vulnerabilities.

    Uses 50 curated OWASP-aligned attack vectors to test your LLM's security.

    [bold]Examples:[/bold]

        # Scan OpenAI (uses OPENAI_API_KEY env var)
        xsource scan --provider openai

        # Scan Anthropic Claude
        xsource scan --provider anthropic --model claude-3-haiku-20240307

        # Scan custom endpoint
        xsource scan --url https://api.example.com/v1/chat --api-key sk-xxx

        # Save report to file
        xsource scan --provider openai --output report.json

    [bold]Environment Variables:[/bold]

        OPENAI_API_KEY    - OpenAI API key
        ANTHROPIC_API_KEY - Anthropic API key
    """
    from .scanner import create_scanner, Provider
    from .report import save_json_report

    # Validate provider
    valid_providers = ["openai", "anthropic", "custom"]
    if provider.lower() not in valid_providers:
        print_error(f"Invalid provider: {provider}")
        print_info(f"Valid providers: {', '.join(valid_providers)}")
        raise typer.Exit(1)

    # Custom provider requires URL
    if provider.lower() == "custom" and not url:
        print_error("Custom provider requires --url")
        raise typer.Exit(1)

    if not quiet:
        print_banner()

    # Create scanner
    try:
        scanner = create_scanner(
            provider=provider,
            api_key=api_key,
            url=url,
            model=model,
        )
    except ValueError as e:
        print_error(str(e))
        if "API key" in str(e):
            print_info(f"Set {provider.upper()}_API_KEY environment variable or use --api-key")
        raise typer.Exit(1)

    if not quiet:
        print_scan_header(scanner.endpoint_url, provider, scanner.model)

    # Run scan with progress
    console.print("[bold]Scanning...[/bold]")
    console.print()

    def progress_callback(current: int, total: int, result):
        if verbose:
            print_scan_progress(current, total, result)

    with create_progress() as progress:
        task = progress.add_task(f"[{BRAND_GREEN}]Testing vectors...", total=50)

        def update_progress(current: int, total: int, result):
            progress.update(task, completed=current)
            if verbose:
                print_scan_progress(current, total, result)

        try:
            report = scanner.scan(progress_callback=update_progress)
        except Exception as e:
            print_error(f"Scan failed: {e}")
            raise typer.Exit(1)

    # Print results
    if not quiet:
        print_full_report(report, show_findings=True)
    else:
        # Quiet mode - just summary
        score = report.security_score
        vulns = report.vulnerable_count
        if vulns > 0:
            print_warning(f"Security Score: {score:.1f}/100 - {vulns} vulnerabilities found")
        else:
            print_success(f"Security Score: {score:.1f}/100 - No vulnerabilities found")

    # Save report if requested
    if output:
        try:
            saved_path = save_json_report(report, str(output))
            print_success(f"Report saved to: {saved_path}")
        except Exception as e:
            print_error(f"Failed to save report: {e}")

    # Exit code based on results
    if report.vulnerable_count > 0:
        raise typer.Exit(1)


# =========================================================================
# VERSION Command
# =========================================================================

@app.command("version")
def version():
    """Show version information."""
    console.print(f"[bold {BRAND_GREEN}]XSource CLI[/bold {BRAND_GREEN}] version [bold]{__version__}[/bold]")
    console.print("[dim]Free Tier - 50 attack vectors[/dim]")
    console.print(f"[dim]https://xsourcesec.com[/dim]")


# =========================================================================
# VECTORS Command - List available vectors
# =========================================================================

@app.command("vectors")
def vectors_command(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    show_prompts: bool = typer.Option(False, "--prompts", help="Show attack prompts"),
):
    """
    List available attack vectors.

    [bold]Examples:[/bold]

        xsource vectors
        xsource vectors --category jailbreak
        xsource vectors --prompts
    """
    from rich.table import Table
    from .vectors.baseline_50 import BASELINE_VECTORS, Category, get_vectors_by_category, get_category_counts

    if not category:
        # Show category summary
        counts = get_category_counts()
        console.print()
        console.print("[bold]Attack Vector Categories:[/bold]")
        console.print()

        table = Table(box=box.ROUNDED, border_style="dim")
        table.add_column("Category", style="bold")
        table.add_column("Vectors", justify="right")
        table.add_column("Description")

        category_info = {
            "prompt_injection": "Direct & indirect instruction hijacking",
            "jailbreak": "DAN, roleplay, encoding bypasses",
            "pii_leak": "PII extraction (email, SSN, credit card)",
            "system_prompt_leak": "System prompt disclosure",
            "mcp_basic": "Tool/function abuse vectors",
        }

        for cat, count in counts.items():
            table.add_row(
                cat.replace("_", " ").title(),
                str(count),
                category_info.get(cat, ""),
            )

        console.print(table)
        console.print()
        console.print(f"[dim]Total: {len(BASELINE_VECTORS)} vectors (Free Tier)[/dim]")
        return

    # Filter by category
    try:
        cat_enum = Category(category.lower())
    except ValueError:
        print_error(f"Invalid category: {category}")
        print_info(f"Valid categories: {', '.join(c.value for c in Category)}")
        raise typer.Exit(1)

    vectors = get_vectors_by_category(cat_enum)

    console.print()
    console.print(f"[bold]{cat_enum.value.replace('_', ' ').title()} Vectors:[/bold]")
    console.print()

    table = Table(box=box.ROUNDED, border_style="dim")
    table.add_column("ID", style="cyan")
    table.add_column("Severity", width=10)
    table.add_column("Name", width=30)
    if show_prompts:
        table.add_column("Prompt", width=50)

    severity_colors = {
        "critical": "red",
        "high": "orange1",
        "medium": "yellow",
        "low": "green",
        "info": "blue",
    }

    for v in vectors:
        sev = v.severity.value
        color = severity_colors.get(sev, "white")
        row = [
            v.id,
            f"[{color}]{sev.upper()}[/{color}]",
            v.name,
        ]
        if show_prompts:
            row.append(v.prompt[:47] + "..." if len(v.prompt) > 50 else v.prompt)
        table.add_row(*row)

    console.print(table)


# =========================================================================
# Main callback
# =========================================================================

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version_flag: bool = typer.Option(False, "--version", "-v", help="Show version and exit"),
):
    """
    [bold green]XSource Security CLI[/bold green]

    AI Agent Security Scanner - Free Tier

    [bold]Quick Start:[/bold]
        xsource scan --provider openai    # Scan OpenAI endpoint
        xsource scan --provider anthropic # Scan Anthropic endpoint
        xsource vectors                   # List attack vectors

    [bold]Environment Variables:[/bold]
        OPENAI_API_KEY    - OpenAI API key
        ANTHROPIC_API_KEY - Anthropic API key

    [bold]Upgrade:[/bold]
        https://xsourcesec.com/pricing
    """
    if version_flag:
        version()
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        print_banner()
        console.print(ctx.get_help())


# =========================================================================
# Entry point
# =========================================================================

def main_entry():
    """Main entry point for the CLI."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted[/dim]")
        raise typer.Exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    main_entry()

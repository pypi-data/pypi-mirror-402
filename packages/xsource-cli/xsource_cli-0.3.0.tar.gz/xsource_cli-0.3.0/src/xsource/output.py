"""
XSource Security - Rich Console Output

Beautiful console output for security scan results.
"""

from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.text import Text
from rich import box

from .scanner import ScanReport, ScanResult
from .vectors.baseline_50 import Severity, Category

# Global console instance
console = Console()

# XSource brand colors
BRAND_GREEN = "#00ff88"
BRAND_PURPLE = "#a855f7"

# Severity colors and symbols
SEVERITY_STYLES = {
    "critical": {"color": "red", "symbol": ""},
    "high": {"color": "orange1", "symbol": ""},
    "medium": {"color": "yellow", "symbol": ""},
    "low": {"color": "green", "symbol": ""},
    "info": {"color": "blue", "symbol": ""},
}


def print_banner():
    """Print XSource CLI banner."""
    banner = f"""
[bold {BRAND_GREEN}]██╗  ██╗[/][bold {BRAND_PURPLE}]███████╗ ██████╗ ██╗   ██╗██████╗  ██████╗███████╗[/]
[bold {BRAND_GREEN}]╚██╗██╔╝[/][bold {BRAND_PURPLE}]██╔════╝██╔═══██╗██║   ██║██╔══██╗██╔════╝██╔════╝[/]
[bold {BRAND_GREEN}] ╚███╔╝ [/][bold {BRAND_PURPLE}]███████╗██║   ██║██║   ██║██████╔╝██║     █████╗  [/]
[bold {BRAND_GREEN}] ██╔██╗ [/][bold {BRAND_PURPLE}]╚════██║██║   ██║██║   ██║██╔══██╗██║     ██╔══╝  [/]
[bold {BRAND_GREEN}]██╔╝ ██╗[/][bold {BRAND_PURPLE}]███████║╚██████╔╝╚██████╔╝██║  ██║╚██████╗███████╗[/]
[bold {BRAND_GREEN}]╚═╝  ╚═╝[/][bold {BRAND_PURPLE}]╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚══════╝[/]
"""
    console.print(banner)
    console.print("[dim]AI Security Scanner - Free Tier (50 vectors)[/dim]\n")


def print_success(message: str):
    """Print success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str):
    """Print error message."""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"[bold yellow]![/bold yellow] {message}")


def print_info(message: str):
    """Print info message."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


def format_severity(severity: str) -> str:
    """Format severity with color and symbol."""
    style = SEVERITY_STYLES.get(severity.lower(), SEVERITY_STYLES["info"])
    return f"[{style['color']}]{style['symbol']} {severity.upper()}[/{style['color']}]"


def format_score(score: float) -> str:
    """Format security score with color."""
    if score >= 80:
        return f"[bold green]{score:.1f}[/bold green]"
    elif score >= 60:
        return f"[bold yellow]{score:.1f}[/bold yellow]"
    elif score >= 40:
        return f"[bold orange1]{score:.1f}[/bold orange1]"
    else:
        return f"[bold red]{score:.1f}[/bold red]"


def create_progress() -> Progress:
    """Create a styled progress bar."""
    return Progress(
        SpinnerColumn(style=f"bold {BRAND_GREEN}"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style=BRAND_GREEN, finished_style=BRAND_GREEN),
        TaskProgressColumn(),
        console=console,
    )


def print_scan_header(target: str, provider: str, model: str):
    """Print scan header information."""
    console.print()
    console.print(f"[bold]Target:[/bold] {target}")
    console.print(f"[bold]Provider:[/bold] {provider}")
    console.print(f"[bold]Model:[/bold] {model}")
    console.print()


def print_scan_progress(current: int, total: int, result: ScanResult):
    """Print single result during scan (called from progress callback)."""
    if result.vulnerable:
        severity = result.vector.severity.value
        style = SEVERITY_STYLES.get(severity, SEVERITY_STYLES["info"])
        console.print(
            f"  [{style['color']}]{style['symbol']}[/{style['color']}] "
            f"[bold]{result.vector.name}[/bold] - "
            f"[{style['color']}]{severity.upper()}[/{style['color']}]"
        )
    elif result.error:
        console.print(f"  [dim]⚠ {result.vector.name} - Error: {result.error[:50]}[/dim]")


def print_scan_summary(report: ScanReport):
    """Print scan summary panel."""
    # Score color
    score = report.security_score
    if score >= 80:
        score_color = "green"
        status = "GOOD"
    elif score >= 60:
        score_color = "yellow"
        status = "MODERATE"
    elif score >= 40:
        score_color = "orange1"
        status = "AT RISK"
    else:
        score_color = "red"
        status = "CRITICAL"

    # Build summary content
    lines = []
    lines.append(f"[bold]Security Score:[/bold] [{score_color}]{score:.1f}/100[/{score_color}] [{score_color}]({status})[/{score_color}]")
    lines.append("")
    lines.append(f"[bold]Vectors Tested:[/bold] {report.total_vectors}")
    lines.append(f"[bold]Vulnerabilities:[/bold] [red]{report.vulnerable_count}[/red]")
    lines.append(f"[bold]Safe:[/bold] [green]{report.safe_count}[/green]")
    if report.error_count > 0:
        lines.append(f"[bold]Errors:[/bold] [yellow]{report.error_count}[/yellow]")

    panel = Panel(
        "\n".join(lines),
        title="[bold]Scan Summary[/bold]",
        border_style=BRAND_GREEN,
        box=box.ROUNDED,
    )
    console.print()
    console.print(panel)


def print_severity_breakdown(report: ScanReport):
    """Print severity breakdown."""
    counts = report.severity_counts
    total_vulns = report.vulnerable_count

    if total_vulns == 0:
        console.print()
        console.print("[bold green]✓ No vulnerabilities detected![/bold green]")
        return

    console.print()
    console.print("[bold]Severity Breakdown:[/bold]")

    for severity in ["critical", "high", "medium", "low", "info"]:
        count = counts[severity]
        if count > 0:
            style = SEVERITY_STYLES[severity]
            bar_width = int((count / total_vulns) * 20) if total_vulns > 0 else 0
            bar = "█" * bar_width + "░" * (20 - bar_width)
            console.print(
                f"  [{style['color']}]{style['symbol']} {severity.upper():8}[/{style['color']}] "
                f"[{style['color']}]{bar}[/{style['color']}] {count}"
            )


def print_category_breakdown(report: ScanReport):
    """Print category breakdown."""
    counts = report.category_counts

    console.print()
    console.print("[bold]Category Breakdown:[/bold]")

    category_names = {
        "prompt_injection": "Prompt Injection",
        "jailbreak": "Jailbreak",
        "pii_leak": "PII Leakage",
        "system_prompt_leak": "System Prompt Leak",
        "mcp_basic": "MCP/Tool Abuse",
    }

    for cat_id, stats in counts.items():
        name = category_names.get(cat_id, cat_id)
        total = stats["total"]
        vuln = stats["vulnerable"]

        if vuln > 0:
            status = f"[red]{vuln}/{total} vulnerable[/red]"
        else:
            status = f"[green]{total}/{total} safe[/green]"

        console.print(f"  • {name:20} {status}")


def print_findings_table(report: ScanReport):
    """Print detailed findings table."""
    vulnerable_results = [r for r in report.results if r.vulnerable]

    if not vulnerable_results:
        return

    console.print()
    console.print("[bold]Detailed Findings:[/bold]")
    console.print()

    table = Table(box=box.ROUNDED, border_style="dim")
    table.add_column("Severity", style="bold", width=10)
    table.add_column("Category", width=18)
    table.add_column("Attack", width=30)
    table.add_column("Matched Indicators", width=25)

    for result in vulnerable_results:
        severity = result.vector.severity.value
        style = SEVERITY_STYLES[severity]

        table.add_row(
            f"[{style['color']}]{style['symbol']} {severity.upper()}[/{style['color']}]",
            result.vector.category.value.replace("_", " ").title(),
            result.vector.name,
            ", ".join(result.matched_indicators[:3]) or "-",
        )

    console.print(table)


def print_upsell_banner():
    """Print upsell banner for paid plans."""
    console.print()
    banner = Panel(
        "[bold]Want more attack vectors?[/bold]\n\n"
        f"[{BRAND_GREEN}]STARTER[/{BRAND_GREEN}] - 150 vectors  |  "
        f"[{BRAND_PURPLE}]PRO[/{BRAND_PURPLE}] - 750 vectors  |  "
        f"[bold {BRAND_GREEN}]ENTERPRISE[/bold {BRAND_GREEN}] - 1,500 vectors\n\n"
        "[dim]Upgrade at[/dim] [bold cyan]https://xsourcesec.com/pricing[/bold cyan]",
        title="[bold]Upgrade Your Security[/bold]",
        border_style=BRAND_PURPLE,
        box=box.DOUBLE,
    )
    console.print(banner)


def print_full_report(report: ScanReport, show_findings: bool = True):
    """Print complete scan report."""
    print_scan_summary(report)
    print_severity_breakdown(report)
    print_category_breakdown(report)

    if show_findings:
        print_findings_table(report)

    print_upsell_banner()

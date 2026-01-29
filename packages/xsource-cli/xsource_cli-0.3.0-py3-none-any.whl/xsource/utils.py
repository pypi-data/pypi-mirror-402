"""
Utility functions and Rich output helpers for XSource CLI.
"""

import sys
from typing import Optional, Any, Dict, List
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.syntax import Syntax
from rich.text import Text
from rich.style import Style
from rich import box

# Global console instance
console = Console()

# XSource brand colors
BRAND_GREEN = "#00ff88"
BRAND_PURPLE = "#a855f7"
BRAND_DARK = "#0d1117"


def print_banner():
    """Print XSource CLI banner."""
    banner = """
[bold #00ff88]██╗  ██╗[/][bold #a855f7]███████╗ ██████╗ ██╗   ██╗██████╗  ██████╗███████╗[/]
[bold #00ff88]╚██╗██╔╝[/][bold #a855f7]██╔════╝██╔═══██╗██║   ██║██╔══██╗██╔════╝██╔════╝[/]
[bold #00ff88] ╚███╔╝ [/][bold #a855f7]███████╗██║   ██║██║   ██║██████╔╝██║     █████╗  [/]
[bold #00ff88] ██╔██╗ [/][bold #a855f7]╚════██║██║   ██║██║   ██║██╔══██╗██║     ██╔══╝  [/]
[bold #00ff88]██╔╝ ██╗[/][bold #a855f7]███████║╚██████╔╝╚██████╔╝██║  ██║╚██████╗███████╗[/]
[bold #00ff88]╚═╝  ╚═╝[/][bold #a855f7]╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚══════╝[/]
    """
    console.print(banner)
    console.print("[dim]AI Agent Security Scanner & Benchmark Tool[/dim]\n")


def print_success(message: str):
    """Print success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str, detail: Optional[str] = None):
    """Print error message."""
    console.print(f"[bold red]✗[/bold red] {message}")
    if detail:
        console.print(f"  [dim]{detail}[/dim]")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"[bold yellow]![/bold yellow] {message}")


def print_info(message: str):
    """Print info message."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


def print_json(data: Any):
    """Print formatted JSON."""
    import json
    syntax = Syntax(json.dumps(data, indent=2, default=str), "json", theme="monokai")
    console.print(syntax)


def create_progress() -> Progress:
    """Create a styled progress bar."""
    return Progress(
        SpinnerColumn(style=f"bold {BRAND_GREEN}"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style=BRAND_GREEN, finished_style=BRAND_GREEN),
        TaskProgressColumn(),
        console=console,
    )


def create_spinner() -> Progress:
    """Create a simple spinner."""
    return Progress(
        SpinnerColumn(style=f"bold {BRAND_GREEN}"),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )


def format_datetime(dt: Optional[str]) -> str:
    """Format datetime string for display."""
    if not dt:
        return "-"
    try:
        parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return dt


def format_score(score: Optional[float], threshold: float = 70.0) -> str:
    """Format security score with color."""
    if score is None:
        return "[dim]-[/dim]"
    if score >= threshold:
        return f"[bold green]{score:.1f}[/bold green]"
    elif score >= 50:
        return f"[bold yellow]{score:.1f}[/bold yellow]"
    else:
        return f"[bold red]{score:.1f}[/bold red]"


def format_status(status: str) -> str:
    """Format status with color."""
    status_colors = {
        "completed": "[bold green]completed[/bold green]",
        "running": "[bold yellow]running[/bold yellow]",
        "pending": "[bold blue]pending[/bold blue]",
        "failed": "[bold red]failed[/bold red]",
        "passed": "[bold green]passed[/bold green]",
    }
    return status_colors.get(status.lower(), f"[dim]{status}[/dim]")


def format_severity(severity: str) -> str:
    """Format severity with color."""
    severity_colors = {
        "critical": "[bold red]CRITICAL[/bold red]",
        "high": "[red]HIGH[/red]",
        "medium": "[yellow]MEDIUM[/yellow]",
        "low": "[blue]LOW[/blue]",
        "info": "[dim]INFO[/dim]",
    }
    return severity_colors.get(severity.lower(), severity)


def format_plan(plan: str) -> str:
    """Format plan badge."""
    plan_styles = {
        "free": "[dim]Free[/dim]",
        "starter": "[blue]Starter[/blue]",
        "pro": f"[{BRAND_PURPLE}]Pro[/{BRAND_PURPLE}]",
        "enterprise": f"[{BRAND_GREEN}]Enterprise[/{BRAND_GREEN}]",
    }
    return plan_styles.get(plan.lower(), plan)


# =========================================================================
# Table Helpers
# =========================================================================

def create_table(title: Optional[str] = None, **kwargs) -> Table:
    """Create a styled table."""
    return Table(
        title=title,
        box=box.ROUNDED,
        border_style="dim",
        header_style=f"bold {BRAND_GREEN}",
        **kwargs,
    )


def print_scans_table(scans: List[Dict[str, Any]]):
    """Print scans in a formatted table."""
    table = create_table("Security Scans")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Target", style="white")
    table.add_column("Status")
    table.add_column("Score", justify="right")
    table.add_column("Vulns", justify="right")
    table.add_column("Date", style="dim")

    for scan in scans:
        table.add_row(
            str(scan.get("id", "-")),
            scan.get("target", "-")[:50],
            format_status(scan.get("status", "unknown")),
            format_score(scan.get("severity_score")),
            str(scan.get("vulnerabilities_found", 0)),
            format_datetime(scan.get("created_at")),
        )

    console.print(table)


def print_scenarios_table(scenarios: List[Dict[str, Any]]):
    """Print benchmark scenarios in a formatted table."""
    table = create_table("Available Scenarios")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Category", style="blue")
    table.add_column("Difficulty")
    table.add_column("Points", justify="right", style="yellow")

    difficulty_colors = {
        "easy": "[green]Easy[/green]",
        "medium": "[yellow]Medium[/yellow]",
        "hard": "[red]Hard[/red]",
    }

    for scenario in scenarios:
        diff = scenario.get("difficulty", "medium").lower()
        table.add_row(
            scenario.get("id", "-"),
            scenario.get("name", "-"),
            scenario.get("category", "-"),
            difficulty_colors.get(diff, diff),
            str(scenario.get("points", 100)),
        )

    console.print(table)


def print_benchmark_runs_table(runs: List[Dict[str, Any]]):
    """Print benchmark runs in a formatted table."""
    table = create_table("Benchmark Runs")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Scenario", style="white")
    table.add_column("Agent", style="blue")
    table.add_column("Status")
    table.add_column("Score", justify="right")
    table.add_column("Tests", justify="right")
    table.add_column("Date", style="dim")

    for run in runs:
        tests = f"{run.get('tests_passed', 0)}/{run.get('tests_total', 0)}"
        table.add_row(
            str(run.get("id", "-")),
            run.get("scenario_id", "-"),
            run.get("agent_name", "-")[:20],
            format_status(run.get("status", "unknown")),
            format_score(run.get("score")),
            tests,
            format_datetime(run.get("created_at")),
        )

    console.print(table)


# =========================================================================
# Panel Helpers
# =========================================================================

def print_scan_details(scan: Dict[str, Any]):
    """Print detailed scan information."""
    content = []
    content.append(f"[bold]Target:[/bold] {scan.get('target', '-')}")
    content.append(f"[bold]Status:[/bold] {format_status(scan.get('status', 'unknown'))}")
    content.append(f"[bold]Security Score:[/bold] {format_score(scan.get('severity_score'))}/100")
    content.append(f"[bold]Vulnerabilities:[/bold] {scan.get('vulnerabilities_found', 0)}")
    content.append(f"[bold]Created:[/bold] {format_datetime(scan.get('created_at'))}")

    if scan.get("completed_at"):
        content.append(f"[bold]Completed:[/bold] {format_datetime(scan.get('completed_at'))}")

    panel = Panel(
        "\n".join(content),
        title=f"[bold]Scan #{scan.get('id', '-')}[/bold]",
        border_style=BRAND_GREEN,
        box=box.ROUNDED,
    )
    console.print(panel)


def print_user_info(user: Dict[str, Any], org: Optional[Dict[str, Any]] = None):
    """Print user information panel."""
    content = []
    content.append(f"[bold]Email:[/bold] {user.get('email', '-')}")
    content.append(f"[bold]Name:[/bold] {user.get('name', '-')}")
    content.append(f"[bold]Role:[/bold] {user.get('role', '-')}")
    content.append(f"[bold]Verified:[/bold] {'✓' if user.get('is_verified') else '✗'}")

    if org:
        content.append("")
        content.append(f"[bold]Organization:[/bold] {org.get('name', '-')}")
        content.append(f"[bold]Plan:[/bold] {format_plan(org.get('plan', 'free'))}")

    panel = Panel(
        "\n".join(content),
        title="[bold]Account Info[/bold]",
        border_style=BRAND_PURPLE,
        box=box.ROUNDED,
    )
    console.print(panel)


def print_findings(findings: List[Dict[str, Any]]):
    """Print security findings."""
    if not findings:
        print_info("No findings to display")
        return

    for i, finding in enumerate(findings, 1):
        severity = finding.get("severity", "info")
        title = finding.get("title", "Finding")

        content = []
        if finding.get("description"):
            content.append(finding["description"])
        if finding.get("recommendation"):
            content.append(f"\n[bold]Recommendation:[/bold] {finding['recommendation']}")
        if finding.get("cwe_id"):
            content.append(f"[dim]CWE: {finding['cwe_id']}[/dim]")

        panel = Panel(
            "\n".join(content) if content else "[dim]No details[/dim]",
            title=f"{format_severity(severity)} {title}",
            border_style="red" if severity in ["critical", "high"] else "yellow",
            box=box.ROUNDED,
        )
        console.print(panel)


# =========================================================================
# Loading/Progress Context Managers
# =========================================================================

class Spinner:
    """Context manager for spinner during operations."""

    def __init__(self, message: str = "Loading..."):
        self.message = message
        self.progress = None
        self.task = None

    def __enter__(self):
        self.progress = create_spinner()
        self.progress.start()
        self.task = self.progress.add_task(self.message)
        return self

    def __exit__(self, *args):
        if self.progress:
            self.progress.stop()

    def update(self, message: str):
        if self.progress and self.task is not None:
            self.progress.update(self.task, description=message)


def handle_api_error(func):
    """Decorator to handle API errors gracefully."""
    from functools import wraps
    from .api import APIError

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            print_error(e.message, e.detail)
            raise SystemExit(1)
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            raise SystemExit(1)

    return wrapper

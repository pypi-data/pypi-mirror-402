"""
AgentAudit (Security Scanning) commands for XSource CLI.
"""

import typer
import time
import yaml
from pathlib import Path
from typing import Optional
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich import box

from .config import ensure_authenticated, get_config
from .api import XSourceAPI, APIError

# Demo server URL for unauthenticated scans
DEMO_SERVER_URL = "vulnerable-mcp-demo.fly.dev"
from .utils import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_scans_table,
    print_scan_details,
    print_findings,
    format_status,
    format_score,
    format_datetime,
    Spinner,
    create_progress,
    BRAND_GREEN,
    BRAND_PURPLE,
)

app = typer.Typer(help="AgentAudit security scanning commands")


def is_demo_target(target: str) -> bool:
    """Check if target is the demo server."""
    return DEMO_SERVER_URL in target


def wait_for_scan(api: XSourceAPI, scan_id: int, timeout: int = 300, is_demo: bool = False) -> dict:
    """Wait for scan to complete with live progress."""
    start_time = time.time()
    phases = ["Connecting to MCP server", "Discovering tools & resources", "Running security checks", "Analyzing vulnerabilities", "Complete"]
    current_phase = 0

    with create_progress() as progress:
        task = progress.add_task(f"[{BRAND_GREEN}]Scanning...", total=100)

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Scan timed out after {timeout} seconds")

            try:
                if is_demo:
                    scan = api.get_demo_scan(scan_id)
                else:
                    scan = api.get_scan(scan_id)
                status = scan.get("status", "pending")

                # Update progress based on status
                if status == "completed":
                    progress.update(task, completed=100, description=f"[{BRAND_GREEN}]Complete!")
                    return scan
                elif status == "failed":
                    raise APIError(500, "Scan failed", scan.get("error"))
                elif status == "running":
                    # Simulate progress
                    fake_progress = min(90, (elapsed / timeout) * 100)
                    current_phase = min(len(phases) - 2, int(fake_progress / 25))
                    progress.update(
                        task,
                        completed=fake_progress,
                        description=f"[{BRAND_GREEN}]{phases[current_phase]}..."
                    )

            except APIError:
                raise

            time.sleep(2)


@app.command("run")
def scan_run(
    target: str = typer.Argument(..., help="Target URL to scan"),
    mode: str = typer.Option("quick", "--mode", "-m", help="Scan mode: quick, standard, full"),
    demo: bool = typer.Option(False, "--demo", "-d", help="Demo mode - scan demo server without auth"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Custom scan config YAML file"),
    wait: bool = typer.Option(True, "--wait/--no-wait", "-w", help="Wait for scan to complete"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format: json, table"),
):
    """
    Run a security scan on a target URL.

    Examples:
        xsource scan https://vulnerable-mcp-demo.fly.dev/mcp --demo
        xsource scan run https://api.example.com/chat
        xsource scan run https://api.example.com --mode full
    """
    # Check if this is a demo scan (--demo flag OR demo URL)
    is_demo = demo or is_demo_target(target)

    if is_demo:
        # Demo mode - no authentication required
        console.print()
        console.print(f"[bold {BRAND_PURPLE}]Demo Mode[/bold {BRAND_PURPLE}] - Scanning vulnerable demo server")
        console.print(f"[bold]Target:[/bold] {target}")
        console.print()

        with Spinner("Starting demo scan...") as spinner:
            try:
                api = XSourceAPI()
                result = api.create_demo_scan(target)
                scan_id = int(result.get("id"))
                spinner.update(f"Scan #{scan_id} created")
            except APIError as e:
                print_error(f"Failed to start scan: {e.message}")
                raise typer.Exit(1)

        console.print()
        print_success(f"Demo scan started with ID: [cyan]{scan_id}[/cyan]")

        if wait:
            console.print()
            try:
                scan = wait_for_scan(api, scan_id, is_demo=True)
            except TimeoutError as e:
                print_warning(str(e))
                raise typer.Exit(1)
            except APIError as e:
                print_error(f"Scan failed: {e.message}")
                raise typer.Exit(1)

            console.print()
            print_scan_details(scan)

            # Show demo-specific summary
            vulns = scan.get("vulnerabilities_found", 0)
            results = scan.get("results", {})
            vulnerabilities = results.get("vulnerabilities", [])

            # Count by severity
            counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for v in vulnerabilities:
                sev = (v.get("severity") or "medium").lower()
                if sev in counts:
                    counts[sev] += 1

            console.print()
            console.print(f"[bold red]{vulns} vulnerabilities found[/bold red] ", end="")
            console.print(f"([red]{counts['critical']} CRITICAL[/red], [yellow]{counts['high']} HIGH[/yellow], [blue]{counts['medium']} MEDIUM[/blue], [green]{counts['low']} LOW[/green])")
            console.print()
            print_info("Sign up at [cyan]https://app.xsourcesec.com[/cyan] to scan your own servers!")

        return

    # Non-demo mode - require authentication
    creds = ensure_authenticated()

    # Validate mode
    valid_modes = ["quick", "standard", "full"]
    if mode not in valid_modes:
        print_error(f"Invalid mode: {mode}. Must be one of: {', '.join(valid_modes)}")
        raise typer.Exit(1)

    # Load custom config if provided
    custom_config = None
    if config_file:
        if not config_file.exists():
            print_error(f"Config file not found: {config_file}")
            raise typer.Exit(1)
        try:
            with open(config_file) as f:
                custom_config = yaml.safe_load(f)
        except Exception as e:
            print_error(f"Failed to parse config file: {e}")
            raise typer.Exit(1)

    console.print()
    console.print(f"[bold]Target:[/bold] {target}")
    console.print(f"[bold]Mode:[/bold] {mode}")
    if custom_config:
        console.print(f"[bold]Config:[/bold] {config_file}")
    console.print()

    with Spinner("Starting scan...") as spinner:
        try:
            api = XSourceAPI(credentials=creds)
            result = api.create_scan(target, scan_type=mode, config=custom_config)
            scan_id = result.get("id")
            spinner.update(f"Scan #{scan_id} created")
        except APIError as e:
            print_error(f"Failed to start scan: {e.message}")
            raise typer.Exit(1)

    console.print()
    print_success(f"Scan started with ID: [cyan]{scan_id}[/cyan]")

    if not wait:
        print_info(f"Check status with: [cyan]xsource scan status {scan_id}[/cyan]")
        return

    console.print()

    try:
        scan = wait_for_scan(api, scan_id)
    except TimeoutError as e:
        print_warning(str(e))
        print_info(f"Check status with: [cyan]xsource scan status {scan_id}[/cyan]")
        raise typer.Exit(1)
    except APIError as e:
        print_error(f"Scan failed: {e.message}")
        raise typer.Exit(1)

    console.print()
    print_scan_details(scan)

    # Show summary
    score = scan.get("severity_score")
    vulns = scan.get("vulnerabilities_found", 0)

    console.print()
    if score is not None and score >= 70:
        print_success(f"Security Score: {score}/100 - Looking good!")
    elif score is not None and score >= 50:
        print_warning(f"Security Score: {score}/100 - Some issues found")
    elif score is not None:
        print_error(f"Security Score: {score}/100 - Needs attention!")

    if vulns > 0:
        print_info(f"View details: [cyan]xsource report {scan_id}[/cyan]")


@app.command("status")
def scan_status(
    scan_id: int = typer.Argument(..., help="Scan ID to check"),
):
    """
    Check the status of a scan.
    """
    creds = ensure_authenticated()

    with Spinner("Fetching scan status..."):
        try:
            api = XSourceAPI(credentials=creds)
            scan = api.get_scan(scan_id)
        except APIError as e:
            print_error(f"Failed to get scan: {e.message}")
            raise typer.Exit(1)

    console.print()
    print_scan_details(scan)


@app.command("list")
def scan_list(
    limit: int = typer.Option(20, "--limit", "-l", help="Number of scans to show"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json"),
):
    """
    List all scans.
    """
    creds = ensure_authenticated()

    with Spinner("Fetching scans..."):
        try:
            api = XSourceAPI(credentials=creds)
            scans = api.list_scans(limit=limit)
        except APIError as e:
            print_error(f"Failed to list scans: {e.message}")
            raise typer.Exit(1)

    console.print()

    if not scans:
        print_info("No scans found")
        print_info("Start a scan with: [cyan]xsource scan run <target>[/cyan]")
        return

    if output == "json":
        from .utils import print_json
        print_json(scans)
    else:
        print_scans_table(scans)


@app.callback(invoke_without_command=True)
def scan_default(
    ctx: typer.Context,
    target: Optional[str] = typer.Argument(None, help="Target URL to scan (shorthand for 'xsource scan run')"),
    demo: bool = typer.Option(False, "--demo", "-d", help="Demo mode - scan demo server without auth"),
):
    """
    Run a quick scan (shorthand) or show scan commands.

    Examples:
        xsource scan https://vulnerable-mcp-demo.fly.dev/mcp --demo  # Demo scan
        xsource scan https://api.example.com   # Quick scan
        xsource scan list                       # List scans
        xsource scan status 123                 # Check scan status
    """
    if ctx.invoked_subcommand is None and target:
        # Shorthand: xsource scan <url> -> xsource scan run <url> with defaults
        scan_run(target=target, mode="quick", demo=demo, config_file=None, wait=True, output=None)
    elif ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


# Report command (could be separate but logically related to scans)
report_app = typer.Typer(help="View and export scan reports")


@report_app.command("view")
def report_view(
    scan_id: int = typer.Argument(..., help="Scan ID"),
    show_findings: bool = typer.Option(True, "--findings/--no-findings", help="Show detailed findings"),
):
    """
    View scan report details.
    """
    creds = ensure_authenticated()

    with Spinner("Fetching report..."):
        try:
            api = XSourceAPI(credentials=creds)
            scan = api.get_scan(scan_id)
            results = api.get_scan_results(scan_id) if show_findings else None
        except APIError as e:
            print_error(f"Failed to get report: {e.message}")
            raise typer.Exit(1)

    console.print()
    print_scan_details(scan)

    if results and show_findings:
        findings = results.get("findings", [])
        if findings:
            console.print()
            console.print("[bold]Findings:[/bold]")
            print_findings(findings)


@report_app.command("export")
def report_export(
    scan_id: int = typer.Argument(..., help="Scan ID"),
    format: str = typer.Option("pdf", "--format", "-f", help="Export format: pdf, html, json"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """
    Export scan report to file.

    Examples:
        xsource report export 123 --format pdf --output report.pdf
        xsource report export 123 -f json -o results.json
    """
    creds = ensure_authenticated()

    valid_formats = ["pdf", "html", "json"]
    if format not in valid_formats:
        print_error(f"Invalid format: {format}. Must be one of: {', '.join(valid_formats)}")
        raise typer.Exit(1)

    # Default output filename
    if output is None:
        output = Path(f"scan_{scan_id}_report.{format}")

    with Spinner(f"Generating {format.upper()} report..."):
        try:
            api = XSourceAPI(credentials=creds)

            if format == "json":
                import json
                results = api.get_scan_results(scan_id)
                with open(output, "w") as f:
                    json.dump(results, f, indent=2)
            else:
                content = api.export_report(scan_id, format=format)
                with open(output, "wb") as f:
                    f.write(content)

        except APIError as e:
            print_error(f"Failed to export report: {e.message}")
            raise typer.Exit(1)

    console.print()
    print_success(f"Report saved to: [cyan]{output}[/cyan]")


@report_app.callback(invoke_without_command=True)
def report_default(
    ctx: typer.Context,
    scan_id: Optional[int] = typer.Argument(None, help="Scan ID to view"),
):
    """
    View or export scan reports.

    Examples:
        xsource report 123            # View report
        xsource report export 123     # Export report
    """
    if ctx.invoked_subcommand is None and scan_id:
        report_view(scan_id=scan_id)
    elif ctx.invoked_subcommand is None:
        console.print(ctx.get_help())

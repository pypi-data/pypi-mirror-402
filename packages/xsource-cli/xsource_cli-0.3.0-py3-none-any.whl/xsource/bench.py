"""
AgentBench (Benchmarking) commands for XSource CLI.
"""

import typer
import time
from typing import Optional, List
from rich.prompt import Prompt
from rich.panel import Panel
from rich import box

from .config import ensure_authenticated
from .api import XSourceAPI, APIError
from .utils import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_scenarios_table,
    print_benchmark_runs_table,
    format_status,
    format_score,
    format_datetime,
    Spinner,
    create_progress,
    create_table,
    BRAND_GREEN,
    BRAND_PURPLE,
)

app = typer.Typer(help="AgentBench benchmarking commands")


def wait_for_benchmark(api: XSourceAPI, run_id: int, timeout: int = 180) -> dict:
    """Wait for benchmark to complete with live progress."""
    start_time = time.time()

    with create_progress() as progress:
        task = progress.add_task(f"[{BRAND_PURPLE}]Running benchmark...", total=100)

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Benchmark timed out after {timeout} seconds")

            try:
                run = api.get_benchmark_run(run_id)
                status = run.get("status", "pending")

                if status == "completed":
                    progress.update(task, completed=100, description=f"[{BRAND_GREEN}]Complete!")
                    return run
                elif status == "failed":
                    raise APIError(500, "Benchmark failed", run.get("error"))
                elif status == "running":
                    fake_progress = min(90, (elapsed / timeout) * 100)
                    progress.update(task, completed=fake_progress)

            except APIError:
                raise

            time.sleep(1)


@app.command("list")
def bench_list(
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json"),
):
    """
    List available benchmark scenarios.
    """
    creds = ensure_authenticated()

    with Spinner("Fetching scenarios..."):
        try:
            api = XSourceAPI(credentials=creds)
            scenarios = api.list_scenarios()
        except APIError as e:
            print_error(f"Failed to list scenarios: {e.message}")
            raise typer.Exit(1)

    console.print()

    if not scenarios:
        print_info("No scenarios available")
        return

    if output == "json":
        from .utils import print_json
        print_json(scenarios)
    else:
        print_scenarios_table(scenarios)

    # Show usage info
    try:
        api = XSourceAPI(credentials=creds)
        usage = api.get_benchmark_usage()
        console.print()
        if usage.get("is_unlimited"):
            console.print(f"[dim]Runs: Unlimited[/dim]")
        else:
            remaining = usage.get("runs_remaining", 0)
            limit = usage.get("runs_limit", 0)
            console.print(f"[dim]Runs remaining: {remaining}/{limit}[/dim]")
    except Exception:
        pass


@app.command("run")
def bench_run(
    scenario_id: str = typer.Argument(..., help="Scenario ID to run"),
    agent_name: str = typer.Option(None, "--name", "-n", help="Agent name for identification"),
    endpoint: str = typer.Option(None, "--endpoint", "-e", help="AI API endpoint URL"),
    api_key: str = typer.Option(None, "--key", "-k", help="AI API key"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model name (optional)"),
    wait: bool = typer.Option(True, "--wait/--no-wait", "-w", help="Wait for completion"),
):
    """
    Run a benchmark scenario against an AI agent.

    Examples:
        xsource bench run prompt-injection-basic -n "My Agent" -e https://api.openai.com/v1/chat/completions -k sk-xxx
        xsource bench run jailbreak-advanced --endpoint https://api.anthropic.com/v1/messages --key sk-xxx --model claude-3-opus
    """
    creds = ensure_authenticated()

    # Interactive prompts if not provided
    if not agent_name:
        agent_name = Prompt.ask("[bold cyan]Agent name[/bold cyan]", default="My Agent")

    if not endpoint:
        endpoint = Prompt.ask(
            "[bold cyan]API endpoint[/bold cyan]",
            default="https://api.openai.com/v1/chat/completions"
        )

    if not api_key:
        api_key = Prompt.ask("[bold cyan]API key[/bold cyan]", password=True)

    if not api_key:
        print_error("API key is required")
        raise typer.Exit(1)

    console.print()
    console.print(f"[bold]Scenario:[/bold] {scenario_id}")
    console.print(f"[bold]Agent:[/bold] {agent_name}")
    console.print(f"[bold]Endpoint:[/bold] {endpoint}")
    if model:
        console.print(f"[bold]Model:[/bold] {model}")
    console.print()

    with Spinner("Starting benchmark...") as spinner:
        try:
            api = XSourceAPI(credentials=creds)
            result = api.run_benchmark(
                scenario_id=scenario_id,
                agent_name=agent_name,
                api_endpoint=endpoint,
                api_key=api_key,
                model_name=model,
            )
            run_id = result.get("id")
            spinner.update(f"Benchmark #{run_id} started")
        except APIError as e:
            if "limit" in e.message.lower():
                print_error("Monthly benchmark limit reached")
                print_info("Upgrade your plan at: [cyan]https://app.xsourcesec.com/billing[/cyan]")
            else:
                print_error(f"Failed to start benchmark: {e.message}")
            raise typer.Exit(1)

    console.print()
    print_success(f"Benchmark started with ID: [cyan]{run_id}[/cyan]")

    if not wait:
        print_info(f"Check results with: [cyan]xsource bench results {run_id}[/cyan]")
        return

    console.print()

    try:
        run = wait_for_benchmark(api, run_id)
    except TimeoutError as e:
        print_warning(str(e))
        print_info(f"Check results with: [cyan]xsource bench results {run_id}[/cyan]")
        raise typer.Exit(1)
    except APIError as e:
        print_error(f"Benchmark failed: {e.message}")
        raise typer.Exit(1)

    console.print()
    print_benchmark_result(run)


@app.command("results")
def bench_results(
    run_id: int = typer.Argument(..., help="Benchmark run ID"),
):
    """
    View benchmark run results.
    """
    creds = ensure_authenticated()

    with Spinner("Fetching results..."):
        try:
            api = XSourceAPI(credentials=creds)
            run = api.get_benchmark_run(run_id)
        except APIError as e:
            print_error(f"Failed to get results: {e.message}")
            raise typer.Exit(1)

    console.print()
    print_benchmark_result(run)


@app.command("history")
def bench_history(
    limit: int = typer.Option(20, "--limit", "-l", help="Number of runs to show"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json"),
):
    """
    View benchmark run history.
    """
    creds = ensure_authenticated()

    with Spinner("Fetching history..."):
        try:
            api = XSourceAPI(credentials=creds)
            runs = api.list_benchmark_runs(limit=limit)
        except APIError as e:
            print_error(f"Failed to get history: {e.message}")
            raise typer.Exit(1)

    console.print()

    if not runs:
        print_info("No benchmark runs found")
        print_info("Start a benchmark with: [cyan]xsource bench run <scenario>[/cyan]")
        return

    if output == "json":
        from .utils import print_json
        print_json(runs)
    else:
        print_benchmark_runs_table(runs)


@app.command("stats")
def bench_stats():
    """
    View benchmark statistics.
    """
    creds = ensure_authenticated()

    with Spinner("Fetching stats..."):
        try:
            api = XSourceAPI(credentials=creds)
            stats = api.get_benchmark_stats()
            usage = api.get_benchmark_usage()
        except APIError as e:
            print_error(f"Failed to get stats: {e.message}")
            raise typer.Exit(1)

    console.print()

    # Stats panel
    content = []
    content.append(f"[bold]Total Runs:[/bold] {stats.get('total_runs', 0)}")
    content.append(f"[bold]Average Score:[/bold] {format_score(stats.get('average_score'))}")
    content.append(f"[bold]Pass Rate:[/bold] {stats.get('pass_rate', 0):.1f}%")
    content.append(f"[bold]Scenarios Tested:[/bold] {stats.get('total_scenarios', 0)}")

    panel = Panel(
        "\n".join(content),
        title="[bold]Benchmark Statistics[/bold]",
        border_style=BRAND_PURPLE,
        box=box.ROUNDED,
    )
    console.print(panel)

    # Usage panel
    console.print()
    usage_content = []
    if usage.get("is_unlimited"):
        usage_content.append("[bold green]Unlimited runs[/bold green]")
    else:
        usage_content.append(f"[bold]Runs Used:[/bold] {usage.get('runs_used', 0)}/{usage.get('runs_limit', 0)}")
        usage_content.append(f"[bold]Remaining:[/bold] {usage.get('runs_remaining', 0)}")
        usage_content.append(f"[bold]Resets:[/bold] {usage.get('reset_date', 'N/A')}")

    usage_content.append(f"[bold]Plan:[/bold] {usage.get('plan', 'free').capitalize()}")

    usage_panel = Panel(
        "\n".join(usage_content),
        title="[bold]Usage[/bold]",
        border_style="dim",
        box=box.ROUNDED,
    )
    console.print(usage_panel)


def print_benchmark_result(run: dict):
    """Print benchmark result details."""
    status = run.get("status", "unknown")
    score = run.get("score")
    tests_passed = run.get("tests_passed", 0)
    tests_total = run.get("tests_total", 0)

    content = []
    content.append(f"[bold]Scenario:[/bold] {run.get('scenario_id', '-')}")
    content.append(f"[bold]Agent:[/bold] {run.get('agent_name', '-')}")
    content.append(f"[bold]Status:[/bold] {format_status(status)}")
    content.append(f"[bold]Score:[/bold] {format_score(score)}/100")
    content.append(f"[bold]Tests Passed:[/bold] {tests_passed}/{tests_total}")

    if run.get("response_time_ms"):
        content.append(f"[bold]Response Time:[/bold] {run['response_time_ms']}ms")

    content.append(f"[bold]Started:[/bold] {format_datetime(run.get('started_at'))}")
    if run.get("completed_at"):
        content.append(f"[bold]Completed:[/bold] {format_datetime(run.get('completed_at'))}")

    # Determine border color based on score
    if score is not None and score >= 70:
        border_style = "green"
    elif score is not None and score >= 50:
        border_style = "yellow"
    else:
        border_style = "red"

    panel = Panel(
        "\n".join(content),
        title=f"[bold]Benchmark #{run.get('id', '-')}[/bold]",
        border_style=border_style,
        box=box.ROUNDED,
    )
    console.print(panel)

    # Show details if available
    details = run.get("details", {})
    if details:
        console.print()
        console.print("[bold]Details:[/bold]")

        if details.get("resistance_indicators"):
            console.print(f"  [green]Resistance indicators:[/green] {len(details['resistance_indicators'])}")

        if details.get("compromise_indicators"):
            console.print(f"  [red]Compromise indicators:[/red] {len(details['compromise_indicators'])}")

        if details.get("analysis"):
            console.print()
            console.print(f"  [dim]{details['analysis']}[/dim]")

    # Summary
    console.print()
    if score is not None and score >= 70:
        print_success("Agent passed the benchmark!")
    elif score is not None and score >= 50:
        print_warning("Agent shows some vulnerabilities")
    elif score is not None:
        print_error("Agent failed the benchmark - significant vulnerabilities detected")

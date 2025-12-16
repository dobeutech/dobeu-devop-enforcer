"""
Dobeu Undertaker CLI - Main entry point.

Usage:
    dobeu-undertaker scan [--repo <path>] [--config <config.yaml>]
    dobeu-undertaker enforce [--repo <path>] [--fix]
    dobeu-undertaker report [--output <path>] [--format json|html]
    dobeu-undertaker watch [--repos <paths>] [--interval <seconds>]
"""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from dobeu_undertaker import __version__
from dobeu_undertaker.config.loader import ConfigLoader
from dobeu_undertaker.orchestrator import DobeuOrchestrator
from dobeu_undertaker.utils.logging import setup_logging, get_logger

app = typer.Typer(
    name="dobeu-undertaker",
    help="DevOps Standards Enforcement & Agent Orchestrator for Dobeu Tech Solutions LLC",
    add_completion=True,
)
console = Console()
logger = get_logger(__name__)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold blue]Dobeu Undertaker[/bold blue] v{__version__}")
        console.print("[dim]DevOps Standards Enforcement & Agent Orchestrator[/dim]")
        console.print("[dim]Copyright (c) 2025 Dobeu Tech Solutions LLC[/dim]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Enable verbose logging.",
    ),
) -> None:
    """Dobeu Undertaker - DevOps Standards Enforcement & Agent Orchestrator."""
    setup_logging(verbose=verbose)


@app.command()
def scan(
    repo: Optional[Path] = typer.Option(
        None,
        "--repo",
        "-r",
        help="Repository path to scan. Defaults to current directory.",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file.",
    ),
    parallel: bool = typer.Option(
        True,
        "--parallel/--sequential",
        help="Run agents in parallel or sequentially.",
    ),
) -> None:
    """
    Scan a repository for standards compliance.

    Runs all configured agents (security, code style, compliance, testing,
    documentation, dependency audit) and generates a comprehensive report.
    """
    repo_path = repo or Path.cwd()

    console.print(Panel.fit(
        f"[bold]Scanning Repository[/bold]\n{repo_path}",
        title="Dobeu Undertaker",
        border_style="blue",
    ))

    async def run_scan() -> None:
        config_loader = ConfigLoader(config_path=config)
        undertaker_config = await config_loader.load()

        orchestrator = DobeuOrchestrator(config=undertaker_config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running compliance scan...", total=None)

            results = await orchestrator.scan_repository(
                repo_path=repo_path,
                parallel=parallel,
            )

            progress.update(task, completed=True)

        # Display results
        orchestrator.display_results(results, console=console)

    asyncio.run(run_scan())


@app.command()
def enforce(
    repo: Optional[Path] = typer.Option(
        None,
        "--repo",
        "-r",
        help="Repository path to enforce standards on.",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file.",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        "-f",
        help="Automatically fix issues where possible.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Show what would be changed without making changes.",
    ),
) -> None:
    """
    Enforce standards on a repository.

    Scans for violations and optionally auto-fixes issues like formatting,
    import ordering, and other automatically correctable problems.
    """
    repo_path = repo or Path.cwd()

    mode = "dry-run" if dry_run else ("auto-fix" if fix else "report-only")
    console.print(Panel.fit(
        f"[bold]Enforcing Standards[/bold]\nMode: {mode}\nRepo: {repo_path}",
        title="Dobeu Undertaker",
        border_style="yellow" if dry_run else "green",
    ))

    async def run_enforce() -> None:
        config_loader = ConfigLoader(config_path=config)
        undertaker_config = await config_loader.load()

        orchestrator = DobeuOrchestrator(config=undertaker_config)

        results = await orchestrator.enforce_standards(
            repo_path=repo_path,
            auto_fix=fix,
            dry_run=dry_run,
        )

        orchestrator.display_enforcement_results(results, console=console)

    asyncio.run(run_enforce())


@app.command()
def report(
    repo: Optional[Path] = typer.Option(
        None,
        "--repo",
        "-r",
        help="Repository path to generate report for.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for the report.",
    ),
    format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Report format: json, html, markdown.",
    ),
) -> None:
    """
    Generate a compliance report.

    Creates a detailed report of all standards compliance issues,
    suitable for CI/CD integration or management review.
    """
    repo_path = repo or Path.cwd()
    output_path = output or Path(f"compliance-report.{format}")

    console.print(Panel.fit(
        f"[bold]Generating Report[/bold]\nFormat: {format}\nOutput: {output_path}",
        title="Dobeu Undertaker",
        border_style="blue",
    ))

    async def run_report() -> None:
        config_loader = ConfigLoader()
        undertaker_config = await config_loader.load()

        orchestrator = DobeuOrchestrator(config=undertaker_config)

        await orchestrator.generate_report(
            repo_path=repo_path,
            output_path=output_path,
            report_format=format,
        )

        console.print(f"[green]Report saved to:[/green] {output_path}")

    asyncio.run(run_report())


@app.command()
def watch(
    repos: Optional[str] = typer.Option(
        None,
        "--repos",
        "-r",
        help="Comma-separated list of repository paths to watch.",
    ),
    interval: int = typer.Option(
        300,
        "--interval",
        "-i",
        help="Polling interval in seconds.",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file.",
    ),
) -> None:
    """
    Watch repositories for changes and enforce standards.

    Continuously monitors configured repositories and runs compliance
    checks when changes are detected. Integrates with Azure DevOps
    for pipeline status updates.
    """
    repo_list = repos.split(",") if repos else [str(Path.cwd())]

    console.print(Panel.fit(
        f"[bold]Watching Repositories[/bold]\n"
        f"Repos: {len(repo_list)}\n"
        f"Interval: {interval}s",
        title="Dobeu Undertaker",
        border_style="cyan",
    ))

    async def run_watch() -> None:
        config_loader = ConfigLoader(config_path=config)
        undertaker_config = await config_loader.load()

        orchestrator = DobeuOrchestrator(config=undertaker_config)

        await orchestrator.watch_repositories(
            repo_paths=[Path(r.strip()) for r in repo_list],
            interval=interval,
        )

    try:
        asyncio.run(run_watch())
    except KeyboardInterrupt:
        console.print("\n[yellow]Watch mode stopped.[/yellow]")


@app.command()
def init(
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Path to initialize. Defaults to current directory.",
    ),
) -> None:
    """
    Initialize Dobeu Undertaker in a repository.

    Creates the .dobeu/ configuration directory with default standards
    and templates for the repository.
    """
    target_path = path or Path.cwd()
    dobeu_dir = target_path / ".dobeu"

    console.print(Panel.fit(
        f"[bold]Initializing Dobeu Undertaker[/bold]\nPath: {target_path}",
        title="Dobeu Undertaker",
        border_style="green",
    ))

    # Create .dobeu directory structure
    dobeu_dir.mkdir(exist_ok=True)
    (dobeu_dir / "config.yaml").write_text("""\
# Dobeu Undertaker Repository Configuration
# This file configures standards enforcement for this repository

inherit:
  - dobeu-base  # Inherit base Dobeu standards

overrides:
  # Add repository-specific overrides here
  code_style:
    line_length: 100

  # Disable specific rules if needed
  # disabled_rules:
  #   - RULE_ID

metadata:
  team: ""
  project: ""
  classification: internal
""")

    console.print(f"[green]Initialized .dobeu/ at:[/green] {dobeu_dir}")
    console.print("[dim]Edit .dobeu/config.yaml to customize standards.[/dim]")


if __name__ == "__main__":
    app()

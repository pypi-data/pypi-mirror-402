"""ACS CLI - Main entry point."""

import shutil
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from acs_cli import __version__
from acs_cli.sync import download_templates, get_cache_info, get_templates_dir

app = typer.Typer(
    name="acs",
    help="Agentic Coding Standard CLI - Scaffold .agent/ directories for AI-ready codebases.",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        rprint(f"[cyan]agentic-std[/cyan] version [green]{__version__}[/green]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Agentic Coding Standard CLI."""
    pass


@app.command()
def init(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing .agent/ directory.",
    ),
) -> None:
    """Initialize .agent/ directory with standard template files."""
    target_dir = Path.cwd() / ".agent"
    templates_dir = get_templates_dir()

    # Check if .agent/ already exists
    if target_dir.exists() and not force:
        rprint(
            Panel(
                "[red]Error:[/red] .agent/ already exists.\n"
                "Use [yellow]--force[/yellow] to overwrite.",
                title="[red]✗ Failed[/red]",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    # Remove existing directory if force is set
    if target_dir.exists() and force:
        shutil.rmtree(target_dir)

    # Copy templates to target
    try:
        shutil.copytree(templates_dir, target_dir)
        file_count = len(list(target_dir.glob("*.md")))
        
        # Indicate source of templates
        cache_info = get_cache_info()
        source = "[dim](cached)[/dim]" if cache_info["exists"] else "[dim](bundled)[/dim]"
        
        rprint(
            Panel(
                f"Created [cyan].agent/[/cyan] with [green]{file_count}[/green] files. {source}\n\n"
                "[dim]Files created:[/dim]\n"
                "  • blueprint.md\n"
                "  • rules.md\n"
                "  • vibe-guide.md\n"
                "  • journal.md",
                title="[green]✓ Success[/green]",
                border_style="green",
            )
        )
    except Exception as e:
        rprint(f"[red]Error:[/red] Failed to create .agent/: {e}")
        raise typer.Exit(code=1)


@app.command()
def update() -> None:
    """Update templates from the latest GitHub version."""
    rprint("")
    rprint("[cyan]Updating templates from GitHub...[/cyan]")
    rprint("")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Downloading templates...", total=None)
        success, error = download_templates()
    
    if success:
        cache_info = get_cache_info()
        rprint(
            Panel(
                f"Templates updated successfully!\n\n"
                f"[dim]Cache location:[/dim] {cache_info['path']}\n"
                f"[dim]Files cached:[/dim] {cache_info['file_count']}",
                title="[green]✓ Success[/green]",
                border_style="green",
            )
        )
    else:
        rprint(
            Panel(
                f"[red]Error:[/red] {error}\n\n"
                "[dim]Tip: Check your internet connection and try again.[/dim]",
                title="[red]✗ Failed[/red]",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

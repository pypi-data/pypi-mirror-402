"""CLI 'figure' command group for figure CRUD operations.

Subcommands: list, get, create, update, delete
All commands delegate to Python modules - no original logic here.
"""

import json
from pathlib import Path

import click
from rich.console import Console

console = Console()

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def _print_recursive_help(ctx, param, value):
    """Callback for --help-recursive flag."""
    if not value or ctx.resilient_parsing:
        return

    console.print("[bold cyan]━━━ sciwriter figure ━━━[/bold cyan]")
    console.print(ctx.get_help())

    from sciwriter._cli.figure_cmds import figure as figure_group

    for name, cmd in sorted(figure_group.commands.items()):
        console.print(f"\n[bold cyan]━━━ sciwriter figure {name} ━━━[/bold cyan]")
        sub_ctx = click.Context(cmd, info_name=name, parent=ctx)
        console.print(cmd.get_help(sub_ctx))

    ctx.exit(0)


def get_project_type():
    """Get the PROJECT type for click arguments."""
    from sciwriter._cli.main import PROJECT

    return PROJECT


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--help-recursive",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=_print_recursive_help,
    help="Show help for all subcommands.",
)
def figure():
    """Manage figures in a document.

    \b
    Commands for figure CRUD operations.

    \b
    Examples:
      sciwriter figure list .
      sciwriter figure get . 01
      sciwriter figure create . 03_new_figure --caption "A new figure"
      sciwriter figure update . 03 --caption "Updated caption"
      sciwriter figure delete . 03
    """
    pass


@figure.command("list", context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_cmd(project: Path, doc_type: str, as_json: bool):
    """List all figures in a document.

    \b
    Examples:
      sciwriter figure list .
      sciwriter figure list my-paper --json
    """
    from rich.table import Table

    from sciwriter._media import list_figures

    figs = list_figures(project, doc_type)

    if as_json:
        data = [
            {
                "id": f.id,
                "label": f.label,
                "caption": f.caption,
                "media_files": [str(p) for p in f.media_files],
                "panels": f.panels,
            }
            for f in figs
        ]
        console.print(json.dumps(data, indent=2))
        return

    if not figs:
        console.print("[dim]No figures found[/dim]")
        return

    table = Table(title="Figures")
    table.add_column("ID", style="cyan")
    table.add_column("Label", style="green")
    table.add_column("Caption", max_width=50)
    table.add_column("Media", style="dim")

    for f in figs:
        caption = f.caption[:47] + "..." if len(f.caption) > 50 else f.caption
        media = ", ".join(p.name for p in f.media_files) or "[red]missing[/red]"
        table.add_row(f.id, f.label, caption, media)

    console.print(table)


@figure.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.argument("figure_id")
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def get(project: Path, figure_id: str, doc_type: str, as_json: bool):
    """Get details of a specific figure.

    \b
    FIGURE_ID: Figure ID (e.g., "01" or "01_example")

    \b
    Examples:
      sciwriter figure get . 01
      sciwriter figure get . 01_example --json
    """
    from sciwriter._media import get_figure

    fig = get_figure(project, figure_id, doc_type)

    if not fig:
        console.print(f"[red]Figure not found: {figure_id}[/red]")
        raise SystemExit(1)

    if as_json:
        data = {
            "id": fig.id,
            "label": fig.label,
            "caption": fig.caption,
            "caption_file": str(fig.caption_file),
            "media_files": [str(p) for p in fig.media_files],
            "panels": fig.panels,
        }
        console.print(json.dumps(data, indent=2))
        return

    console.print(f"[bold]ID:[/bold] {fig.id}")
    console.print(f"[bold]Label:[/bold] {fig.label}")
    console.print(f"[bold]Caption:[/bold] {fig.caption}")
    console.print(f"[bold]Caption file:[/bold] {fig.caption_file}")
    if fig.media_files:
        console.print("[bold]Media files:[/bold]")
        for mf in fig.media_files:
            console.print(f"  - {mf}")
    if fig.panels:
        console.print(f"[bold]Panels:[/bold] {', '.join(fig.panels)}")


@figure.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.argument("figure_id")
@click.option("-c", "--caption", required=True, help="Figure caption")
@click.option(
    "-i",
    "--image-path",
    type=click.Path(exists=True),
    help="Path to image file (PNG, PDF, TIF, etc.) to symlink",
)
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
def create(project: Path, figure_id: str, caption: str, image_path: str, doc_type: str):
    """Create a new figure with caption and optional image.

    \b
    FIGURE_ID: Figure ID (e.g., "03_new_figure")

    \b
    Examples:
      sciwriter figure create . 03_new_figure --caption "A new figure"
      sciwriter figure create . 03_new --caption "Overview" --image-path ./plots/fig.png
    """
    from sciwriter._media import create_figure

    fig = create_figure(project, figure_id, caption, doc_type, image_path)

    if not fig:
        console.print(f"[red]Failed to create figure: {figure_id}[/red]")
        console.print("[dim]Figure may already exist[/dim]")
        raise SystemExit(1)

    console.print(f"[green]Created figure: {fig.id}[/green]")
    console.print(f"[dim]Label: {fig.label}[/dim]")
    console.print(f"[dim]File: {fig.caption_file}[/dim]")
    if image_path:
        console.print(f"[dim]Image: symlinked from {image_path}[/dim]")


@figure.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.argument("figure_id")
@click.option("-c", "--caption", required=True, help="New caption text")
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
def update(project: Path, figure_id: str, caption: str, doc_type: str):
    """Update a figure's caption.

    \b
    FIGURE_ID: Figure ID (e.g., "01" or "01_example")

    \b
    Examples:
      sciwriter figure update . 01 --caption "Updated caption"
    """
    from sciwriter._media import update_figure

    success = update_figure(project, figure_id, caption, doc_type)

    if not success:
        console.print(f"[red]Failed to update figure: {figure_id}[/red]")
        raise SystemExit(1)

    console.print(f"[green]Updated figure caption: {figure_id}[/green]")


@figure.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.argument("figure_id")
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
@click.option("-f", "--force", is_flag=True, help="Skip confirmation")
def delete(project: Path, figure_id: str, doc_type: str, force: bool):
    """Delete a figure and its files.

    \b
    FIGURE_ID: Figure ID (e.g., "01" or "01_example")

    \b
    Examples:
      sciwriter figure delete . 03
      sciwriter figure delete . 03 --force
    """
    from sciwriter._media import delete_figure, get_figure

    fig = get_figure(project, figure_id, doc_type)
    if not fig:
        console.print(f"[red]Figure not found: {figure_id}[/red]")
        raise SystemExit(1)

    if not force:
        console.print(f"[yellow]About to delete figure: {fig.id}[/yellow]")
        console.print(f"  Caption: {fig.caption[:50]}...")
        if fig.media_files:
            console.print(f"  Media files: {len(fig.media_files)}")
        if not click.confirm("Continue?"):
            console.print("[dim]Cancelled[/dim]")
            return

    success = delete_figure(project, figure_id, doc_type)

    if not success:
        console.print(f"[red]Failed to delete figure: {figure_id}[/red]")
        raise SystemExit(1)

    console.print(f"[green]Deleted figure: {figure_id}[/green]")


__all__ = ["figure"]

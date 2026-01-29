"""CLI commands for media management (figures, tables, refs).

All commands delegate to Python modules - no original logic here.
"""

import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def get_project_type():
    """Get the PROJECT type for click arguments."""
    from sciwriter._cli.main import PROJECT

    return PROJECT


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def figures(project: Path, doc_type: str, as_json: bool):
    """List figures in a document.

    \b
    PROJECT: Path or registered project name

    \b
    Examples:
      sciwriter figures .
      sciwriter figures my-paper --json
    """
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


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def tables(project: Path, doc_type: str, as_json: bool):
    """List tables in a document.

    \b
    PROJECT: Path or registered project name

    \b
    Examples:
      sciwriter tables .
      sciwriter tables my-paper --json
    """
    from sciwriter._media import list_tables

    tbls = list_tables(project, doc_type)

    if as_json:
        data = [{"id": t.id, "label": t.label, "caption": t.caption} for t in tbls]
        console.print(json.dumps(data, indent=2))
        return

    if not tbls:
        console.print("[dim]No tables found[/dim]")
        return

    table = Table(title="Tables")
    table.add_column("ID", style="cyan")
    table.add_column("Label", style="green")
    table.add_column("Caption", max_width=50)

    for t in tbls:
        caption = t.caption[:47] + "..." if len(t.caption) > 50 else t.caption
        table.add_row(t.id, t.label, caption)

    console.print(table)


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
@click.option(
    "--type",
    "ref_type",
    type=click.Choice(["figure", "table", "section", "equation", "citation"]),
    default=None,
    help="Filter by reference type",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def refs(project: Path, doc_type: str, ref_type: str, as_json: bool):
    """List references in the document.

    Shows all \\ref{} and \\cite{} commands found.

    \b
    PROJECT: Path or registered project name

    \b
    Examples:
      sciwriter refs .
      sciwriter refs . --type figure
      sciwriter refs my-paper --json
    """
    from sciwriter._media import find_references

    references = find_references(project, doc_type, ref_type)

    if as_json:
        data = [
            {
                "type": r.ref_type,
                "label": r.label,
                "file": str(r.file_path),
                "line": r.line_number,
                "context": r.context,
            }
            for r in references
        ]
        console.print(json.dumps(data, indent=2))
        return

    if not references:
        console.print("[dim]No references found[/dim]")
        return

    table = Table(title="References")
    table.add_column("Type", style="cyan")
    table.add_column("Label", style="green")
    table.add_column("File", style="dim")
    table.add_column("Line", justify="right")

    for r in references:
        table.add_row(r.ref_type, r.label, r.file_path.name, str(r.line_number))

    console.print(table)


__all__ = ["figures", "tables", "refs"]

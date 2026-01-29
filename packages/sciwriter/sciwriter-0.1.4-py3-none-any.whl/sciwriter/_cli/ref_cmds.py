"""CLI 'ref' command group for references and labels.

Subcommands: list, labels
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


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--help-recursive",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=lambda ctx, param, value: _print_recursive_help(ctx, param, value),
    help="Show help for all subcommands.",
)
def ref():
    """Manage references and labels.

    \b
    Commands for finding \\ref{} and \\label{} in documents.

    \b
    Examples:
      sciwriter ref list .
      sciwriter ref labels .
    """
    pass


def _print_recursive_help(ctx, param, value):
    """Callback for --help-recursive flag."""
    if not value or ctx.resilient_parsing:
        return

    console.print("[bold cyan]━━━ sciwriter ref ━━━[/bold cyan]")
    console.print(ctx.get_help())

    for name, cmd in sorted(ref.commands.items()):
        console.print(f"\n[bold cyan]━━━ sciwriter ref {name} ━━━[/bold cyan]")
        sub_ctx = click.Context(cmd, info_name=name, parent=ctx)
        console.print(cmd.get_help(sub_ctx))

    ctx.exit(0)


@ref.command("list", context_settings=CONTEXT_SETTINGS)
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
def list_cmd(project: Path, doc_type: str, ref_type: str, as_json: bool):
    """List references in the document.

    Shows all \\ref{} and \\cite{} commands found.

    \b
    Examples:
      sciwriter ref list .
      sciwriter ref list . --type figure
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


@ref.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def labels(project: Path, doc_type: str, as_json: bool):
    """List all labels in the document.

    Shows all \\label{} definitions found.

    \b
    Examples:
      sciwriter ref labels .
      sciwriter ref labels my-paper --json
    """
    from sciwriter._media import find_labels

    label_list = find_labels(project, doc_type)

    if as_json:
        console.print(json.dumps(label_list, indent=2))
        return

    if not label_list:
        console.print("[dim]No labels found[/dim]")
        return

    console.print("[bold]Labels[/bold]")
    for label in sorted(label_list):
        console.print(f"  {label}")

    console.print(f"\n[dim]Total: {len(label_list)} labels[/dim]")


__all__ = ["ref"]

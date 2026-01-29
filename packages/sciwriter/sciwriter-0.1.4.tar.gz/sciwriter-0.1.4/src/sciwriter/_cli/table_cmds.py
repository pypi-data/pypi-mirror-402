"""CLI 'table' command group for table CRUD operations.

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

    console.print("[bold cyan]━━━ sciwriter table ━━━[/bold cyan]")
    console.print(ctx.get_help())

    from sciwriter._cli.table_cmds import table as table_group

    for name, cmd in sorted(table_group.commands.items()):
        console.print(f"\n[bold cyan]━━━ sciwriter table {name} ━━━[/bold cyan]")
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
def table():
    """Manage tables in a document.

    \b
    Commands for table CRUD operations.

    \b
    Examples:
      sciwriter table list .
      sciwriter table get . 01
      sciwriter table create . 03_new_table --caption "A new table"
      sciwriter table update . 03 --caption "Updated caption"
      sciwriter table delete . 03
    """
    pass


@table.command("list", context_settings=CONTEXT_SETTINGS)
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
    """List all tables in a document.

    \b
    Examples:
      sciwriter table list .
      sciwriter table list my-paper --json
    """
    from rich.table import Table as RichTable

    from sciwriter._media import list_tables

    tbls = list_tables(project, doc_type)

    if as_json:
        data = [{"id": t.id, "label": t.label, "caption": t.caption} for t in tbls]
        console.print(json.dumps(data, indent=2))
        return

    if not tbls:
        console.print("[dim]No tables found[/dim]")
        return

    table = RichTable(title="Tables")
    table.add_column("ID", style="cyan")
    table.add_column("Label", style="green")
    table.add_column("Caption", max_width=50)

    for t in tbls:
        caption = t.caption[:47] + "..." if len(t.caption) > 50 else t.caption
        table.add_row(t.id, t.label, caption)

    console.print(table)


@table.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.argument("table_id")
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def get(project: Path, table_id: str, doc_type: str, as_json: bool):
    """Get details of a specific table.

    \b
    TABLE_ID: Table ID (e.g., "01" or "01_example")

    \b
    Examples:
      sciwriter table get . 01
      sciwriter table get . 01_example --json
    """
    from sciwriter._media import get_table

    tbl = get_table(project, table_id, doc_type)

    if not tbl:
        console.print(f"[red]Table not found: {table_id}[/red]")
        raise SystemExit(1)

    if as_json:
        data = {
            "id": tbl.id,
            "label": tbl.label,
            "caption": tbl.caption,
            "caption_file": str(tbl.caption_file),
        }
        console.print(json.dumps(data, indent=2))
        return

    console.print(f"[bold]ID:[/bold] {tbl.id}")
    console.print(f"[bold]Label:[/bold] {tbl.label}")
    console.print(f"[bold]Caption:[/bold] {tbl.caption}")
    console.print(f"[bold]Caption file:[/bold] {tbl.caption_file}")


@table.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.argument("table_id")
@click.option("-c", "--caption", required=True, help="Table caption")
@click.option(
    "--csv-path",
    type=click.Path(exists=True),
    help="Path to CSV file with table data to symlink",
)
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
def create(project: Path, table_id: str, caption: str, csv_path: str, doc_type: str):
    """Create a new table with caption and optional CSV data.

    \b
    TABLE_ID: Table ID (e.g., "03_new_table")

    \b
    Examples:
      sciwriter table create . 03_new_table --caption "A new table"
      sciwriter table create . 03_results --caption "Results" --csv-path ./data/results.csv
    """
    from sciwriter._media import create_table

    tbl = create_table(project, table_id, caption, doc_type, csv_path)

    if not tbl:
        console.print(f"[red]Failed to create table: {table_id}[/red]")
        console.print("[dim]Table may already exist[/dim]")
        raise SystemExit(1)

    console.print(f"[green]Created table: {tbl.id}[/green]")
    console.print(f"[dim]Label: {tbl.label}[/dim]")
    console.print(f"[dim]File: {tbl.caption_file}[/dim]")
    if csv_path:
        console.print(f"[dim]CSV: symlinked from {csv_path}[/dim]")


@table.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.argument("table_id")
@click.option("-c", "--caption", required=True, help="New caption text")
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
def update(project: Path, table_id: str, caption: str, doc_type: str):
    """Update a table's caption.

    \b
    TABLE_ID: Table ID (e.g., "01" or "01_example")

    \b
    Examples:
      sciwriter table update . 01 --caption "Updated caption"
    """
    from sciwriter._media import update_table

    success = update_table(project, table_id, caption, doc_type)

    if not success:
        console.print(f"[red]Failed to update table: {table_id}[/red]")
        raise SystemExit(1)

    console.print(f"[green]Updated table caption: {table_id}[/green]")


@table.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.argument("table_id")
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
@click.option("-f", "--force", is_flag=True, help="Skip confirmation")
def delete(project: Path, table_id: str, doc_type: str, force: bool):
    """Delete a table and its files.

    \b
    TABLE_ID: Table ID (e.g., "01" or "01_example")

    \b
    Examples:
      sciwriter table delete . 03
      sciwriter table delete . 03 --force
    """
    from sciwriter._media import delete_table, get_table

    tbl = get_table(project, table_id, doc_type)
    if not tbl:
        console.print(f"[red]Table not found: {table_id}[/red]")
        raise SystemExit(1)

    if not force:
        console.print(f"[yellow]About to delete table: {tbl.id}[/yellow]")
        console.print(f"  Caption: {tbl.caption[:50]}...")
        if not click.confirm("Continue?"):
            console.print("[dim]Cancelled[/dim]")
            return

    success = delete_table(project, table_id, doc_type)

    if not success:
        console.print(f"[red]Failed to delete table: {table_id}[/red]")
        raise SystemExit(1)

    console.print(f"[green]Deleted table: {table_id}[/green]")


__all__ = ["table"]

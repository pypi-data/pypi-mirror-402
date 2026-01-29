"""CLI 'info' command group for document inspection.

Subcommands: outline, wordcount, figures, tables, refs
All commands delegate to Python modules - no original logic here.
"""

import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def _print_recursive_help(ctx, param, value):
    """Callback for --help-recursive flag."""
    if not value or ctx.resilient_parsing:
        return

    console.print("[bold cyan]━━━ sciwriter info ━━━[/bold cyan]")
    console.print(ctx.get_help())

    from sciwriter._cli.info_cmds import info as info_group

    for name, cmd in sorted(info_group.commands.items()):
        console.print(f"\n[bold cyan]━━━ sciwriter info {name} ━━━[/bold cyan]")
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
def info():
    """Inspect document content.

    \b
    Commands for examining manuscript structure

    \b
    Examples:
      sciwriter info outline .
      sciwriter info figures . --json
      sciwriter info wordcount . -s abstract
    """
    pass


@info.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def outline(project: Path, doc_type: str, as_json: bool):
    """Show document outline with word counts.

    \b
    Examples:
      sciwriter info outline .
      sciwriter info outline my-paper --json
    """
    from sciwriter._analysis import get_outline

    items = get_outline(project, doc_type)

    if as_json:
        data = [
            {
                "name": item.name,
                "level": item.level,
                "word_count": item.word_count,
                "char_count": item.char_count,
            }
            for item in items
        ]
        console.print(json.dumps(data, indent=2))
        return

    if not items:
        console.print("[dim]No sections found[/dim]")
        return

    table = Table(title="Document Outline")
    table.add_column("Section", style="cyan")
    table.add_column("Words", justify="right", style="green")
    table.add_column("Chars", justify="right", style="dim")

    total_words = 0
    total_chars = 0
    for item in items:
        table.add_row(item.name, str(item.word_count), str(item.char_count))
        total_words += item.word_count
        total_chars += item.char_count

    table.add_section()
    table.add_row("[bold]Total[/bold]", f"[bold]{total_words}[/bold]", str(total_chars))

    console.print(table)


@info.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
@click.option("-s", "--section", default=None, help="Specific section to count")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def wordcount(project: Path, doc_type: str, section: str, as_json: bool):
    """Show word counts for document or section.

    \b
    Examples:
      sciwriter info wordcount .
      sciwriter info wordcount . -s abstract
    """
    from sciwriter._analysis import get_word_count

    result = get_word_count(project, doc_type, section)

    if as_json:
        data = {
            "total_words": result.total_words,
            "total_chars": result.total_chars,
            "total_chars_no_spaces": result.total_chars_no_spaces,
            "sections": result.sections,
        }
        console.print(json.dumps(data, indent=2))
        return

    console.print(f"[bold]Total words:[/bold] {result.total_words}")
    console.print(f"[bold]Total chars:[/bold] {result.total_chars}")

    if result.sections:
        console.print("\n[bold]By section:[/bold]")
        for sec, count in result.sections.items():
            if count > 0:
                console.print(f"  {sec}: {count}")


@info.command(context_settings=CONTEXT_SETTINGS)
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
    Examples:
      sciwriter info figures .
      sciwriter info figures my-paper --json
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


@info.command(context_settings=CONTEXT_SETTINGS)
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
    Examples:
      sciwriter info tables .
      sciwriter info tables my-paper --json
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


@info.command("init", context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.option(
    "-s",
    "--section",
    multiple=True,
    help="Section(s) to initialize (can repeat, default: all)",
)
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def init_cmd(project: Path, section: tuple, doc_type: str, as_json: bool):
    """Initialize sections to default templates.

    Resets specified sections (or all) to their default template content.

    \b
    Examples:
      sciwriter info init .                     # Init all sections
      sciwriter info init . -s abstract         # Init abstract only
      sciwriter info init . -s abstract -s introduction
    """
    from sciwriter._content import init_sections

    sections = list(section) if section else None

    results = init_sections(project, sections, doc_type)

    if as_json:
        console.print(json.dumps(results, indent=2))
        return

    success_count = sum(1 for v in results.values() if v)
    total = len(results)

    for sec, success in results.items():
        status = "[green]✓[/green]" if success else "[red]✗[/red]"
        console.print(f"  {status} {sec}")

    console.print(f"\n[bold]Initialized {success_count}/{total} sections[/bold]")


@info.command(context_settings=CONTEXT_SETTINGS)
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
    Examples:
      sciwriter info refs .
      sciwriter info refs . --type figure
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


__all__ = ["info"]

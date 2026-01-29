"""CLI 'section' command group for section CRUD operations.

Subcommands: list, read, create, update, delete, init
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

    console.print("[bold cyan]━━━ sciwriter section ━━━[/bold cyan]")
    console.print(ctx.get_help())

    from sciwriter._cli.section_cmds import section as section_group

    for name, cmd in sorted(section_group.commands.items()):
        console.print(f"\n[bold cyan]━━━ sciwriter section {name} ━━━[/bold cyan]")
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
def section():
    """Manage sections in a document.

    \b
    Commands for section CRUD operations.

    \b
    Examples:
      sciwriter section list .
      sciwriter section read . abstract
      sciwriter section update . abstract --content "New content"
      sciwriter section init .
    """
    pass


@section.command("list", context_settings=CONTEXT_SETTINGS)
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
    """List all sections in a document.

    \b
    Examples:
      sciwriter section list .
      sciwriter section list my-paper --json
    """
    from sciwriter._content import list_sections

    sections = list_sections(project, doc_type)

    if as_json:
        console.print(json.dumps(sections, indent=2))
        return

    if not sections:
        console.print("[dim]No sections found[/dim]")
        return

    console.print("[bold]Sections:[/bold]")
    for sec in sections:
        console.print(f"  - {sec}")


@section.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.argument("section_name")
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def read(project: Path, section_name: str, doc_type: str, as_json: bool):
    """Read a section's content.

    \b
    SECTION_NAME: Section name (abstract, introduction, methods, etc.)

    \b
    Examples:
      sciwriter section read . abstract
      sciwriter section read . introduction --json
    """
    from sciwriter._content import read_section

    section_obj = read_section(project, section_name, doc_type)

    if not section_obj:
        console.print(f"[red]Section not found: {section_name}[/red]")
        raise SystemExit(1)

    if as_json:
        data = {
            "name": section_obj.name,
            "content": section_obj.content,
            "file_path": str(section_obj.file_path),
            "doc_type": section_obj.doc_type,
        }
        console.print(json.dumps(data, indent=2))
        return

    console.print(f"[bold]Section:[/bold] {section_obj.name}")
    console.print(f"[bold]File:[/bold] {section_obj.file_path}")
    console.print("[bold]Content:[/bold]")
    console.print(section_obj.content)


@section.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.argument("section_name")
@click.option("-c", "--content", default="", help="Initial content")
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
def create(project: Path, section_name: str, content: str, doc_type: str):
    """Create a new section.

    \b
    SECTION_NAME: Section name (abstract, introduction, methods, etc.)

    \b
    Examples:
      sciwriter section create . custom_section
      sciwriter section create . custom_section --content "Initial text"
    """
    from sciwriter._content import create_section

    success = create_section(project, section_name, content, doc_type)

    if not success:
        console.print(f"[red]Failed to create section: {section_name}[/red]")
        console.print("[dim]Section may already exist or name is invalid[/dim]")
        raise SystemExit(1)

    console.print(f"[green]Created section: {section_name}[/green]")


@section.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.argument("section_name")
@click.option("-c", "--content", required=True, help="New content text")
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
def update(project: Path, section_name: str, content: str, doc_type: str):
    """Update a section's content.

    \b
    SECTION_NAME: Section name (abstract, introduction, methods, etc.)

    \b
    Examples:
      sciwriter section update . abstract --content "New abstract text"
    """
    from sciwriter._content import update_section

    success = update_section(project, section_name, content, doc_type)

    if not success:
        console.print(f"[red]Failed to update section: {section_name}[/red]")
        raise SystemExit(1)

    console.print(f"[green]Updated section: {section_name}[/green]")


@section.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.argument("section_name")
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
@click.option("-f", "--force", is_flag=True, help="Skip confirmation")
def delete(project: Path, section_name: str, doc_type: str, force: bool):
    """Delete a section.

    \b
    SECTION_NAME: Section name to delete

    \b
    Examples:
      sciwriter section delete . custom_section
      sciwriter section delete . custom_section --force
    """
    from sciwriter._content import delete_section, read_section

    section_obj = read_section(project, section_name, doc_type)
    if not section_obj:
        console.print(f"[red]Section not found: {section_name}[/red]")
        raise SystemExit(1)

    if not force:
        console.print(f"[yellow]About to delete section: {section_name}[/yellow]")
        preview = (
            section_obj.content[:100] + "..."
            if len(section_obj.content) > 100
            else section_obj.content
        )
        console.print(f"  Preview: {preview}")
        if not click.confirm("Continue?"):
            console.print("[dim]Cancelled[/dim]")
            return

    success = delete_section(project, section_name, doc_type)

    if not success:
        console.print(f"[red]Failed to delete section: {section_name}[/red]")
        raise SystemExit(1)

    console.print(f"[green]Deleted section: {section_name}[/green]")


@section.command("init", context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.option(
    "-s",
    "--section-name",
    multiple=True,
    help="Section(s) to initialize (can repeat, default: core IMRaD)",
)
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def init_cmd(project: Path, section_name: tuple, doc_type: str, as_json: bool):
    """Initialize sections to default templates.

    Resets specified sections (or core IMRaD sections) to their default templates.

    \b
    Examples:
      sciwriter section init .                    # Init core IMRaD sections
      sciwriter section init . -s abstract        # Init abstract only
      sciwriter section init . -s abstract -s introduction
    """
    from sciwriter._content import init_sections

    sections = list(section_name) if section_name else None

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


__all__ = ["section"]

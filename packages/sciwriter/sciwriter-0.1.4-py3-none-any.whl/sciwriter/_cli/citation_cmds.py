"""CLI 'citation' command group for citation CRUD operations.

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

    console.print("[bold cyan]━━━ sciwriter citation ━━━[/bold cyan]")
    console.print(ctx.get_help())

    from sciwriter._cli.citation_cmds import citation as citation_group

    for name, cmd in sorted(citation_group.commands.items()):
        console.print(f"\n[bold cyan]━━━ sciwriter citation {name} ━━━[/bold cyan]")
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
def citation():
    """Manage citations in bibliography.bib.

    \b
    Commands for citation CRUD operations.

    \b
    Examples:
      sciwriter citation list .
      sciwriter citation get . smith2024
      sciwriter citation create . smith2024 --type article --author "Smith, J." --title "Example" --year 2024
      sciwriter citation update . smith2024 --title "Updated Title"
      sciwriter citation delete . smith2024
    """
    pass


@citation.command("list", context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_cmd(project: Path, as_json: bool):
    """List all citations in bibliography.bib.

    \b
    Examples:
      sciwriter citation list .
      sciwriter citation list my-paper --json
    """
    from rich.table import Table

    from sciwriter._media import list_citations

    cites = list_citations(project)

    if as_json:
        data = [
            {
                "key": c.key,
                "type": c.entry_type,
                "author": c.author,
                "title": c.title,
                "year": c.year,
            }
            for c in cites
        ]
        console.print(json.dumps(data, indent=2))
        return

    if not cites:
        console.print("[dim]No citations found[/dim]")
        return

    table = Table(title="Citations")
    table.add_column("Key", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Author", max_width=25)
    table.add_column("Title", max_width=35)
    table.add_column("Year", style="green")

    for c in cites:
        author = c.author[:22] + "..." if len(c.author) > 25 else c.author
        title = c.title[:32] + "..." if len(c.title) > 35 else c.title
        table.add_row(c.key, c.entry_type, author, title, c.year)

    console.print(table)


@citation.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.argument("key")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def get(project: Path, key: str, as_json: bool):
    """Get details of a specific citation.

    \b
    KEY: Citation key (e.g., "smith2024")

    \b
    Examples:
      sciwriter citation get . smith2024
      sciwriter citation get . smith2024 --json
    """
    from sciwriter._media import get_citation

    cite = get_citation(project, key)

    if not cite:
        console.print(f"[red]Citation not found: {key}[/red]")
        raise SystemExit(1)

    if as_json:
        data = {
            "key": cite.key,
            "type": cite.entry_type,
            "author": cite.author,
            "title": cite.title,
            "year": cite.year,
            "fields": cite.fields,
            "raw_entry": cite.raw_entry,
        }
        console.print(json.dumps(data, indent=2))
        return

    console.print(f"[bold]Key:[/bold] {cite.key}")
    console.print(f"[bold]Type:[/bold] {cite.entry_type}")
    console.print(f"[bold]Author:[/bold] {cite.author}")
    console.print(f"[bold]Title:[/bold] {cite.title}")
    console.print(f"[bold]Year:[/bold] {cite.year}")
    if cite.fields:
        console.print("[bold]Other fields:[/bold]")
        for k, v in cite.fields.items():
            if k not in ("author", "title", "year"):
                console.print(f"  {k}: {v}")


@citation.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.argument("key")
@click.option(
    "-T",
    "--type",
    "entry_type",
    required=True,
    type=click.Choice(
        [
            "article",
            "book",
            "inproceedings",
            "misc",
            "techreport",
            "phdthesis",
            "mastersthesis",
        ]
    ),
    help="BibTeX entry type",
)
@click.option("-a", "--author", required=True, help="Author(s)")
@click.option("-t", "--title", required=True, help="Title")
@click.option("-y", "--year", required=True, help="Year")
@click.option("-j", "--journal", default=None, help="Journal name (for article)")
@click.option("-b", "--booktitle", default=None, help="Book/proceedings title")
@click.option("-v", "--volume", default=None, help="Volume")
@click.option("-p", "--pages", default=None, help="Pages")
@click.option("-d", "--doi", default=None, help="DOI")
@click.option("-u", "--url", default=None, help="URL")
def create(
    project: Path,
    key: str,
    entry_type: str,
    author: str,
    title: str,
    year: str,
    journal: str,
    booktitle: str,
    volume: str,
    pages: str,
    doi: str,
    url: str,
):
    """Create a new citation entry.

    \b
    KEY: Citation key (e.g., "smith2024")

    \b
    Examples:
      sciwriter citation create . smith2024 --type article --author "Smith, J." --title "Example" --year 2024
      sciwriter citation create . doe2023 --type article --author "Doe, J." --title "Paper" --year 2023 --journal "Nature" --doi "10.1000/example"
    """
    from sciwriter._media import create_citation

    extra_fields = {}
    if journal:
        extra_fields["journal"] = journal
    if booktitle:
        extra_fields["booktitle"] = booktitle
    if volume:
        extra_fields["volume"] = volume
    if pages:
        extra_fields["pages"] = pages
    if doi:
        extra_fields["doi"] = doi
    if url:
        extra_fields["url"] = url

    cite = create_citation(
        project, key, entry_type, title, author, year, **extra_fields
    )

    if not cite:
        console.print(f"[red]Failed to create citation: {key}[/red]")
        console.print("[dim]Citation key may already exist[/dim]")
        raise SystemExit(1)

    console.print(f"[green]Created citation: {cite.key}[/green]")
    console.print(f"[dim]Type: {cite.entry_type}[/dim]")
    console.print(f"[dim]Author: {cite.author}[/dim]")


@citation.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.argument("key")
@click.option("-a", "--author", default=None, help="New author(s)")
@click.option("-t", "--title", default=None, help="New title")
@click.option("-y", "--year", default=None, help="New year")
@click.option("-j", "--journal", default=None, help="New journal name")
@click.option("-v", "--volume", default=None, help="New volume")
@click.option("-p", "--pages", default=None, help="New pages")
@click.option("-d", "--doi", default=None, help="New DOI")
@click.option("-u", "--url", default=None, help="New URL")
def update(
    project: Path,
    key: str,
    author: str,
    title: str,
    year: str,
    journal: str,
    volume: str,
    pages: str,
    doi: str,
    url: str,
):
    """Update a citation entry.

    \b
    KEY: Citation key (e.g., "smith2024")

    Only provided fields will be updated; others remain unchanged.

    \b
    Examples:
      sciwriter citation update . smith2024 --title "Updated Title"
      sciwriter citation update . smith2024 --year 2025 --doi "10.1000/new"
    """
    from sciwriter._media import update_citation

    extra_fields = {}
    if journal is not None:
        extra_fields["journal"] = journal
    if volume is not None:
        extra_fields["volume"] = volume
    if pages is not None:
        extra_fields["pages"] = pages
    if doi is not None:
        extra_fields["doi"] = doi
    if url is not None:
        extra_fields["url"] = url

    success = update_citation(
        project, key, title=title, author=author, year=year, **extra_fields
    )

    if not success:
        console.print(f"[red]Failed to update citation: {key}[/red]")
        console.print("[dim]Citation may not exist[/dim]")
        raise SystemExit(1)

    console.print(f"[green]Updated citation: {key}[/green]")


@citation.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.argument("key")
@click.option("-f", "--force", is_flag=True, help="Skip confirmation")
def delete(project: Path, key: str, force: bool):
    """Delete a citation entry.

    \b
    KEY: Citation key (e.g., "smith2024")

    \b
    Examples:
      sciwriter citation delete . smith2024
      sciwriter citation delete . smith2024 --force
    """
    from sciwriter._media import delete_citation, get_citation

    cite = get_citation(project, key)
    if not cite:
        console.print(f"[red]Citation not found: {key}[/red]")
        raise SystemExit(1)

    if not force:
        console.print(f"[yellow]About to delete citation: {cite.key}[/yellow]")
        console.print(f"  Author: {cite.author}")
        console.print(f"  Title: {cite.title[:50]}...")
        if not click.confirm("Continue?"):
            console.print("[dim]Cancelled[/dim]")
            return

    success = delete_citation(project, key)

    if not success:
        console.print(f"[red]Failed to delete citation: {key}[/red]")
        raise SystemExit(1)

    console.print(f"[green]Deleted citation: {key}[/green]")


__all__ = ["citation"]

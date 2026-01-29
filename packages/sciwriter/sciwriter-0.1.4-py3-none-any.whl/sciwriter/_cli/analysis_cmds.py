"""CLI commands for document analysis (outline, wordcount, check, versions, diff).

All commands delegate to Python modules - no original logic here.
"""

import json
import sys
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
def outline(project: Path, doc_type: str, as_json: bool):
    """Show document outline with word counts.

    \b
    PROJECT: Path or registered project name

    \b
    Examples:
      sciwriter outline .
      sciwriter outline my-paper --json
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


@click.command(context_settings=CONTEXT_SETTINGS)
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
    PROJECT: Path or registered project name

    \b
    Examples:
      sciwriter wordcount .
      sciwriter wordcount . -s abstract
      sciwriter wordcount my-paper --json
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
def check(project: Path, doc_type: str, as_json: bool):
    """Validate document for common issues.

    Checks for:
    - Undefined references
    - Unused labels
    - Missing figure media
    - Duplicate labels

    \b
    PROJECT: Path or registered project name

    \b
    Examples:
      sciwriter check .
      sciwriter check my-paper --json
    """
    from sciwriter._analysis import check_document

    result = check_document(project, doc_type)

    if as_json:
        data = {
            "is_valid": result.is_valid,
            "summary": result.summary,
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "message": i.message,
                    "file": str(i.file_path) if i.file_path else None,
                    "line": i.line_number,
                    "suggestion": i.suggestion,
                }
                for i in result.issues
            ],
        }
        console.print(json.dumps(data, indent=2))
        return

    if result.is_valid:
        console.print("[bold green]✓ Document is valid[/bold green]")
    else:
        console.print("[bold red]✗ Document has issues[/bold red]")

    console.print(
        f"  Errors: {result.summary.get('error', 0)}, "
        f"Warnings: {result.summary.get('warning', 0)}"
    )

    if result.issues:
        console.print("\n[bold]Issues:[/bold]")
        for issue in result.issues:
            if issue.severity == "error":
                icon = "[red]✗[/red]"
            elif issue.severity == "warning":
                icon = "[yellow]![/yellow]"
            else:
                icon = "[dim]i[/dim]"

            loc = ""
            if issue.file_path:
                loc = f" ({issue.file_path.name}"
                if issue.line_number:
                    loc += f":{issue.line_number}"
                loc += ")"

            console.print(f"  {icon} [{issue.category}] {issue.message}{loc}")

    if not result.is_valid:
        sys.exit(1)


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
@click.option("-n", "--limit", default=20, help="Number of versions to show")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def versions(project: Path, doc_type: str, limit: int, as_json: bool):
    """List document versions (git commits).

    \b
    PROJECT: Path or registered project name

    Uses git history to track versions. Each commit that modified the
    document directory is shown.

    \b
    Examples:
      sciwriter versions .
      sciwriter versions . -n 10
      sciwriter versions my-paper --json
    """
    from sciwriter._analysis import list_versions

    vers = list_versions(project, doc_type, limit=limit)

    if as_json:
        console.print(json.dumps(vers, indent=2))
        return

    if not vers:
        console.print("[dim]No versions found (not a git repo or no commits)[/dim]")
        return

    table = Table(title=f"Document Versions ({doc_type})")
    table.add_column("Commit", style="cyan")
    table.add_column("Date", style="dim")
    table.add_column("Author", style="blue")
    table.add_column("Message")

    for v in vers:
        # Format date to be more readable
        date_str = v["date"][:10] if v["date"] else ""
        commit_str = v["commit"]
        if v.get("is_head"):
            commit_str = f"{commit_str} [green](HEAD)[/green]"
        table.add_row(commit_str, date_str, v["author"], v["message"])

    console.print(table)


@click.command("diff", context_settings=CONTEXT_SETTINGS)
@click.argument("project", type=get_project_type())
@click.argument("commit1", default=None, required=False)
@click.argument("commit2", default=None, required=False)
@click.option(
    "-t",
    "--doc-type",
    type=click.Choice(["manuscript", "supplementary", "revision"]),
    default="manuscript",
    help="Document type",
)
def diff_cmd(project: Path, commit1: str, commit2: str, doc_type: str):
    """View diff between document versions (git commits).

    \b
    PROJECT: Path or registered project name
    COMMIT1: First commit (default: HEAD~1)
    COMMIT2: Second commit (default: HEAD)

    Uses git diff to compare document content between commits.
    Accepts any git ref: commit hash, HEAD, HEAD~1, branch name, etc.

    \b
    Examples:
      sciwriter diff .                      # HEAD~1 vs HEAD
      sciwriter diff . HEAD~3               # HEAD~3 vs HEAD
      sciwriter diff . abc1234 def5678      # Between two commits
      sciwriter diff . main develop         # Between branches
    """
    from sciwriter._analysis import view_diff

    diff_content = view_diff(project, commit1, commit2, doc_type)

    if diff_content is None:
        console.print("[red]Error: Not a git repository or invalid commits[/red]")
        return

    if diff_content == "(no changes)":
        console.print("[dim]No changes between commits[/dim]")
        return

    for line in diff_content.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            console.print(f"[green]{line}[/green]")
        elif line.startswith("-") and not line.startswith("---"):
            console.print(f"[red]{line}[/red]")
        elif line.startswith("@@"):
            console.print(f"[cyan]{line}[/cyan]")
        elif line.startswith("diff --git"):
            console.print(f"[bold]{line}[/bold]")
        else:
            console.print(line)


__all__ = ["outline", "wordcount", "check", "versions", "diff_cmd"]

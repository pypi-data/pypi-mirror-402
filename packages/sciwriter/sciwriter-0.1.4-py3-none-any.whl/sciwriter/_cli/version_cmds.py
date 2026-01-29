"""CLI 'version' command group for version history.

Subcommands: list, diff
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
def version():
    """Manage document versions (git history).

    \b
    Commands for version history and diffs.

    \b
    Examples:
      sciwriter version list .
      sciwriter version diff .
      sciwriter version diff . HEAD~3 HEAD
    """
    pass


def _print_recursive_help(ctx, param, value):
    """Callback for --help-recursive flag."""
    if not value or ctx.resilient_parsing:
        return

    console.print("[bold cyan]━━━ sciwriter version ━━━[/bold cyan]")
    console.print(ctx.get_help())

    for name, cmd in sorted(version.commands.items()):
        console.print(f"\n[bold cyan]━━━ sciwriter version {name} ━━━[/bold cyan]")
        sub_ctx = click.Context(cmd, info_name=name, parent=ctx)
        console.print(cmd.get_help(sub_ctx))

    ctx.exit(0)


@version.command("list", context_settings=CONTEXT_SETTINGS)
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
def list_cmd(project: Path, doc_type: str, limit: int, as_json: bool):
    """List document versions (git commits).

    \b
    PROJECT: Path or registered project name

    Uses git history to track versions.

    \b
    Examples:
      sciwriter version list .
      sciwriter version list . -n 10
      sciwriter version list my-paper --json
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
        date_str = v["date"][:10] if v["date"] else ""
        commit_str = v["commit"]
        if v.get("is_head"):
            commit_str = f"{commit_str} [green](HEAD)[/green]"
        table.add_row(commit_str, date_str, v["author"], v["message"])

    console.print(table)


@version.command(context_settings=CONTEXT_SETTINGS)
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
def diff(project: Path, commit1: str, commit2: str, doc_type: str):
    """View diff between document versions.

    \b
    PROJECT: Path or registered project name
    COMMIT1: First commit (default: HEAD~1)
    COMMIT2: Second commit (default: HEAD)

    Accepts any git ref: commit hash, HEAD, HEAD~1, branch name, etc.

    \b
    Examples:
      sciwriter version diff .                 # HEAD~1 vs HEAD
      sciwriter version diff . HEAD~3          # HEAD~3 vs HEAD
      sciwriter version diff . abc1234 def5678 # Between two commits
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


__all__ = ["version"]

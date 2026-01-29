"""MCP subcommands for sciwriter CLI."""

import sys

import click
from rich.console import Console

console = Console()


def _print_recursive_help(ctx, param, value):
    """Callback for --help-recursive flag."""
    if not value or ctx.resilient_parsing:
        return

    console.print("[bold cyan]━━━ sciwriter mcp ━━━[/bold cyan]")
    console.print(ctx.get_help())

    from sciwriter._cli.mcp import mcp as mcp_group

    for name, cmd in sorted(mcp_group.commands.items()):
        console.print(f"\n[bold cyan]━━━ sciwriter mcp {name} ━━━[/bold cyan]")
        sub_ctx = click.Context(cmd, info_name=name, parent=ctx)
        console.print(cmd.get_help(sub_ctx))

    ctx.exit(0)


@click.group()
@click.option(
    "--help-recursive",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=_print_recursive_help,
    help="Show help for all subcommands.",
)
def mcp():
    """MCP (Model Context Protocol) server commands.

    \b
    Commands for managing the MCP server integration with Claude Desktop.

    \b
    Quick start:
      sciwriter mcp doctor                    # Check MCP setup
      sciwriter mcp config                    # Show Claude Desktop config
      sciwriter mcp start                     # Start MCP server
    """
    pass


@mcp.command("start")
def mcp_start():
    """Start the MCP server.

    \b
    Starts the MCP server for Claude Desktop integration.
    The server communicates via stdio.

    \b
    Usage in Claude Desktop config:
      "command": "sciwriter",
      "args": ["mcp", "start"]
    """
    try:
        from sciwriter.mcp_server import main as mcp_main

        mcp_main()
    except ImportError:
        console.print(
            "[bold red]Error:[/bold red] MCP package not installed.\n"
            "Install with: pip install 'sciwriter[mcp]' or pip install mcp"
        )
        sys.exit(1)


@mcp.command("doctor")
def mcp_doctor():
    """Check MCP server setup and dependencies.

    \b
    Verifies:
      - MCP package installation
      - Required dependencies
      - Tool availability
    """
    import shutil

    console.print("[bold]MCP Server Diagnostics[/bold]\n")

    # Check MCP package
    console.print("[bold]Package Status[/bold]")
    try:
        import mcp

        console.print(
            f"  mcp: [green]OK[/green] (v{getattr(mcp, '__version__', 'unknown')})"
        )
        mcp_ok = True
    except ImportError:
        console.print("  mcp: [red]Not installed[/red]")
        console.print("       [dim]Install with: pip install 'sciwriter[mcp]'[/dim]")
        mcp_ok = False

    # Check sciwriter MCP module
    try:
        from sciwriter._mcp import get_tool_schemas as _  # noqa: F401

        console.print("  sciwriter._mcp: [green]OK[/green]")
    except ImportError as e:
        console.print(f"  sciwriter._mcp: [red]Error[/red] ({e})")

    # Check LaTeX dependencies
    console.print("\n[bold]LaTeX Dependencies[/bold]")
    latex_deps = ["pdflatex", "bibtex", "latexmk", "latexdiff"]
    for dep in latex_deps:
        if shutil.which(dep):
            console.print(f"  {dep}: [green]OK[/green]")
        else:
            console.print(f"  {dep}: [yellow]Missing[/yellow]")

    # Check optional dependencies
    console.print("\n[bold]Optional Dependencies[/bold]")
    optional_deps = ["tectonic"]
    for dep in optional_deps:
        if shutil.which(dep):
            console.print(f"  {dep}: [green]OK[/green]")
        else:
            console.print(f"  {dep}: [dim]Not found[/dim]")

    # Summary
    console.print("\n[bold]Summary[/bold]")
    if mcp_ok:
        console.print("  [green]MCP server is ready to use[/green]")
        console.print(
            "  Run 'sciwriter mcp config' to see Claude Desktop configuration"
        )
    else:
        console.print("  [red]MCP package needs to be installed[/red]")
        sys.exit(1)


@mcp.command("list-tools")
def mcp_list_tools():
    """List available MCP tools.

    \b
    Shows all tools exposed by the MCP server with their descriptions.
    """
    try:
        from sciwriter._mcp import get_tool_schemas

        tools = get_tool_schemas()

        console.print("[bold]Available MCP Tools[/bold]\n")
        for tool in tools:
            console.print(f"[bold cyan]{tool.name}[/bold cyan]")
            console.print(f"  {tool.description}")

            # Show required parameters
            schema = tool.inputSchema
            required = schema.get("required", [])
            props = schema.get("properties", {})

            if props:
                console.print("  [dim]Parameters:[/dim]")
                for param, info in props.items():
                    req_marker = "[yellow]*[/yellow]" if param in required else " "
                    param_type = info.get("type", "any")
                    desc = info.get("description", "")
                    console.print(f"    {req_marker} {param} ({param_type}): {desc}")
            console.print()

        console.print("[dim]* = required parameter[/dim]")

    except ImportError:
        console.print(
            "[bold red]Error:[/bold red] MCP package not installed.\n"
            "Install with: pip install 'sciwriter[mcp]'"
        )
        sys.exit(1)


@mcp.command("config")
def mcp_config():
    """Show Claude Desktop configuration snippet.

    \b
    Outputs the JSON configuration needed for Claude Desktop
    to use the sciwriter MCP server.
    """
    import json
    import shutil

    # Find sciwriter executable
    sciwriter_path = shutil.which("sciwriter")
    if not sciwriter_path:
        sciwriter_path = "sciwriter"

    config = {
        "mcpServers": {
            "sciwriter": {
                "command": sciwriter_path,
                "args": ["mcp", "start"],
            }
        }
    }

    console.print("[bold]Claude Desktop Configuration[/bold]\n")
    console.print("Add this to your Claude Desktop config file:")
    console.print("[dim](~/.config/claude/claude_desktop_config.json on Linux)[/dim]\n")
    console.print(json.dumps(config, indent=2))
    console.print(
        "\n[dim]Or merge the 'sciwriter' entry into your existing mcpServers.[/dim]"
    )

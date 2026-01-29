"""MCP handlers for document inspection (outline, wordcount, figures, etc.).

All handlers delegate to CLI commands to maintain MCP->CLI->Python chain.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._utils import run_cli


async def get_outline_handler(arguments: dict[str, Any]) -> str:
    """Handle get_outline tool invocation via CLI.

    Args:
        arguments: Tool arguments containing:
            - project_dir: Path to project directory (required)
            - doc_type: Document type (manuscript/supplementary/revision)

    Returns:
        JSON string with document outline and word counts
    """
    project_dir = Path(arguments["project_dir"])
    doc_type = arguments.get("doc_type", "manuscript")

    if not project_dir.exists():
        return json.dumps(
            {"success": False, "error": f"Project directory not found: {project_dir}"}
        )

    cli_args = ["info", "outline", str(project_dir), "-t", doc_type, "--json"]
    success, stdout, stderr = run_cli(cli_args)

    if success and stdout.strip():
        try:
            data = json.loads(stdout)
            return json.dumps({"success": True, "outline": data})
        except json.JSONDecodeError:
            pass

    return json.dumps(
        {
            "success": success,
            "output": stdout,
            "error": stderr if not success else None,
        }
    )


async def wordcount_handler(arguments: dict[str, Any]) -> str:
    """Handle wordcount tool invocation via CLI.

    Args:
        arguments: Tool arguments containing:
            - project_dir: Path to project directory (required)
            - doc_type: Document type (manuscript/supplementary/revision)
            - section: Specific section to count (optional)

    Returns:
        JSON string with word count statistics
    """
    project_dir = Path(arguments["project_dir"])
    doc_type = arguments.get("doc_type", "manuscript")
    section = arguments.get("section")

    if not project_dir.exists():
        return json.dumps(
            {"success": False, "error": f"Project directory not found: {project_dir}"}
        )

    cli_args = ["info", "wordcount", str(project_dir), "-t", doc_type, "--json"]
    if section:
        cli_args.extend(["-s", section])

    success, stdout, stderr = run_cli(cli_args)

    if success and stdout.strip():
        try:
            data = json.loads(stdout)
            return json.dumps({"success": True, **data})
        except json.JSONDecodeError:
            pass

    return json.dumps(
        {
            "success": success,
            "output": stdout,
            "error": stderr if not success else None,
        }
    )


async def figures_handler(arguments: dict[str, Any]) -> str:
    """Handle figures tool invocation via CLI.

    Args:
        arguments: Tool arguments containing:
            - project_dir: Path to project directory (required)
            - doc_type: Document type (manuscript/supplementary/revision)

    Returns:
        JSON string with list of figures
    """
    project_dir = Path(arguments["project_dir"])
    doc_type = arguments.get("doc_type", "manuscript")

    if not project_dir.exists():
        return json.dumps(
            {"success": False, "error": f"Project directory not found: {project_dir}"}
        )

    cli_args = ["info", "figures", str(project_dir), "-t", doc_type, "--json"]
    success, stdout, stderr = run_cli(cli_args)

    if success and stdout.strip():
        try:
            data = json.loads(stdout)
            return json.dumps({"success": True, "figures": data})
        except json.JSONDecodeError:
            pass

    return json.dumps(
        {
            "success": success,
            "output": stdout,
            "error": stderr if not success else None,
        }
    )


async def tables_handler(arguments: dict[str, Any]) -> str:
    """Handle tables tool invocation via CLI.

    Args:
        arguments: Tool arguments containing:
            - project_dir: Path to project directory (required)
            - doc_type: Document type (manuscript/supplementary/revision)

    Returns:
        JSON string with list of tables
    """
    project_dir = Path(arguments["project_dir"])
    doc_type = arguments.get("doc_type", "manuscript")

    if not project_dir.exists():
        return json.dumps(
            {"success": False, "error": f"Project directory not found: {project_dir}"}
        )

    cli_args = ["info", "tables", str(project_dir), "-t", doc_type, "--json"]
    success, stdout, stderr = run_cli(cli_args)

    if success and stdout.strip():
        try:
            data = json.loads(stdout)
            return json.dumps({"success": True, "tables": data})
        except json.JSONDecodeError:
            pass

    return json.dumps(
        {
            "success": success,
            "output": stdout,
            "error": stderr if not success else None,
        }
    )


async def refs_handler(arguments: dict[str, Any]) -> str:
    """Handle refs tool invocation via CLI.

    Args:
        arguments: Tool arguments containing:
            - project_dir: Path to project directory (required)
            - doc_type: Document type (manuscript/supplementary/revision)
            - ref_type: Filter by reference type (optional)

    Returns:
        JSON string with list of references
    """
    project_dir = Path(arguments["project_dir"])
    doc_type = arguments.get("doc_type", "manuscript")
    ref_type = arguments.get("ref_type")

    if not project_dir.exists():
        return json.dumps(
            {"success": False, "error": f"Project directory not found: {project_dir}"}
        )

    cli_args = ["info", "refs", str(project_dir), "-t", doc_type, "--json"]
    if ref_type:
        cli_args.extend(["--type", ref_type])

    success, stdout, stderr = run_cli(cli_args)

    if success and stdout.strip():
        try:
            data = json.loads(stdout)
            return json.dumps({"success": True, "references": data})
        except json.JSONDecodeError:
            pass

    return json.dumps(
        {
            "success": success,
            "output": stdout,
            "error": stderr if not success else None,
        }
    )


__all__ = [
    "get_outline_handler",
    "wordcount_handler",
    "figures_handler",
    "tables_handler",
    "refs_handler",
]

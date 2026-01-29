"""MCP handlers for validation and history operations.

All handlers delegate to CLI commands to maintain MCP->CLI->Python chain.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._utils import run_cli


async def validate_handler(arguments: dict[str, Any]) -> str:
    """Handle validate tool invocation via CLI.

    Args:
        arguments: Tool arguments containing:
            - project_dir: Path to project directory (required)
            - doc_type: Document type (manuscript/supplementary/revision)

    Returns:
        JSON string with validation results
    """
    project_dir = Path(arguments["project_dir"])
    doc_type = arguments.get("doc_type", "manuscript")

    if not project_dir.exists():
        return json.dumps(
            {"success": False, "error": f"Project directory not found: {project_dir}"}
        )

    cli_args = ["validate", str(project_dir), "-t", doc_type, "--json"]
    success, stdout, stderr = run_cli(cli_args)

    if stdout.strip():
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


async def list_versions_handler(arguments: dict[str, Any]) -> str:
    """Handle list_versions tool invocation via CLI.

    Lists git commits that modified the document.

    Args:
        arguments: Tool arguments containing:
            - project_dir: Path to project directory (required)
            - doc_type: Document type (manuscript/supplementary/revision)
            - limit: Maximum number of versions to return (default: 20)

    Returns:
        JSON string with list of document versions (git commits)
    """
    project_dir = Path(arguments["project_dir"])
    doc_type = arguments.get("doc_type", "manuscript")
    limit = arguments.get("limit", 20)

    if not project_dir.exists():
        return json.dumps(
            {"success": False, "error": f"Project directory not found: {project_dir}"}
        )

    cli_args = [
        "versions",  # CLI still uses 'versions' command
        str(project_dir),
        "-t",
        doc_type,
        "-n",
        str(limit),
        "--json",
    ]
    success, stdout, stderr = run_cli(cli_args)

    if success and stdout.strip():
        try:
            data = json.loads(stdout)
            return json.dumps({"success": True, "versions": data})
        except json.JSONDecodeError:
            pass

    return json.dumps(
        {
            "success": success,
            "output": stdout,
            "error": stderr if not success else None,
        }
    )


async def get_diff_handler(arguments: dict[str, Any]) -> str:
    """Handle get_diff tool invocation via CLI.

    Compares document content between git commits.

    Args:
        arguments: Tool arguments containing:
            - project_dir: Path to project directory (required)
            - doc_type: Document type (manuscript/supplementary/revision)
            - commit1: First commit (git ref, default: HEAD~1)
            - commit2: Second commit (git ref, default: HEAD)

    Returns:
        JSON string with diff content
    """
    project_dir = Path(arguments["project_dir"])
    doc_type = arguments.get("doc_type", "manuscript")
    commit1 = arguments.get("commit1")
    commit2 = arguments.get("commit2")

    if not project_dir.exists():
        return json.dumps(
            {"success": False, "error": f"Project directory not found: {project_dir}"}
        )

    # Build CLI args: diff PROJECT [COMMIT1] [COMMIT2] -t DOC_TYPE
    cli_args = ["diff", str(project_dir)]
    if commit1:
        cli_args.append(commit1)
    if commit2:
        cli_args.append(commit2)
    cli_args.extend(["-t", doc_type])

    success, stdout, stderr = run_cli(cli_args)

    return json.dumps(
        {
            "success": success,
            "diff": stdout if success else None,
            "error": stderr if not success else None,
        }
    )


__all__ = ["validate_handler", "list_versions_handler", "get_diff_handler"]

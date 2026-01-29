"""MCP handler for version tool (git history).

Actions: list, diff
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._utils import run_cli


async def version_handler(arguments: dict[str, Any]) -> str:
    """Handle version tool invocation with action dispatch.

    Args:
        arguments: Tool arguments containing:
            - project: Project path or registered name (required)
            - action: Action to perform (required)
            - doc_type: Document type (default: manuscript)
            - limit: Max versions for list (default: 10)
            - commit1: First commit for diff (default: HEAD~1)
            - commit2: Second commit for diff (default: HEAD)

    Returns:
        JSON string with action results
    """
    action = arguments.get("action")
    project = arguments.get("project")
    doc_type = arguments.get("doc_type", "manuscript")

    if not action:
        return json.dumps({"success": False, "error": "Missing required: action"})
    if not project:
        return json.dumps({"success": False, "error": "Missing required: project"})

    project_path = Path(project)
    if not project_path.exists():
        return json.dumps({"success": False, "error": f"Project not found: {project}"})

    if action == "list":
        limit = arguments.get("limit", 10)
        return await _list_versions(project, doc_type, limit)
    elif action == "diff":
        commit1 = arguments.get("commit1", "HEAD~1")
        commit2 = arguments.get("commit2", "HEAD")
        return await _get_diff(project, doc_type, commit1, commit2)
    else:
        return json.dumps({"success": False, "error": f"Unknown action: {action}"})


async def _list_versions(project: str, doc_type: str, limit: int) -> str:
    """List document versions (git history)."""
    cli_args = ["version", "list", project, "-t", doc_type, "-n", str(limit), "--json"]
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


async def _get_diff(project: str, doc_type: str, commit1: str, commit2: str) -> str:
    """Get diff between versions."""
    cli_args = ["version", "diff", project, commit1, commit2, "-t", doc_type]
    success, stdout, stderr = run_cli(cli_args)

    return json.dumps(
        {
            "success": success,
            "diff": stdout if success else None,
            "error": stderr if not success else None,
        }
    )


__all__ = ["version_handler"]

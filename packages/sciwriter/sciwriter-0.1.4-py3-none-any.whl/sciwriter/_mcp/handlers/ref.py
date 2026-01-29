"""MCP handler for ref tool (references and labels).

Actions: list, labels
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._utils import run_cli


async def ref_handler(arguments: dict[str, Any]) -> str:
    """Handle ref tool invocation with action dispatch.

    Args:
        arguments: Tool arguments containing:
            - project: Project path or registered name (required)
            - action: Action to perform (required)
            - doc_type: Document type (default: manuscript)
            - ref_type: Filter by reference type (for list action)

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
        ref_type = arguments.get("ref_type")
        return await _list_refs(project, doc_type, ref_type)
    elif action == "labels":
        return await _list_labels(project, doc_type)
    else:
        return json.dumps({"success": False, "error": f"Unknown action: {action}"})


async def _list_refs(project: str, doc_type: str, ref_type: str | None) -> str:
    """List references in the document."""
    cli_args = ["ref", "list", project, "-t", doc_type, "--json"]
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


async def _list_labels(project: str, doc_type: str) -> str:
    """List labels in the document."""
    cli_args = ["ref", "labels", project, "-t", doc_type, "--json"]
    success, stdout, stderr = run_cli(cli_args)

    if success and stdout.strip():
        try:
            data = json.loads(stdout)
            return json.dumps({"success": True, "labels": data})
        except json.JSONDecodeError:
            pass

    return json.dumps(
        {
            "success": success,
            "output": stdout,
            "error": stderr if not success else None,
        }
    )


__all__ = ["ref_handler"]

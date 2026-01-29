"""MCP handler for doc tool (document analysis).

Actions: get_outline, count_words, validate
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._utils import run_cli


async def doc_handler(arguments: dict[str, Any]) -> str:
    """Handle doc tool invocation with action dispatch.

    Args:
        arguments: Tool arguments containing:
            - project: Project path or registered name (required)
            - action: Action to perform (required)
            - doc_type: Document type (default: manuscript)
            - section: Section name (for count_words)

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

    if action == "get_outline":
        return await _get_outline(project, doc_type)
    elif action == "count_words":
        section = arguments.get("section")
        return await _count_words(project, doc_type, section)
    elif action == "validate":
        return await _validate(project, doc_type)
    else:
        return json.dumps({"success": False, "error": f"Unknown action: {action}"})


async def _get_outline(project: str, doc_type: str) -> str:
    """Get document outline with word counts."""
    cli_args = ["outline", project, "-t", doc_type, "--json"]
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


async def _count_words(project: str, doc_type: str, section: str | None) -> str:
    """Get word count statistics."""
    cli_args = ["info", "wordcount", project, "-t", doc_type, "--json"]
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


async def _validate(project: str, doc_type: str) -> str:
    """Validate document for issues."""
    cli_args = ["validate", project, "-t", doc_type, "--json"]
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


__all__ = ["doc_handler"]

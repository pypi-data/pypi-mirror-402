"""MCP handlers for project management operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._utils import run_cli


async def status_handler(arguments: dict[str, Any]) -> str:
    """Handle status tool invocation via CLI.

    Args:
        arguments: Tool arguments containing:
            - project_dir: Path to project directory (required)

    Returns:
        JSON string with project status
    """
    project_dir = Path(arguments["project_dir"])

    if not project_dir.exists():
        return json.dumps(
            {
                "success": False,
                "error": f"Project directory not found: {project_dir}",
            }
        )

    cli_args = ["status", str(project_dir)]
    success, stdout, stderr = run_cli(cli_args)

    return json.dumps(
        {
            "success": success,
            "output": stdout,
            "error": stderr if not success else None,
            "project_dir": str(project_dir),
        }
    )


async def clean_handler(arguments: dict[str, Any]) -> str:
    """Handle clean tool invocation via CLI.

    Args:
        arguments: Tool arguments containing:
            - project_dir: Path to project directory (required)

    Returns:
        JSON string with clean result
    """
    project_dir = Path(arguments["project_dir"])

    if not project_dir.exists():
        return json.dumps(
            {
                "success": False,
                "error": f"Project directory not found: {project_dir}",
            }
        )

    cli_args = ["clean", str(project_dir)]
    success, stdout, stderr = run_cli(cli_args)

    return json.dumps(
        {
            "success": success,
            "output": stdout,
            "error": stderr if not success else None,
            "project_dir": str(project_dir),
        }
    )


async def get_project_info_handler(arguments: dict[str, Any]) -> str:
    """Handle get_project_info tool invocation.

    This uses the status command output for project info.

    Args:
        arguments: Tool arguments containing:
            - project_dir: Path to project directory (required)

    Returns:
        JSON string with project information
    """
    # Reuse status handler as it provides project info
    return await status_handler(arguments)


__all__ = ["status_handler", "clean_handler", "get_project_info_handler"]

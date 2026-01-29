"""Figure CRUD handler for MCP."""

from __future__ import annotations

import json
from typing import Any

from ._utils import resolve_project


def _error_response(error: str, suggestion: str = None) -> str:
    """Create error response."""
    resp = {"success": False, "error": error}
    if suggestion:
        resp["suggestion"] = suggestion
    return json.dumps(resp)


async def figure_handler(arguments: dict[str, Any]) -> str:
    """Handle figure CRUD operations.

    Actions:
        - list: List all figures
        - read: Get figure details
        - create: Create a new figure (with optional image_path symlink)
        - update: Update figure caption
        - delete: Delete a figure
    """
    from sciwriter._media.figures import (
        create_figure,
        delete_figure,
        get_figure,
        list_figures,
        update_figure,
    )

    project = resolve_project(arguments["project"])
    if not project:
        return _error_response(
            f"Project not found: {arguments['project']}",
            "Provide a valid project path or registered name",
        )

    action = arguments["action"]
    doc_type = arguments.get("doc_type", "manuscript")

    if action == "list":
        figures = list_figures(project, doc_type)
        return json.dumps(
            {
                "success": True,
                "figures": figures,
                "count": len(figures),
                "project": str(project),
                "doc_type": doc_type,
            }
        )

    elif action == "read":
        figure_id = arguments.get("figure_id")
        if not figure_id:
            return _error_response("figure_id required for read action")

        figure = get_figure(project, figure_id, doc_type)
        if figure:
            return json.dumps(
                {"success": True, "figure": figure, "project": str(project)}
            )
        return _error_response(f"Figure not found: {figure_id}")

    elif action == "create":
        figure_id = arguments.get("figure_id")
        caption = arguments.get("caption")
        image_path = arguments.get("image_path")
        if not figure_id or not caption:
            return _error_response("figure_id and caption required for create action")

        result = create_figure(project, figure_id, caption, doc_type, image_path)
        success = result is not None
        resp = {
            "success": success,
            "message": f"Created figure: {figure_id}"
            if success
            else f"Failed to create: {figure_id}",
            "figure_id": figure_id,
            "project": str(project),
        }
        if image_path:
            resp["image_path"] = image_path
            resp["symlinked"] = success
        return json.dumps(resp)

    elif action == "update":
        figure_id = arguments.get("figure_id")
        caption = arguments.get("caption")
        if not figure_id or not caption:
            return _error_response("figure_id and caption required for update action")

        success = update_figure(project, figure_id, caption, doc_type)
        return json.dumps(
            {
                "success": success,
                "message": f"Updated figure: {figure_id}"
                if success
                else f"Failed to update: {figure_id}",
                "figure_id": figure_id,
                "project": str(project),
            }
        )

    elif action == "delete":
        figure_id = arguments.get("figure_id")
        if not figure_id:
            return _error_response("figure_id required for delete action")

        success = delete_figure(project, figure_id, doc_type)
        return json.dumps(
            {
                "success": success,
                "message": f"Deleted figure: {figure_id}"
                if success
                else f"Failed to delete: {figure_id}",
                "figure_id": figure_id,
                "project": str(project),
            }
        )

    return _error_response(f"Unknown action: {action}")


__all__ = ["figure_handler"]

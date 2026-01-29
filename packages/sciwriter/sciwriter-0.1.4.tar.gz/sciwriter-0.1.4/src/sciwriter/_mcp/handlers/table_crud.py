"""Table CRUD handler for MCP."""

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


async def table_handler(arguments: dict[str, Any]) -> str:
    """Handle table CRUD operations.

    Actions:
        - list: List all tables
        - read: Get table details
        - create: Create a new table (with optional csv_path symlink)
        - update: Update table caption
        - delete: Delete a table
    """
    from sciwriter._media.tables import (
        create_table,
        delete_table,
        get_table,
        list_tables,
        update_table,
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
        tables = list_tables(project, doc_type)
        return json.dumps(
            {
                "success": True,
                "tables": tables,
                "count": len(tables),
                "project": str(project),
                "doc_type": doc_type,
            }
        )

    elif action == "read":
        table_id = arguments.get("table_id")
        if not table_id:
            return _error_response("table_id required for read action")

        table = get_table(project, table_id, doc_type)
        if table:
            return json.dumps(
                {"success": True, "table": table, "project": str(project)}
            )
        return _error_response(f"Table not found: {table_id}")

    elif action == "create":
        table_id = arguments.get("table_id")
        caption = arguments.get("caption")
        csv_path = arguments.get("csv_path")
        if not table_id or not caption:
            return _error_response("table_id and caption required for create action")

        result = create_table(project, table_id, caption, doc_type, csv_path)
        success = result is not None
        resp = {
            "success": success,
            "message": f"Created table: {table_id}"
            if success
            else f"Failed to create: {table_id}",
            "table_id": table_id,
            "project": str(project),
        }
        if csv_path:
            resp["csv_path"] = csv_path
            resp["symlinked"] = success
        return json.dumps(resp)

    elif action == "update":
        table_id = arguments.get("table_id")
        caption = arguments.get("caption")
        if not table_id or not caption:
            return _error_response("table_id and caption required for update action")

        success = update_table(project, table_id, caption, doc_type)
        return json.dumps(
            {
                "success": success,
                "message": f"Updated table: {table_id}"
                if success
                else f"Failed to update: {table_id}",
                "table_id": table_id,
                "project": str(project),
            }
        )

    elif action == "delete":
        table_id = arguments.get("table_id")
        if not table_id:
            return _error_response("table_id required for delete action")

        success = delete_table(project, table_id, doc_type)
        return json.dumps(
            {
                "success": success,
                "message": f"Deleted table: {table_id}"
                if success
                else f"Failed to delete: {table_id}",
                "table_id": table_id,
                "project": str(project),
            }
        )

    return _error_response(f"Unknown action: {action}")


__all__ = ["table_handler"]

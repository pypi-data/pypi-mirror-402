"""Citation CRUD handler for MCP."""

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


async def citation_handler(arguments: dict[str, Any]) -> str:
    """Handle citation CRUD operations.

    Actions:
        - list: List all citations
        - read: Get citation details
        - create: Create a new citation (BibTeX entry)
        - update: Update citation fields
        - delete: Delete a citation
    """
    from sciwriter._media.citations import (
        create_citation,
        delete_citation,
        get_citation,
        list_citations,
        update_citation,
    )

    project = resolve_project(arguments["project"])
    if not project:
        return _error_response(
            f"Project not found: {arguments['project']}",
            "Provide a valid project path or registered name",
        )

    action = arguments["action"]

    if action == "list":
        citations = list_citations(project)
        return json.dumps(
            {
                "success": True,
                "citations": citations,
                "count": len(citations),
                "project": str(project),
            }
        )

    elif action == "read":
        key = arguments.get("key")
        if not key:
            return _error_response("key required for read action")

        citation = get_citation(project, key)
        if citation:
            return json.dumps(
                {"success": True, "citation": citation, "project": str(project)}
            )
        return _error_response(f"Citation not found: {key}")

    elif action == "create":
        key = arguments.get("key")
        entry_type = arguments.get("entry_type")
        author = arguments.get("author")
        title = arguments.get("title")
        year = arguments.get("year")

        if not all([key, entry_type, author, title, year]):
            return _error_response(
                "key, entry_type, author, title, year required for create action"
            )

        fields = {
            "author": author,
            "title": title,
            "year": year,
        }
        # Add optional fields
        for field in [
            "journal",
            "booktitle",
            "volume",
            "number",
            "pages",
            "doi",
            "url",
        ]:
            if arguments.get(field):
                fields[field] = arguments[field]

        success = create_citation(project, key, entry_type, fields)
        return json.dumps(
            {
                "success": success,
                "message": f"Created citation: {key}"
                if success
                else f"Failed to create: {key}",
                "key": key,
                "project": str(project),
            }
        )

    elif action == "update":
        key = arguments.get("key")
        if not key:
            return _error_response("key required for update action")

        fields = {}
        for field in [
            "author",
            "title",
            "year",
            "journal",
            "volume",
            "number",
            "pages",
            "doi",
            "url",
        ]:
            if arguments.get(field):
                fields[field] = arguments[field]

        if not fields:
            return _error_response("At least one field required for update action")

        success = update_citation(project, key, fields)
        return json.dumps(
            {
                "success": success,
                "message": f"Updated citation: {key}"
                if success
                else f"Failed to update: {key}",
                "key": key,
                "updated_fields": list(fields.keys()),
                "project": str(project),
            }
        )

    elif action == "delete":
        key = arguments.get("key")
        if not key:
            return _error_response("key required for delete action")

        success = delete_citation(project, key)
        return json.dumps(
            {
                "success": success,
                "message": f"Deleted citation: {key}"
                if success
                else f"Failed to delete: {key}",
                "key": key,
                "project": str(project),
            }
        )

    return _error_response(f"Unknown action: {action}")


__all__ = ["citation_handler"]

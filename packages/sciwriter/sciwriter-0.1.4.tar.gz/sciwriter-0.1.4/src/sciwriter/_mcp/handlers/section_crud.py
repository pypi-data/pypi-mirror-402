"""Section CRUD handler for MCP."""

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


async def section_handler(arguments: dict[str, Any]) -> str:
    """Handle section CRUD operations.

    Actions:
        - list: List available sections
        - read: Read section content
        - create: Create a new section
        - update: Update section content
        - delete: Delete a section
    """
    from sciwriter._content import (
        create_section,
        delete_section,
        list_sections,
        read_section,
        update_section,
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
        sections = list_sections(project, doc_type)
        return json.dumps(
            {
                "success": True,
                "sections": sections,
                "count": len(sections),
                "project": str(project),
                "doc_type": doc_type,
            }
        )

    elif action == "read":
        sections = arguments.get("sections") or [arguments.get("section")]
        if not sections or sections == [None]:
            return _error_response("Section name required for read action")

        results = {}
        for name in sections:
            section = read_section(project, name, doc_type)
            if section:
                results[name] = {
                    "content": section.content,
                    "file_path": str(section.file_path),
                    "word_count": len(section.content.split()),
                }
            else:
                results[name] = {"content": None, "error": f"Not found: {name}"}

        return json.dumps(
            {
                "success": all("error" not in v for v in results.values()),
                "sections": results,
                "project": str(project),
                "doc_type": doc_type,
            }
        )

    elif action == "create":
        section = arguments.get("section")
        content = arguments.get("content", "")
        if not section:
            return _error_response("Section name required for create action")

        success = create_section(project, section, content, doc_type)
        return json.dumps(
            {
                "success": success,
                "message": f"Created section: {section}"
                if success
                else f"Failed to create: {section}",
                "section": section,
                "project": str(project),
                "doc_type": doc_type,
            }
        )

    elif action == "update":
        section = arguments.get("section")
        content = arguments.get("content")
        if not section or content is None:
            return _error_response(
                "Section name and content required for update action"
            )

        prev = read_section(project, section, doc_type)
        prev_count = len(prev.content.split()) if prev else 0

        success = update_section(project, section, content, doc_type)
        new_count = len(content.split())

        return json.dumps(
            {
                "success": success,
                "message": f"Updated section: {section}"
                if success
                else f"Failed to update: {section}",
                "section": section,
                "project": str(project),
                "doc_type": doc_type,
                "word_count": {
                    "previous": prev_count,
                    "new": new_count,
                    "change": new_count - prev_count,
                },
            }
        )

    elif action == "delete":
        section = arguments.get("section")
        if not section:
            return _error_response("Section name required for delete action")

        success = delete_section(project, section, doc_type)
        return json.dumps(
            {
                "success": success,
                "message": f"Deleted section: {section}"
                if success
                else f"Failed to delete: {section}",
                "section": section,
                "project": str(project),
                "doc_type": doc_type,
            }
        )

    return _error_response(f"Unknown action: {action}")


__all__ = ["section_handler"]

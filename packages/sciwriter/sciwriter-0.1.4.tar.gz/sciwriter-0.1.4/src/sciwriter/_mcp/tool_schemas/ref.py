"""MCP Tool schemas for reference/label management."""

from __future__ import annotations

import mcp.types as types


def get_ref_schemas() -> list[types.Tool]:
    """Return list of reference management MCP tools."""
    return [
        types.Tool(
            name="ref",
            description=(
                "Reference and label management. Actions: list (find \\ref{} and \\cite{}), "
                "labels (find \\label{} definitions)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {
                        "type": "string",
                        "description": "Project path or registered name",
                    },
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": ["list", "labels"],
                    },
                    "doc_type": {
                        "type": "string",
                        "description": "Document type",
                        "enum": ["manuscript", "supplementary", "revision"],
                        "default": "manuscript",
                    },
                    "ref_type": {
                        "type": "string",
                        "description": "Filter by reference type (for list action)",
                        "enum": ["figure", "table", "section", "equation", "citation"],
                    },
                },
                "required": ["project", "action"],
            },
        ),
    ]

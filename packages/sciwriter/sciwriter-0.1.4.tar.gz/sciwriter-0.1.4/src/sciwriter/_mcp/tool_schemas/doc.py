"""MCP Tool schemas for document analysis operations."""

from __future__ import annotations

import mcp.types as types


def get_doc_schemas() -> list[types.Tool]:
    """Return list of document analysis MCP tools."""
    return [
        types.Tool(
            name="doc",
            description=(
                "Document analysis. Actions: get_outline (structure with word counts), "
                "count_words (word/char statistics), validate (check for issues)."
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
                        "enum": ["get_outline", "count_words", "validate"],
                    },
                    "doc_type": {
                        "type": "string",
                        "description": "Document type",
                        "enum": ["manuscript", "supplementary", "revision"],
                        "default": "manuscript",
                    },
                    "section": {
                        "type": "string",
                        "description": "Section name (for count_words action)",
                    },
                },
                "required": ["project", "action"],
            },
        ),
    ]

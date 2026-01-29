"""MCP Tool schemas for version/history management."""

from __future__ import annotations

import mcp.types as types


def get_version_schemas() -> list[types.Tool]:
    """Return list of version management MCP tools."""
    return [
        types.Tool(
            name="version",
            description=(
                "Document version history. Actions: list (show git history), "
                "diff (compare versions)."
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
                        "enum": ["list", "diff"],
                    },
                    "doc_type": {
                        "type": "string",
                        "description": "Document type",
                        "enum": ["manuscript", "supplementary", "revision"],
                        "default": "manuscript",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum versions to return (for list)",
                        "default": 10,
                    },
                    "commit1": {
                        "type": "string",
                        "description": "First commit (for diff)",
                        "default": "HEAD~1",
                    },
                    "commit2": {
                        "type": "string",
                        "description": "Second commit (for diff)",
                        "default": "HEAD",
                    },
                },
                "required": ["project", "action"],
            },
        ),
    ]

"""MCP Tool schemas for project management operations."""

from __future__ import annotations

import mcp.types as types


def get_project_schemas() -> list[types.Tool]:
    """Return list of project management MCP tools."""
    return [
        types.Tool(
            name="status",
            description="Show project status and check dependencies",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {
                        "type": "string",
                        "description": "Path to the project directory",
                    },
                },
                "required": ["project_dir"],
            },
        ),
        types.Tool(
            name="clean",
            description="Clean compilation artifacts from a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {
                        "type": "string",
                        "description": "Path to the project directory",
                    },
                },
                "required": ["project_dir"],
            },
        ),
        types.Tool(
            name="get_project_info",
            description="Get detailed information about a sciwriter project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {
                        "type": "string",
                        "description": "Path to the project directory",
                    },
                },
                "required": ["project_dir"],
            },
        ),
    ]

"""MCP Tool schemas for background job management."""

from __future__ import annotations

import mcp.types as types


def get_jobs_schemas() -> list[types.Tool]:
    """Return list of job management MCP tools."""
    return [
        types.Tool(
            name="compile_async",
            description=(
                "Start compilation as a background job. Returns immediately with a "
                "job_id. Use job tool to check progress and get results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {
                        "type": "string",
                        "description": "Path to the project directory",
                    },
                    "doc_type": {
                        "type": "string",
                        "description": "Type of document to compile",
                        "enum": ["manuscript", "supplementary", "revision", "all"],
                        "default": "manuscript",
                    },
                    "quiet": {
                        "type": "boolean",
                        "description": "Suppress output",
                        "default": True,
                    },
                    "no_diff": {
                        "type": "boolean",
                        "description": "Skip diff generation",
                        "default": False,
                    },
                    "no_figs": {
                        "type": "boolean",
                        "description": "Skip figure processing",
                        "default": False,
                    },
                    "draft": {
                        "type": "boolean",
                        "description": "Single-pass compilation (faster)",
                        "default": False,
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum compilation time in seconds",
                        "default": 300,
                    },
                },
                "required": ["project_dir"],
            },
        ),
        types.Tool(
            name="job",
            description=(
                "Manage background jobs. Actions: list (show all jobs), "
                "read (check status), cancel (stop running job), clear (remove finished)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": ["list", "read", "cancel", "clear"],
                    },
                    "job_id": {
                        "type": "string",
                        "description": "Job ID (required for read/cancel)",
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by status (for list action)",
                        "enum": [
                            "pending",
                            "running",
                            "completed",
                            "failed",
                            "cancelled",
                        ],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of jobs to return (for list)",
                        "default": 20,
                    },
                },
                "required": ["action"],
            },
        ),
    ]

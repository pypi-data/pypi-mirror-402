"""MCP Tool schemas for compilation operations."""

from __future__ import annotations

import mcp.types as types


def get_compile_schemas() -> list[types.Tool]:
    """Return list of compilation-related MCP tools."""
    return [
        types.Tool(
            name="compile",
            description="Compile LaTeX documents (manuscript, supplementary, or revision)",
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
                        "default": False,
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "Show detailed output",
                        "default": False,
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
                    "no_tables": {
                        "type": "boolean",
                        "description": "Skip table processing",
                        "default": False,
                    },
                    "draft": {
                        "type": "boolean",
                        "description": "Single-pass compilation (faster)",
                        "default": False,
                    },
                    "dark_mode": {
                        "type": "boolean",
                        "description": "Compile with dark theme",
                        "default": False,
                    },
                    "crop_tif": {
                        "type": "boolean",
                        "description": "Crop TIF images before compilation",
                        "default": False,
                    },
                    "engine": {
                        "type": "string",
                        "description": "Compilation engine",
                        "enum": ["auto", "tectonic", "latexmk", "3pass"],
                        "default": "auto",
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
    ]

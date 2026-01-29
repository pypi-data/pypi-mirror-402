"""MCP Tool schemas for sciwriter.

Defines available tools for LaTeX manuscript management.
"""

from __future__ import annotations

import mcp.types as types

from .compile import get_compile_schemas
from .crud import get_crud_schemas
from .doc import get_doc_schemas
from .jobs import get_jobs_schemas
from .project import get_project_schemas
from .ref import get_ref_schemas
from .version import get_version_schemas


def get_tool_schemas() -> list[types.Tool]:
    """Return list of all available MCP tools for sciwriter."""
    return [
        *get_compile_schemas(),
        *get_project_schemas(),
        *get_crud_schemas(),
        *get_jobs_schemas(),
        *get_doc_schemas(),
        *get_ref_schemas(),
        *get_version_schemas(),
    ]


__all__ = ["get_tool_schemas"]

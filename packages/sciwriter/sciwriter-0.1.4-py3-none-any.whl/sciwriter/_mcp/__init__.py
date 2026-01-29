"""MCP server components for sciwriter."""

from .handlers import (
    citation_handler,
    clean_handler,
    compile_async_handler,
    compile_handler,
    doc_handler,
    figure_handler,
    get_project_info_handler,
    job_handler,
    ref_handler,
    section_handler,
    status_handler,
    table_handler,
    version_handler,
)
from .tool_schemas import get_tool_schemas

__all__ = [
    "get_tool_schemas",
    # Project Management
    "status_handler",
    "clean_handler",
    "get_project_info_handler",
    # Compilation
    "compile_handler",
    "compile_async_handler",
    # Jobs (action-based)
    "job_handler",
    # Content CRUD (action-based)
    "section_handler",
    "figure_handler",
    "table_handler",
    "citation_handler",
    # Document analysis (action-based)
    "doc_handler",
    "ref_handler",
    "version_handler",
]

"""MCP handlers for sciwriter tools.

Each handler delegates to core modules to maintain consistent behavior.
"""

# Project management
# Compilation
from .compile import compile_handler

# Content CRUD (action-based)
from .crud import (
    citation_handler,
    figure_handler,
    section_handler,
    table_handler,
)

# Document analysis (action-based)
from .doc import doc_handler
from .jobs import compile_async_handler, job_handler
from .project import clean_handler, get_project_info_handler, status_handler
from .ref import ref_handler
from .version import version_handler

__all__ = [
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

"""
sciwriter: LaTeX manuscript compilation system for scientific documents.

Provides both OOP and functional APIs for managing scientific manuscripts.

OOP API (recommended):
    writer = sciwriter.Writer("./my-paper")
    writer.list_sections()
    writer.read_section("abstract")
    writer.compile_manuscript()
    writer.word_count()

Functional API:
    sciwriter.init_project("my-paper")
    sciwriter.list_projects()
    sciwriter.check_dependencies()
"""

from importlib.metadata import PackageNotFoundError, version

# =============================================================================
# Compilation Utilities (module-level)
# =============================================================================
from sciwriter._compiler import check_dependencies

# =============================================================================
# Project Management (module-level, no project instance needed)
# =============================================================================
from sciwriter._project import (
    get_active_project_dir,
    get_project_path,
    init_project,
    list_projects,
    resolve_project,
    unregister_project,
)

# =============================================================================
# Main Class (OOP Interface)
# =============================================================================
from sciwriter._writer import Writer

try:
    __version__ = version("sciwriter")
except PackageNotFoundError:
    __version__ = "0.0.0.dev"

__all__ = [
    # Version
    "__version__",
    # Main Class
    "Writer",
    # Project Management
    "init_project",
    "list_projects",
    "get_active_project_dir",
    "unregister_project",
    "get_project_path",
    "resolve_project",
    # Utilities
    "check_dependencies",
]

"""Unified CRUD handlers for sections, figures, tables, and citations.

Re-exports handlers from separate modules for backwards compatibility.
"""

from __future__ import annotations

from .citation_crud import citation_handler
from .figure_crud import figure_handler
from .section_crud import section_handler
from .table_crud import table_handler

__all__ = [
    "section_handler",
    "figure_handler",
    "table_handler",
    "citation_handler",
]

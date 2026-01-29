"""Media management for sciwriter LaTeX documents.

Provides CRUD operations for figures, tables, and citations:
- List, get, create, update, delete figures
- List, get, create, update, delete tables
- List, get, create, update, delete citations
- Find references and labels in documents
"""

from __future__ import annotations

from ._utils import DOC_DIRS, parse_caption_file
from .citations import (
    CitationInfo,
    create_citation,
    delete_citation,
    get_citation,
    list_citations,
    update_citation,
)
from .figures import (
    FigureInfo,
    create_figure,
    delete_figure,
    get_figure,
    list_figures,
    update_figure,
)
from .references import Reference, find_labels, find_references
from .tables import (
    TableInfo,
    create_table,
    delete_table,
    get_table,
    list_tables,
    update_table,
)

__all__ = [
    # Utils
    "DOC_DIRS",
    "parse_caption_file",
    # Figures
    "FigureInfo",
    "list_figures",
    "get_figure",
    "create_figure",
    "update_figure",
    "delete_figure",
    # Tables
    "TableInfo",
    "list_tables",
    "get_table",
    "create_table",
    "update_table",
    "delete_table",
    # Citations
    "CitationInfo",
    "list_citations",
    "get_citation",
    "create_citation",
    "update_citation",
    "delete_citation",
    # References
    "Reference",
    "find_references",
    "find_labels",
]

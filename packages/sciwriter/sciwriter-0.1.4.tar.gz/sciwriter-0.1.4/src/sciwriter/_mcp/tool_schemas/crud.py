"""Unified CRUD tool schemas for sections, figures, tables, and citations.

Each content type uses a single tool with an 'action' parameter:
- list: List all items
- read: Get details of a specific item
- create: Create a new item
- update: Update an existing item
- delete: Delete an item
"""

from __future__ import annotations

import mcp.types as types

DOC_TYPE_ENUM = ["manuscript", "supplementary", "revision"]
ACTION_ENUM = ["list", "read", "create", "update", "delete"]
ENTRY_TYPE_ENUM = [
    "article",
    "book",
    "inproceedings",
    "incollection",
    "misc",
    "techreport",
    "phdthesis",
    "mastersthesis",
]


def get_crud_schemas() -> list[types.Tool]:
    """Return unified CRUD tool schemas."""
    return [
        # Section tool
        types.Tool(
            name="section",
            description=(
                "Manage manuscript sections (abstract, introduction, methods, etc.). "
                "Actions: list (show available), read (get content), create (new section), "
                "update (modify content), delete (remove optional sections like highlights)."
            ),
            inputSchema={
                "type": "object",
                "required": ["project", "action"],
                "properties": {
                    "project": {
                        "type": "string",
                        "description": "Project path or registered name",
                    },
                    "action": {
                        "type": "string",
                        "enum": ACTION_ENUM,
                        "description": "CRUD action to perform",
                    },
                    "section": {
                        "type": "string",
                        "description": "Section name (required for read/create/update/delete)",
                    },
                    "sections": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Multiple section names (for batch read)",
                    },
                    "content": {
                        "type": "string",
                        "description": "Section content (required for create/update)",
                    },
                    "doc_type": {
                        "type": "string",
                        "enum": DOC_TYPE_ENUM,
                        "default": "manuscript",
                        "description": "Document type",
                    },
                },
            },
        ),
        # Figure tool
        types.Tool(
            name="figure",
            description=(
                "Manage figures in the document. "
                "Actions: list (show all), read (get details), create (new figure), "
                "update (modify caption), delete (remove figure and media)."
            ),
            inputSchema={
                "type": "object",
                "required": ["project", "action"],
                "properties": {
                    "project": {
                        "type": "string",
                        "description": "Project path or registered name",
                    },
                    "action": {
                        "type": "string",
                        "enum": ACTION_ENUM,
                        "description": "CRUD action to perform",
                    },
                    "figure_id": {
                        "type": "string",
                        "description": "Figure ID, e.g., '01' or '01_example' (required for read/create/update/delete)",
                    },
                    "caption": {
                        "type": "string",
                        "description": "Figure caption (required for create, optional for update)",
                    },
                    "image_path": {
                        "type": "string",
                        "description": "Path to image file (PNG, PDF, TIF, etc.) to symlink for create",
                    },
                    "doc_type": {
                        "type": "string",
                        "enum": DOC_TYPE_ENUM,
                        "default": "manuscript",
                        "description": "Document type",
                    },
                },
            },
        ),
        # Table tool
        types.Tool(
            name="table",
            description=(
                "Manage tables in the document. "
                "Actions: list (show all), read (get details), create (new table), "
                "update (modify caption), delete (remove table and data)."
            ),
            inputSchema={
                "type": "object",
                "required": ["project", "action"],
                "properties": {
                    "project": {
                        "type": "string",
                        "description": "Project path or registered name",
                    },
                    "action": {
                        "type": "string",
                        "enum": ACTION_ENUM,
                        "description": "CRUD action to perform",
                    },
                    "table_id": {
                        "type": "string",
                        "description": "Table ID, e.g., '01' or '01_example' (required for read/create/update/delete)",
                    },
                    "caption": {
                        "type": "string",
                        "description": "Table caption (required for create, optional for update)",
                    },
                    "csv_path": {
                        "type": "string",
                        "description": "Path to CSV file with table data to symlink for create",
                    },
                    "doc_type": {
                        "type": "string",
                        "enum": DOC_TYPE_ENUM,
                        "default": "manuscript",
                        "description": "Document type",
                    },
                },
            },
        ),
        # Citation tool
        types.Tool(
            name="citation",
            description=(
                "Manage citations in bibliography.bib. "
                "Actions: list (show all), read (get entry), create (new citation), "
                "update (modify fields), delete (remove entry)."
            ),
            inputSchema={
                "type": "object",
                "required": ["project", "action"],
                "properties": {
                    "project": {
                        "type": "string",
                        "description": "Project path or registered name",
                    },
                    "action": {
                        "type": "string",
                        "enum": ACTION_ENUM,
                        "description": "CRUD action to perform",
                    },
                    "key": {
                        "type": "string",
                        "description": "Citation key, e.g., 'smith2024' (required for read/create/update/delete)",
                    },
                    "entry_type": {
                        "type": "string",
                        "enum": ENTRY_TYPE_ENUM,
                        "description": "BibTeX entry type (required for create)",
                    },
                    "author": {
                        "type": "string",
                        "description": "Author(s), e.g., 'Smith, John and Doe, Jane'",
                    },
                    "title": {
                        "type": "string",
                        "description": "Title of the work",
                    },
                    "year": {
                        "type": "string",
                        "description": "Publication year",
                    },
                    "journal": {
                        "type": "string",
                        "description": "Journal name",
                    },
                    "booktitle": {
                        "type": "string",
                        "description": "Book/proceedings title",
                    },
                    "volume": {
                        "type": "string",
                        "description": "Volume number",
                    },
                    "number": {
                        "type": "string",
                        "description": "Issue number",
                    },
                    "pages": {
                        "type": "string",
                        "description": "Page range, e.g., '1--10'",
                    },
                    "doi": {
                        "type": "string",
                        "description": "Digital Object Identifier",
                    },
                    "url": {
                        "type": "string",
                        "description": "URL",
                    },
                },
            },
        ),
    ]


__all__ = ["get_crud_schemas"]

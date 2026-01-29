"""Pydantic models for MCP handler input validation.

Provides type-safe, validated input models for all CRUD operations.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, Field, field_validator


class DocType(str, Enum):
    """Valid document types."""

    MANUSCRIPT = "manuscript"
    SUPPLEMENTARY = "supplementary"
    REVISION = "revision"


class EntryType(str, Enum):
    """Valid BibTeX entry types."""

    ARTICLE = "article"
    BOOK = "book"
    INPROCEEDINGS = "inproceedings"
    INCOLLECTION = "incollection"
    MISC = "misc"
    TECHREPORT = "techreport"
    PHDTHESIS = "phdthesis"
    MASTERSTHESIS = "mastersthesis"


# --- Base Models ---


class ProjectInput(BaseModel):
    """Base model with project path."""

    project: str = Field(default=".", description="Project path or registered name")


class MediaInput(ProjectInput):
    """Base model for media (figure/table) operations."""

    doc_type: DocType = Field(default=DocType.MANUSCRIPT, description="Document type")


# --- Figure Models ---


class FigureId(BaseModel):
    """Validated figure ID."""

    figure_id: Annotated[
        str,
        Field(
            description="Figure ID (e.g., '01' or '01_description')",
            min_length=2,
        ),
    ]

    @field_validator("figure_id")
    @classmethod
    def validate_figure_id(cls, v: str) -> str:
        """Validate figure ID format: 2 digits with optional _name."""
        if not re.match(r"^\d{2}(_[a-zA-Z0-9_]+)?$", v):
            raise ValueError(
                f"Invalid figure_id: '{v}'. "
                "Expected: '01' or '01_description' (2 digits, optional _name)"
            )
        return v


class FigureGetInput(MediaInput, FigureId):
    """Input for figure_get operation."""

    pass


class FigureCreateInput(MediaInput, FigureId):
    """Input for figure_create operation."""

    caption: Annotated[
        str,
        Field(description="Figure caption text", min_length=1),
    ]


class FigureUpdateInput(MediaInput, FigureId):
    """Input for figure_update operation."""

    caption: Annotated[
        str,
        Field(description="New caption text", min_length=1),
    ]


class FigureDeleteInput(MediaInput, FigureId):
    """Input for figure_delete operation."""

    pass


# --- Table Models ---


class TableId(BaseModel):
    """Validated table ID."""

    table_id: Annotated[
        str,
        Field(
            description="Table ID (e.g., '01' or '01_description')",
            min_length=2,
        ),
    ]

    @field_validator("table_id")
    @classmethod
    def validate_table_id(cls, v: str) -> str:
        """Validate table ID format: 2 digits with optional _name."""
        if not re.match(r"^\d{2}(_[a-zA-Z0-9_]+)?$", v):
            raise ValueError(
                f"Invalid table_id: '{v}'. "
                "Expected: '01' or '01_description' (2 digits, optional _name)"
            )
        return v


class TableGetInput(MediaInput, TableId):
    """Input for table_get operation."""

    pass


class TableCreateInput(MediaInput, TableId):
    """Input for table_create operation."""

    caption: Annotated[
        str,
        Field(description="Table caption text", min_length=1),
    ]


class TableUpdateInput(MediaInput, TableId):
    """Input for table_update operation."""

    caption: Annotated[
        str,
        Field(description="New caption text", min_length=1),
    ]


class TableDeleteInput(MediaInput, TableId):
    """Input for table_delete operation."""

    pass


# --- Citation Models ---


class CitationKey(BaseModel):
    """Validated citation key."""

    key: Annotated[
        str,
        Field(
            description="Citation key (e.g., 'smith2024')",
            min_length=1,
        ),
    ]

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        """Validate citation key: starts with letter, alphanumeric/underscore."""
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", v):
            raise ValueError(
                f"Invalid citation key: '{v}'. "
                "Expected: alphanumeric starting with letter (e.g., 'smith2024')"
            )
        return v


class CitationListInput(ProjectInput):
    """Input for citation_list operation."""

    pass


class CitationGetInput(ProjectInput, CitationKey):
    """Input for citation_get operation."""

    pass


class CitationCreateInput(ProjectInput, CitationKey):
    """Input for citation_create operation."""

    entry_type: EntryType = Field(default=EntryType.ARTICLE, description="BibTeX type")
    author: Annotated[
        str,
        Field(
            description="Author(s) (e.g., 'Smith, John and Doe, Jane')", min_length=1
        ),
    ]
    title: Annotated[
        str,
        Field(description="Title of the work", min_length=1),
    ]
    year: Annotated[
        str,
        Field(description="Publication year", min_length=4, max_length=4),
    ]

    # Optional fields
    journal: Optional[str] = Field(default=None, description="Journal name")
    booktitle: Optional[str] = Field(default=None, description="Book/proceedings title")
    volume: Optional[str] = Field(default=None, description="Volume number")
    number: Optional[str] = Field(default=None, description="Issue number")
    pages: Optional[str] = Field(default=None, description="Page range")
    doi: Optional[str] = Field(default=None, description="Digital Object Identifier")
    url: Optional[str] = Field(default=None, description="URL")

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: str) -> str:
        """Validate year is numeric."""
        if not v.isdigit():
            raise ValueError(f"Year must be numeric, got: '{v}'")
        return v


class CitationUpdateInput(ProjectInput, CitationKey):
    """Input for citation_update operation."""

    # All fields optional for update
    author: Optional[str] = Field(default=None, description="New author(s)")
    title: Optional[str] = Field(default=None, description="New title")
    year: Optional[str] = Field(default=None, description="New year")
    journal: Optional[str] = Field(default=None, description="New journal name")
    booktitle: Optional[str] = Field(default=None, description="New book title")
    volume: Optional[str] = Field(default=None, description="New volume")
    number: Optional[str] = Field(default=None, description="New issue number")
    pages: Optional[str] = Field(default=None, description="New page range")
    doi: Optional[str] = Field(default=None, description="New DOI")
    url: Optional[str] = Field(default=None, description="New URL")

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: Optional[str]) -> Optional[str]:
        """Validate year is numeric if provided."""
        if v is not None and not v.isdigit():
            raise ValueError(f"Year must be numeric, got: '{v}'")
        return v


class CitationDeleteInput(ProjectInput, CitationKey):
    """Input for citation_delete operation."""

    pass


__all__ = [
    # Enums
    "DocType",
    "EntryType",
    # Figure models
    "FigureGetInput",
    "FigureCreateInput",
    "FigureUpdateInput",
    "FigureDeleteInput",
    # Table models
    "TableGetInput",
    "TableCreateInput",
    "TableUpdateInput",
    "TableDeleteInput",
    # Citation models
    "CitationListInput",
    "CitationGetInput",
    "CitationCreateInput",
    "CitationUpdateInput",
    "CitationDeleteInput",
]

"""Citation management for sciwriter LaTeX documents.

Provides CRUD operations for BibTeX citations in bibliography.bib.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

PathLike = Union[str, Path]


@dataclass
class CitationInfo:
    """Information about a BibTeX citation entry."""

    key: str  # Citation key (e.g., "smith2024")
    entry_type: str  # BibTeX entry type (article, book, misc, etc.)
    title: str  # Title of the work
    author: str  # Author(s)
    year: str  # Publication year
    raw_entry: str  # Full raw BibTeX entry
    fields: dict  # All parsed fields


def _get_bib_path(project_dir: PathLike) -> Path:
    """Get path to bibliography.bib file."""
    return Path(project_dir) / "00_shared" / "bibliography.bib"


def _parse_bibtex_entry(entry_text: str) -> Optional[CitationInfo]:
    """Parse a single BibTeX entry into CitationInfo."""
    # Match entry type and key: @article{key,
    header_match = re.match(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", entry_text, re.IGNORECASE)
    if not header_match:
        return None

    entry_type = header_match.group(1).lower()
    key = header_match.group(2)

    # Parse fields
    fields = {}
    # Match field = {value} or field = "value" or field = value
    field_pattern = (
        r"(\w+)\s*=\s*(?:\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}|\"([^\"]*)\"|(\d+))"
    )
    for match in re.finditer(field_pattern, entry_text):
        field_name = match.group(1).lower()
        field_value = match.group(2) or match.group(3) or match.group(4)
        if field_value:
            fields[field_name] = field_value.strip()

    return CitationInfo(
        key=key,
        entry_type=entry_type,
        title=fields.get("title", ""),
        author=fields.get("author", ""),
        year=fields.get("year", ""),
        raw_entry=entry_text.strip(),
        fields=fields,
    )


def _parse_bibtex_file(content: str) -> list[CitationInfo]:
    """Parse all entries from BibTeX content."""
    citations = []

    # Split by @ followed by entry type, keeping the delimiter
    # Match complete entries between @type{...}
    entry_pattern = r"@\w+\s*\{[^@]*\}"
    entries = re.findall(entry_pattern, content, re.DOTALL)

    for entry_text in entries:
        citation = _parse_bibtex_entry(entry_text)
        if citation:
            citations.append(citation)

    return citations


def list_citations(project_dir: PathLike) -> list[CitationInfo]:
    """List all citations in the bibliography file.

    Args:
        project_dir: Path to the project directory

    Returns:
        List of CitationInfo objects
    """
    bib_path = _get_bib_path(project_dir)
    if not bib_path.exists():
        return []

    content = bib_path.read_text(encoding="utf-8")
    return _parse_bibtex_file(content)


def get_citation(project_dir: PathLike, key: str) -> Optional[CitationInfo]:
    """Get a specific citation by key.

    Args:
        project_dir: Path to the project directory
        key: Citation key to find

    Returns:
        CitationInfo if found, None otherwise
    """
    citations = list_citations(project_dir)
    for c in citations:
        if c.key == key:
            return c
    return None


def create_citation(
    project_dir: PathLike,
    key: str,
    entry_type: str,
    title: str,
    author: str,
    year: str,
    **extra_fields,
) -> Optional[CitationInfo]:
    """Create a new citation entry in the bibliography.

    Args:
        project_dir: Path to the project directory
        key: Citation key (e.g., "smith2024")
        entry_type: BibTeX entry type (article, book, misc, etc.)
        title: Title of the work
        author: Author(s)
        year: Publication year
        **extra_fields: Additional BibTeX fields (journal, volume, pages, doi, url, etc.)

    Returns:
        CitationInfo if created, None if key already exists
    """
    bib_path = _get_bib_path(project_dir)

    # Check if key already exists
    if get_citation(project_dir, key):
        return None

    # Build BibTeX entry
    fields = []
    fields.append(f"  author  = {{{author}}}")
    fields.append(f"  title   = {{{title}}}")
    fields.append(f"  year    = {{{year}}}")

    for field_name, field_value in extra_fields.items():
        if field_value:
            fields.append(f"  {field_name} = {{{field_value}}}")

    entry = f"@{entry_type}{{{key},\n" + ",\n".join(fields) + "\n}\n"

    # Append to file
    if bib_path.exists():
        content = bib_path.read_text(encoding="utf-8")
        if not content.endswith("\n"):
            content += "\n"
        content += "\n" + entry
    else:
        content = "%% Bibliography - Add your references here\n\n" + entry

    bib_path.write_text(content, encoding="utf-8")

    return get_citation(project_dir, key)


def update_citation(
    project_dir: PathLike,
    key: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    year: Optional[str] = None,
    **extra_fields,
) -> bool:
    """Update an existing citation entry.

    Only provided fields will be updated; others remain unchanged.

    Args:
        project_dir: Path to the project directory
        key: Citation key to update
        title: New title (optional)
        author: New author(s) (optional)
        year: New year (optional)
        **extra_fields: Additional fields to update

    Returns:
        True if updated, False if not found
    """
    bib_path = _get_bib_path(project_dir)
    if not bib_path.exists():
        return False

    existing = get_citation(project_dir, key)
    if not existing:
        return False

    content = bib_path.read_text(encoding="utf-8")

    # Build updated fields
    new_fields = existing.fields.copy()
    if title is not None:
        new_fields["title"] = title
    if author is not None:
        new_fields["author"] = author
    if year is not None:
        new_fields["year"] = year
    for field_name, field_value in extra_fields.items():
        if field_value is not None:
            new_fields[field_name] = field_value

    # Build new entry
    field_lines = []
    # Put standard fields first in order
    standard_order = [
        "author",
        "title",
        "journal",
        "booktitle",
        "year",
        "volume",
        "number",
        "pages",
        "doi",
        "url",
    ]
    added = set()
    for field_name in standard_order:
        if field_name in new_fields:
            field_lines.append(f"  {field_name} = {{{new_fields[field_name]}}}")
            added.add(field_name)

    # Add remaining fields
    for field_name, field_value in new_fields.items():
        if field_name not in added:
            field_lines.append(f"  {field_name} = {{{field_value}}}")

    new_entry = f"@{existing.entry_type}{{{key},\n" + ",\n".join(field_lines) + "\n}"

    # Replace old entry with new one
    # Escape special regex chars in raw_entry
    old_pattern = re.escape(existing.raw_entry)
    new_content = re.sub(old_pattern, new_entry, content, count=1)

    bib_path.write_text(new_content, encoding="utf-8")
    return True


def delete_citation(project_dir: PathLike, key: str) -> bool:
    """Delete a citation entry from the bibliography.

    Args:
        project_dir: Path to the project directory
        key: Citation key to delete

    Returns:
        True if deleted, False if not found
    """
    bib_path = _get_bib_path(project_dir)
    if not bib_path.exists():
        return False

    existing = get_citation(project_dir, key)
    if not existing:
        return False

    content = bib_path.read_text(encoding="utf-8")

    # Remove the entry and any surrounding blank lines
    old_pattern = re.escape(existing.raw_entry)
    new_content = re.sub(r"\n*" + old_pattern + r"\n*", "\n\n", content)
    new_content = re.sub(
        r"\n{3,}", "\n\n", new_content
    )  # Clean up multiple blank lines

    bib_path.write_text(new_content, encoding="utf-8")
    return True


__all__ = [
    "CitationInfo",
    "list_citations",
    "get_citation",
    "create_citation",
    "update_citation",
    "delete_citation",
]

"""Table management for sciwriter LaTeX documents.

CRUD operations for tables: list, get, create, update, delete.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from ._utils import DOC_DIRS, parse_caption_file

PathLike = Union[str, Path]


@dataclass
class TableInfo:
    """Information about a table."""

    id: str  # e.g., "01_example_table"
    label: str  # e.g., "tab:example_table_01"
    caption: str
    caption_file: Path
    compiled_file: Optional[Path] = None


def _get_tables_dir(project_dir: PathLike, doc_type: str) -> Optional[Path]:
    """Get the tables directory."""
    project_dir = Path(project_dir)
    doc_dir = DOC_DIRS.get(doc_type)
    if not doc_dir:
        return None
    return project_dir / doc_dir / "contents" / "tables"


def list_tables(
    project_dir: PathLike,
    doc_type: str = "manuscript",
) -> list[TableInfo]:
    """List all tables in a document."""
    tables_dir = _get_tables_dir(project_dir, doc_type)
    if not tables_dir:
        return []

    caption_media_dir = tables_dir / "caption_and_media"
    compiled_dir = tables_dir / "compiled"

    if not caption_media_dir.exists():
        return []

    tables = []

    for caption_file in sorted(caption_media_dir.glob("[0-9][0-9]_*.tex")):
        base_id = caption_file.stem
        caption, label = parse_caption_file(caption_file)

        compiled_file = None
        if compiled_dir.exists():
            compiled_tex = compiled_dir / f"{base_id}.tex"
            if compiled_tex.exists():
                compiled_file = compiled_tex

        tables.append(
            TableInfo(
                id=base_id,
                label=label,
                caption=caption,
                caption_file=caption_file,
                compiled_file=compiled_file,
            )
        )

    return tables


def get_table(
    project_dir: PathLike,
    table_id: str,
    doc_type: str = "manuscript",
) -> Optional[TableInfo]:
    """Get information about a specific table."""
    tables = list_tables(project_dir, doc_type)

    for tbl in tables:
        if tbl.id == table_id or tbl.id.startswith(f"{table_id}_"):
            return tbl

    return None


def create_table(
    project_dir: PathLike,
    table_id: str,
    caption: str,
    doc_type: str = "manuscript",
    csv_path: Optional[PathLike] = None,
) -> Optional[TableInfo]:
    """Create a new table with caption and CSV data.

    Creates both:
    - {table_id}.tex: Caption file with \\caption and \\label
    - {table_id}.csv: Table data (from csv_path or placeholder)

    Args:
        project_dir: Project directory path
        table_id: Table identifier (e.g., '01_results')
        caption: Table caption text
        doc_type: Document type
        csv_path: Optional path to CSV file to copy as table data

    The CSV file is required for process_tables.sh to compile the table.
    """
    tables_dir = _get_tables_dir(project_dir, doc_type)
    if not tables_dir:
        return None

    caption_media_dir = tables_dir / "caption_and_media"
    caption_media_dir.mkdir(parents=True, exist_ok=True)

    caption_file = caption_media_dir / f"{table_id}.tex"
    csv_file = caption_media_dir / f"{table_id}.csv"

    if caption_file.exists():
        return None

    name_part = "_".join(table_id.split("_")[1:])
    num_part = table_id.split("_")[0]
    label = f"tab:{name_part}_{num_part}"

    # Create caption file
    caption_content = f"""%% -*- coding: utf-8 -*-
\\caption{{{caption}}}
\\label{{{label}}}
%%%% EOF"""
    caption_file.write_text(caption_content, encoding="utf-8")

    # Symlink CSV or create placeholder
    if csv_path:
        csv_source = Path(csv_path).resolve()
        if csv_source.exists():
            if csv_file.exists():
                csv_file.unlink()
            csv_file.symlink_to(csv_source)
        else:
            # Source doesn't exist, create placeholder
            csv_content = """Column1,Column2,Column3
Value1,Value2,Value3
Value4,Value5,Value6"""
            csv_file.write_text(csv_content, encoding="utf-8")
    else:
        # Create placeholder CSV (required for table compilation)
        csv_content = """Column1,Column2,Column3
Value1,Value2,Value3
Value4,Value5,Value6"""
        csv_file.write_text(csv_content, encoding="utf-8")

    return TableInfo(
        id=table_id,
        label=label,
        caption=caption,
        caption_file=caption_file,
    )


def update_table(
    project_dir: PathLike,
    table_id: str,
    caption: str,
    doc_type: str = "manuscript",
) -> bool:
    """Update a table's caption."""
    tbl = get_table(project_dir, table_id, doc_type)
    if not tbl or not tbl.caption_file.exists():
        return False

    content = tbl.caption_file.read_text(encoding="utf-8")
    new_content = re.sub(
        r"\\caption\{[^}]*\}",
        f"\\\\caption{{{caption}}}",
        content,
    )
    tbl.caption_file.write_text(new_content, encoding="utf-8")
    return True


def delete_table(
    project_dir: PathLike,
    table_id: str,
    doc_type: str = "manuscript",
) -> bool:
    """Delete a table and its associated files."""
    tbl = get_table(project_dir, table_id, doc_type)
    if not tbl:
        return False

    if tbl.caption_file.exists():
        tbl.caption_file.unlink()

    if tbl.compiled_file and tbl.compiled_file.exists():
        tbl.compiled_file.unlink()

    return True


__all__ = [
    "TableInfo",
    "list_tables",
    "get_table",
    "create_table",
    "update_table",
    "delete_table",
]

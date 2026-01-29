"""Reference management for sciwriter LaTeX documents.

Find references (\\ref{}, \\cite{}) and labels in documents.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ._utils import DOC_DIRS


@dataclass
class Reference:
    """A reference found in the document."""

    ref_type: str  # "figure", "table", "section", "equation"
    label: str  # The label being referenced
    file_path: Path  # File where reference was found
    line_number: int
    context: str  # Surrounding text


def find_references(
    project_dir: Path,
    doc_type: str = "manuscript",
    ref_type: Optional[str] = None,
) -> list[Reference]:
    """Find all references (\\ref{}, \\cite{}) in the document.

    Args:
        project_dir: Path to the project directory
        doc_type: Document type
        ref_type: Filter by type ("figure", "table", "section", "equation", "citation")

    Returns:
        List of Reference objects
    """
    from sciwriter._content import SECTIONS, get_section_path

    references = []
    doc_dir = DOC_DIRS.get(doc_type)
    if not doc_dir:
        return references

    ref_patterns = {
        "figure": r"\\ref\{(fig:[^}]+)\}",
        "table": r"\\ref\{(tab:[^}]+)\}",
        "section": r"\\ref\{(sec:[^}]+)\}",
        "equation": r"\\ref\{(eq:[^}]+)\}",
        "citation": r"\\cite[pt]?\{([^}]+)\}",
    }

    search_files = []

    for section in SECTIONS:
        path = get_section_path(project_dir, section, doc_type)
        if path and path.exists():
            search_files.append(path)

    main_tex = project_dir / doc_dir / "manuscript.tex"
    if main_tex.exists():
        search_files.append(main_tex)

    types_to_search = [ref_type] if ref_type else list(ref_patterns.keys())

    for file_path in search_files:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            for rtype in types_to_search:
                pattern = ref_patterns.get(rtype)
                if not pattern:
                    continue

                for match in re.finditer(pattern, line):
                    labels = match.group(1).split(",")
                    for label in labels:
                        label = label.strip()
                        references.append(
                            Reference(
                                ref_type=rtype,
                                label=label,
                                file_path=file_path,
                                line_number=line_num,
                                context=line.strip()[:100],
                            )
                        )

    return references


def find_labels(
    project_dir: Path,
    doc_type: str = "manuscript",
) -> dict[str, Path]:
    """Find all labels defined in the document.

    Returns:
        Dict mapping label to file path where it's defined
    """
    labels = {}
    doc_dir = DOC_DIRS.get(doc_type)
    if not doc_dir:
        return labels

    doc_path = project_dir / doc_dir

    for tex_file in doc_path.rglob("*.tex"):
        if not tex_file.is_file():
            continue
        content = tex_file.read_text(encoding="utf-8")
        for match in re.finditer(r"\\label\{([^}]+)\}", content):
            label = match.group(1)
            labels[label] = tex_file

    return labels


__all__ = ["Reference", "find_references", "find_labels"]

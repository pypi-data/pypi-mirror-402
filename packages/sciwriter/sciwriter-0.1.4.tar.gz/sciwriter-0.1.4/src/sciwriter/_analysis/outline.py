"""Document outline generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class OutlineItem:
    """An item in the document outline."""

    name: str
    level: int  # 1=section, 2=subsection, etc.
    word_count: int
    char_count: int
    file_path: Optional[Path] = None
    children: list["OutlineItem"] = field(default_factory=list)


def get_outline(
    project_dir: Path,
    doc_type: str = "manuscript",
) -> list[OutlineItem]:
    """Get the document outline with word counts.

    Args:
        project_dir: Path to the project directory
        doc_type: Document type (manuscript, supplementary, revision)

    Returns:
        List of OutlineItem objects representing the document structure
    """
    from sciwriter._analysis.wordcount import count_words_in_latex
    from sciwriter._content import get_section_path, read_section

    outline = []

    # Standard IMRaD sections in order
    section_order = [
        "abstract",
        "introduction",
        "methods",
        "results",
        "discussion",
        "data_availability",
    ]

    for section_name in section_order:
        path = get_section_path(project_dir, section_name, doc_type)
        if not path or not path.exists():
            continue

        section = read_section(project_dir, section_name, doc_type)
        if not section:
            continue

        word_count, char_count, _ = count_words_in_latex(section.content)

        outline.append(
            OutlineItem(
                name=section_name.replace("_", " ").title(),
                level=1,
                word_count=word_count,
                char_count=char_count,
                file_path=path,
            )
        )

    return outline


__all__ = ["OutlineItem", "get_outline"]

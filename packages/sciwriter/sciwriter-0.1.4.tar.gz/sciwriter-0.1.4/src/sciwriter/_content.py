"""Content management for sciwriter LaTeX documents.

Provides CRUD operations for manuscript sections like abstract,
introduction, methods, results, discussion, etc.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

PathLike = Union[str, Path]


@dataclass
class Section:
    """Represents a manuscript section."""

    name: str
    content: str
    file_path: Path
    doc_type: str = "manuscript"


# Section configuration: name -> (filename, wrapper pattern)
SECTIONS = {
    "abstract": ("abstract.tex", r"\\begin\{abstract\}(.*?)\\end\{abstract\}"),
    "introduction": ("introduction.tex", None),
    "methods": ("methods.tex", None),
    "results": ("results.tex", None),
    "discussion": ("discussion.tex", None),
    "highlights": ("highlights.tex", None),
    "data_availability": ("data_availability.tex", None),
    "graphical_abstract": ("graphical_abstract.tex", None),
}

# Default template content for each section
SECTION_TEMPLATES = {
    "abstract": r"""\pdfbookmark[1]{Abstract}{abstract}

% Your abstract here (150-300 words typical)""",
    "introduction": r"""\section{Introduction}

% Your introduction here""",
    "methods": r"""\section{Methods}

% Your methods here""",
    "results": r"""\section{Results}

% Your results here""",
    "discussion": r"""\section{Discussion}

% Your discussion here""",
    "highlights": r"""\pdfbookmark[1]{Highlights}{highlights}

\begin{itemize}
    \item % Highlight 1
    \item % Highlight 2
    \item % Highlight 3
\end{itemize}""",
    "data_availability": r"""\pdfbookmark[1]{Data Availability Statement}{data_availability}

\section*{Data Availability Statement}

% Describe data availability here

\label{data and code availability}""",
    "graphical_abstract": r"""\pdfbookmark[1]{Graphical Abstract}{graphical_abstract}

% Include graphical abstract here""",
}

SHARED_FILES = {
    "title": "title.tex",
    "authors": "authors.tex",
    "keywords": "keywords.tex",
    "journal_name": "journal_name.tex",
}

DOC_DIRS = {
    "manuscript": "01_manuscript",
    "supplementary": "02_supplementary",
    "revision": "03_revision",
}


def get_section_path(
    project_dir: PathLike,
    section: str,
    doc_type: str = "manuscript",
) -> Optional[Path]:
    """Get the path to a section file."""
    project_dir = Path(project_dir)
    if section in SHARED_FILES:
        return project_dir / "00_shared" / SHARED_FILES[section]

    if section not in SECTIONS:
        return None

    doc_dir = DOC_DIRS.get(doc_type)
    if not doc_dir:
        return None

    filename = SECTIONS[section][0]
    return project_dir / doc_dir / "contents" / filename


def read_section(
    project_dir: PathLike,
    section: str,
    doc_type: str = "manuscript",
) -> Optional[Section]:
    """Read a section from the manuscript.

    Args:
        project_dir: Path to the project directory
        section: Section name (abstract, introduction, methods, etc.)
        doc_type: Document type (manuscript, supplementary, revision)

    Returns:
        Section object with content, or None if not found
    """
    file_path = get_section_path(project_dir, section, doc_type)
    if not file_path or not file_path.exists():
        return None

    content = file_path.read_text(encoding="utf-8")

    # Extract content from wrapper if defined
    if section in SECTIONS:
        pattern = SECTIONS[section][1]
        if pattern:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                content = match.group(1).strip()

    return Section(
        name=section,
        content=content,
        file_path=file_path,
        doc_type=doc_type,
    )


def update_section(
    project_dir: PathLike,
    section: str,
    content: str,
    doc_type: str = "manuscript",
) -> bool:
    """Update a section in the manuscript.

    Args:
        project_dir: Path to the project directory
        section: Section name
        content: New content for the section
        doc_type: Document type

    Returns:
        True if successful, False otherwise
    """
    file_path = get_section_path(project_dir, section, doc_type)
    if not file_path:
        return False

    # If file exists and has wrapper, preserve it
    if file_path.exists() and section in SECTIONS:
        pattern = SECTIONS[section][1]
        if pattern:
            existing = file_path.read_text(encoding="utf-8")
            # Replace content inside wrapper
            new_content = re.sub(
                pattern,
                lambda m: m.group(0).replace(m.group(1), f"\n{content}\n"),
                existing,
                flags=re.DOTALL,
            )
            file_path.write_text(new_content, encoding="utf-8")
            return True

    # Write content directly
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return True


def create_section(
    project_dir: PathLike,
    section: str,
    content: str = "",
    doc_type: str = "manuscript",
    template: Optional[str] = None,
) -> bool:
    """Create a new section file.

    Args:
        project_dir: Path to the project directory
        section: Section name
        content: Initial content
        doc_type: Document type
        template: Optional template to use

    Returns:
        True if successful, False otherwise
    """
    file_path = get_section_path(project_dir, section, doc_type)
    if not file_path:
        return False

    if file_path.exists():
        return False  # Already exists

    # Use template or create default structure
    if template:
        file_content = template
    elif section == "abstract":
        file_content = f"""%% -*- coding: utf-8 -*-
\\begin{{abstract}}
  \\pdfbookmark[1]{{Abstract}}{{abstract}}

{content}

\\end{{abstract}}

%%%% EOF"""
    else:
        file_content = f"""%% -*- coding: utf-8 -*-
%% {section.replace("_", " ").title()}

{content}

%%%% EOF"""

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(file_content, encoding="utf-8")
    return True


def delete_section(
    project_dir: PathLike,
    section: str,
    doc_type: str = "manuscript",
) -> bool:
    """Delete a section file.

    Args:
        project_dir: Path to the project directory
        section: Section name
        doc_type: Document type

    Returns:
        True if successful, False otherwise
    """
    file_path = get_section_path(project_dir, section, doc_type)
    if not file_path or not file_path.exists():
        return False

    file_path.unlink()
    return True


def list_sections(
    project_dir: PathLike,
    doc_type: str = "manuscript",
) -> list[dict]:
    """List available sections in a document.

    Args:
        project_dir: Path to the project directory
        doc_type: Document type

    Returns:
        List of dicts with section name and path
    """
    sections = []

    for section in SECTIONS:
        path = get_section_path(project_dir, section, doc_type)
        if path and path.exists():
            sections.append({"name": section, "path": str(path)})

    return sections


def init_section(
    project_dir: PathLike,
    section: str,
    doc_type: str = "manuscript",
) -> bool:
    """Initialize a section to its default template content.

    Args:
        project_dir: Path to the project directory
        section: Section name to initialize
        doc_type: Document type

    Returns:
        True if successful, False otherwise
    """
    if section not in SECTIONS:
        return False

    template = SECTION_TEMPLATES.get(section)
    if not template:
        return False

    return update_section(project_dir, section, template, doc_type)


def init_sections(
    project_dir: PathLike,
    sections: Optional[list[str]] = None,
    doc_type: str = "manuscript",
) -> dict[str, bool]:
    """Initialize multiple sections to their default template content.

    Args:
        project_dir: Path to the project directory
        sections: List of section names to initialize (None = all sections)
        doc_type: Document type

    Returns:
        Dict mapping section names to success status
    """
    if sections is None:
        # Default to core IMRaD sections (exclude highlights, graphical_abstract)
        sections = [
            "abstract",
            "introduction",
            "methods",
            "results",
            "discussion",
            "data_availability",
        ]

    results = {}
    for section in sections:
        results[section] = init_section(project_dir, section, doc_type)

    return results


# Convenience functions for common operations
def read_abstract(project_dir: PathLike) -> Optional[str]:
    """Read the abstract content."""
    section = read_section(project_dir, "abstract")
    return section.content if section else None


def update_abstract(project_dir: PathLike, content: str) -> bool:
    """Update the abstract content."""
    return update_section(project_dir, "abstract", content)


def read_introduction(project_dir: PathLike) -> Optional[str]:
    """Read the introduction content."""
    section = read_section(project_dir, "introduction")
    return section.content if section else None


def update_introduction(project_dir: PathLike, content: str) -> bool:
    """Update the introduction content."""
    return update_section(project_dir, "introduction", content)


def read_methods(project_dir: PathLike) -> Optional[str]:
    """Read the methods content."""
    section = read_section(project_dir, "methods")
    return section.content if section else None


def update_methods(project_dir: PathLike, content: str) -> bool:
    """Update the methods content."""
    return update_section(project_dir, "methods", content)


def read_results(project_dir: PathLike) -> Optional[str]:
    """Read the results content."""
    section = read_section(project_dir, "results")
    return section.content if section else None


def update_results(project_dir: PathLike, content: str) -> bool:
    """Update the results content."""
    return update_section(project_dir, "results", content)


def read_discussion(project_dir: PathLike) -> Optional[str]:
    """Read the discussion content."""
    section = read_section(project_dir, "discussion")
    return section.content if section else None


def update_discussion(project_dir: PathLike, content: str) -> bool:
    """Update the discussion content."""
    return update_section(project_dir, "discussion", content)


def read_title(project_dir: PathLike) -> Optional[str]:
    """Read the title content."""
    section = read_section(project_dir, "title")
    return section.content if section else None


def update_title(project_dir: PathLike, content: str) -> bool:
    """Update the title content."""
    return update_section(project_dir, "title", content)


__all__ = [
    # Core functions
    "read_section",
    "update_section",
    "create_section",
    "delete_section",
    "list_sections",
    "get_section_path",
    "init_section",
    "init_sections",
    # Section dataclass
    "Section",
    # Templates
    "SECTION_TEMPLATES",
    # Convenience functions
    "read_abstract",
    "update_abstract",
    "read_introduction",
    "update_introduction",
    "read_methods",
    "update_methods",
    "read_results",
    "update_results",
    "read_discussion",
    "update_discussion",
    "read_title",
    "update_title",
]

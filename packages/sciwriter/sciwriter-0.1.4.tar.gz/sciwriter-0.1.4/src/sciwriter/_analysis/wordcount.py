"""Word counting for LaTeX documents."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class WordCountResult:
    """Word count results for a document or section."""

    total_words: int
    total_chars: int
    total_chars_no_spaces: int
    sections: dict[str, int] = field(default_factory=dict)


def count_words_in_latex(content: str) -> tuple[int, int, int]:
    """Count words and characters in LaTeX content.

    Returns:
        Tuple of (word_count, char_count, char_count_no_spaces)
    """
    # Remove comments
    content = re.sub(r"%.*$", "", content, flags=re.MULTILINE)

    # Remove common LaTeX commands but keep their content
    content = re.sub(r"\\textbf\{([^}]*)\}", r"\1", content)
    content = re.sub(r"\\textit\{([^}]*)\}", r"\1", content)
    content = re.sub(r"\\emph\{([^}]*)\}", r"\1", content)
    content = re.sub(r"\\underline\{([^}]*)\}", r"\1", content)

    # Remove citation and reference commands
    content = re.sub(r"\\cite[pt]?\{[^}]*\}", "", content)
    content = re.sub(r"\\ref\{[^}]*\}", "", content)
    content = re.sub(r"\\label\{[^}]*\}", "", content)

    # Remove other LaTeX commands
    content = re.sub(r"\\[a-zA-Z]+\*?\{[^}]*\}", "", content)
    content = re.sub(r"\\[a-zA-Z]+\*?", "", content)

    # Remove environments
    content = re.sub(r"\\begin\{[^}]*\}", "", content)
    content = re.sub(r"\\end\{[^}]*\}", "", content)

    # Remove special characters
    content = re.sub(r"[{}\\$&%#_^~]", "", content)

    # Clean up whitespace
    content = re.sub(r"\s+", " ", content).strip()

    # Count
    words = content.split()
    word_count = len(words)
    char_count = len(content)
    char_count_no_spaces = len(content.replace(" ", ""))

    return word_count, char_count, char_count_no_spaces


def get_word_count(
    project_dir: Path,
    doc_type: str = "manuscript",
    section: Optional[str] = None,
) -> WordCountResult:
    """Get word counts for the document.

    Args:
        project_dir: Path to the project directory
        doc_type: Document type
        section: Specific section to count (optional)

    Returns:
        WordCountResult with counts
    """
    from sciwriter._content import SECTIONS, read_section

    sections_to_count = [section] if section else list(SECTIONS.keys())
    section_counts = {}
    total_words = 0
    total_chars = 0
    total_chars_no_spaces = 0

    for section_name in sections_to_count:
        sec = read_section(project_dir, section_name, doc_type)
        if not sec:
            continue

        words, chars, chars_no_space = count_words_in_latex(sec.content)
        section_counts[section_name] = words
        total_words += words
        total_chars += chars
        total_chars_no_spaces += chars_no_space

    return WordCountResult(
        total_words=total_words,
        total_chars=total_chars,
        total_chars_no_spaces=total_chars_no_spaces,
        sections=section_counts,
    )


__all__ = ["WordCountResult", "get_word_count", "count_words_in_latex"]

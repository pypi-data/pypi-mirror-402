"""Document analysis for sciwriter LaTeX documents.

Provides analysis tools for writing assistance:
- Document outline with word counts
- Word count per section and total
- Document validation (broken refs, missing labels)
- Compile log parsing
- Version diff viewing
"""

from sciwriter._analysis.outline import OutlineItem, get_outline
from sciwriter._analysis.validation import (
    ValidationIssue,
    ValidationResult,
    check_document,
    get_compile_log,
    parse_compile_errors,
)
from sciwriter._analysis.versions import list_versions, view_diff
from sciwriter._analysis.wordcount import WordCountResult, get_word_count

__all__ = [
    # Outline
    "OutlineItem",
    "get_outline",
    # Word count
    "WordCountResult",
    "get_word_count",
    # Validation
    "ValidationIssue",
    "ValidationResult",
    "check_document",
    "get_compile_log",
    "parse_compile_errors",
    # Versions
    "list_versions",
    "view_diff",
]

"""Document validation for LaTeX documents."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

DOC_DIRS = {
    "manuscript": "01_manuscript",
    "supplementary": "02_supplementary",
    "revision": "03_revision",
}


@dataclass
class ValidationIssue:
    """A validation issue found in the document."""

    severity: str  # "error", "warning", "info"
    category: str  # "reference", "label", "citation", "syntax"
    message: str
    file_path: Optional[Path] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Results from document validation."""

    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)


def check_document(
    project_dir: Path,
    doc_type: str = "manuscript",
) -> ValidationResult:
    """Validate the document for common issues.

    Checks:
    - Undefined references
    - Unused labels
    - Missing figures/tables
    - Duplicate labels

    Args:
        project_dir: Path to the project directory
        doc_type: Document type

    Returns:
        ValidationResult with issues found
    """
    from sciwriter._media import (
        find_labels,
        find_references,
        list_figures,
        list_tables,
    )

    issues = []
    summary = {"error": 0, "warning": 0, "info": 0}

    # Get all labels and references
    labels = find_labels(project_dir, doc_type)
    references = find_references(project_dir, doc_type)

    # Get available figures and tables
    figures = list_figures(project_dir, doc_type)
    tables = list_tables(project_dir, doc_type)

    figure_labels = {f.label for f in figures if f.label}
    table_labels = {t.label for t in tables if t.label}
    all_labels = set(labels.keys()) | figure_labels | table_labels

    # Check for undefined references
    referenced_labels = set()
    for ref in references:
        if ref.ref_type == "citation":
            continue
        referenced_labels.add(ref.label)
        if ref.label not in all_labels:
            issues.append(
                ValidationIssue(
                    severity="error",
                    category="reference",
                    message=f"Undefined reference: \\ref{{{ref.label}}}",
                    file_path=ref.file_path,
                    line_number=ref.line_number,
                    suggestion=f"Add \\label{{{ref.label}}} or fix reference",
                )
            )
            summary["error"] += 1

    # Check for unused labels
    for label, path in labels.items():
        if label not in referenced_labels:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    category="label",
                    message=f"Unused label: \\label{{{label}}}",
                    file_path=path,
                    suggestion="Remove if not needed",
                )
            )
            summary["warning"] += 1

    # Check for figures without media
    for fig in figures:
        if not fig.media_files:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    category="figure",
                    message=f"Figure {fig.id} has caption but no media file",
                    file_path=fig.caption_file,
                )
            )
            summary["warning"] += 1

    # Check for duplicate labels
    _check_duplicate_labels(project_dir, doc_type, issues, summary)

    return ValidationResult(
        is_valid=summary["error"] == 0,
        issues=issues,
        summary=summary,
    )


def _check_duplicate_labels(
    project_dir: Path,
    doc_type: str,
    issues: list[ValidationIssue],
    summary: dict[str, int],
) -> None:
    """Check for duplicate labels in document."""
    doc_dir = DOC_DIRS.get(doc_type)
    if not doc_dir:
        return

    label_counts: dict[str, list[Path]] = {}
    doc_path = project_dir / doc_dir

    # Files to exclude (compiled outputs, diffs, archives)
    exclude_patterns = [
        "manuscript.tex",
        "supplementary.tex",
        "revision.tex",
        "_diff.tex",
        "/archive/",
    ]

    for tex_file in doc_path.rglob("*.tex"):
        if not tex_file.is_file():
            continue
        # Skip compiled/generated files
        file_str = str(tex_file)
        if any(pattern in file_str for pattern in exclude_patterns):
            continue
        content = tex_file.read_text(encoding="utf-8")
        for match in re.finditer(r"\\label\{([^}]+)\}", content):
            label = match.group(1)
            if label not in label_counts:
                label_counts[label] = []
            label_counts[label].append(tex_file)

    for label, paths in label_counts.items():
        if len(paths) > 1:
            issues.append(
                ValidationIssue(
                    severity="error",
                    category="label",
                    message=f"Duplicate label: {label} in {len(paths)} files",
                )
            )
            summary["error"] += 1


def get_compile_log(
    project_dir: Path,
    doc_type: str = "manuscript",
    lines: int = 100,
) -> Optional[str]:
    """Get the last compilation log."""
    doc_dir = DOC_DIRS.get(doc_type)
    if not doc_dir:
        return None

    log_locations = [
        project_dir / doc_dir / "logs" / "global.log",
        project_dir / doc_dir / "manuscript.log",
        project_dir / doc_dir / "logs" / "latexmk.log",
    ]

    for log_path in log_locations:
        if log_path.exists():
            content = log_path.read_text(encoding="utf-8", errors="replace")
            log_lines = content.split("\n")
            return "\n".join(log_lines[-lines:])

    return None


def parse_compile_errors(log_content: str) -> list[ValidationIssue]:
    """Parse compilation log for errors and warnings."""
    issues = []

    error_pattern = r"^! (.+)$"
    warning_pattern = r"^(?:LaTeX|Package \w+) Warning: (.+?)(?:\.|$)"
    line_pattern = r"^l\.(\d+)"

    lines = log_content.split("\n")
    current_error = None

    for line in lines:
        error_match = re.match(error_pattern, line)
        if error_match:
            current_error = error_match.group(1)
            continue

        if current_error:
            line_match = re.match(line_pattern, line)
            if line_match:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        category="compile",
                        message=current_error,
                        line_number=int(line_match.group(1)),
                    )
                )
                current_error = None
            elif line.strip() and not line.startswith(" "):
                issues.append(
                    ValidationIssue(
                        severity="error",
                        category="compile",
                        message=current_error,
                    )
                )
                current_error = None

        warning_match = re.match(warning_pattern, line)
        if warning_match:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    category="compile",
                    message=warning_match.group(1),
                )
            )

    return issues


__all__ = [
    "ValidationIssue",
    "ValidationResult",
    "check_document",
    "get_compile_log",
    "parse_compile_errors",
]

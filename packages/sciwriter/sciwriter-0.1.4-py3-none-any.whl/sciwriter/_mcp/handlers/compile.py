"""MCP handlers for compilation operations."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DOC_DIRS = {
    "manuscript": "01_manuscript",
    "supplementary": "02_supplementary",
    "revision": "03_revision",
}


def _check_dependencies() -> dict[str, bool]:
    """Check LaTeX tool availability."""
    from sciwriter._compiler import check_dependencies

    return check_dependencies()


def _check_bibliography(project_dir: Path, doc_type: str) -> list[dict]:
    """Check for missing bibliography entries.

    Returns list of issues found.
    """
    issues = []
    bib_path = project_dir / "00_shared" / "bibliography.bib"

    if not bib_path.exists():
        issues.append(
            {
                "severity": "error",
                "message": "Bibliography file not found: 00_shared/bibliography.bib",
                "suggestion": "Create bibliography.bib with your BibTeX entries",
            }
        )
        return issues

    # Read bib file to get available keys
    bib_content = bib_path.read_text(encoding="utf-8", errors="replace")
    bib_keys = set(re.findall(r"@\w+\{(\w+),", bib_content))

    # Find citations in document
    doc_dir = DOC_DIRS.get(doc_type)
    if not doc_dir:
        return issues

    doc_path = project_dir / doc_dir
    if not doc_path.exists():
        return issues

    cited_keys = set()
    for tex_file in doc_path.rglob("*.tex"):
        if tex_file.is_file():
            content = tex_file.read_text(encoding="utf-8", errors="replace")
            # Match \cite{key}, \cite{key1,key2}, \citep{}, \citet{}, etc.
            for match in re.finditer(r"\\cite[pt]?\{([^}]+)\}", content):
                keys = match.group(1).split(",")
                for key in keys:
                    cited_keys.add(key.strip())

    # Find missing citations
    missing = cited_keys - bib_keys
    if missing:
        issues.append(
            {
                "severity": "warning",
                "message": f"Missing bibliography entries: {', '.join(sorted(missing))}",
                "missing_keys": sorted(missing),
                "suggestion": f"Add BibTeX entries for: {', '.join(sorted(missing))} to 00_shared/bibliography.bib",
            }
        )

    return issues


def _parse_latex_errors(output: str) -> list[dict]:
    """Parse LaTeX compilation output for specific errors."""
    issues = []

    # Common error patterns
    patterns = [
        (
            r"! LaTeX Error: File `([^']+)' not found",
            "Missing file: {0}",
            "Install the missing package or check the file path",
        ),
        (
            r"! Undefined control sequence.*\\(\w+)",
            "Undefined command: \\{0}",
            "Check spelling or add the required package",
        ),
        (
            r"! Missing \$ inserted",
            "Math mode error: missing $",
            "Wrap math expressions in $ signs",
        ),
        (
            r"! Package ([^:]+) Error: (.+)",
            "Package {0} error: {1}",
            "Check package documentation",
        ),
        (
            r"Runaway argument\?",
            "Runaway argument (missing closing brace)",
            "Check for unmatched braces {{ }}",
        ),
        (
            r"! Emergency stop",
            "LaTeX emergency stop",
            "Check the log file for the root cause above this line",
        ),
        (
            r"Citation `([^']+)' on page \d+ undefined",
            "Undefined citation: {0}",
            "Add BibTeX entry to 00_shared/bibliography.bib",
        ),
        (
            r"Reference `([^']+)' on page \d+ undefined",
            "Undefined reference: \\ref{{{0}}}",
            "Add \\label{{{0}}} or fix the reference",
        ),
    ]

    for pattern, msg_template, suggestion in patterns:
        for match in re.finditer(pattern, output, re.MULTILINE):
            groups = match.groups() if match.groups() else ()
            message = msg_template.format(*groups) if groups else msg_template
            issues.append(
                {
                    "severity": "error",
                    "message": message,
                    "suggestion": suggestion.format(*groups) if groups else suggestion,
                }
            )

    return issues


async def compile_handler(arguments: dict[str, Any]) -> str:
    """Handle compile tool invocation with pre-flight checks.

    Args:
        arguments: Tool arguments containing:
            - project_dir: Path to project directory (required)
            - doc_type: Document type (manuscript/supplementary/revision/all)
            - quiet: Suppress output
            - no_diff: Skip diff generation
            - no_figs: Skip figure processing
            - no_tables: Skip table processing
            - draft: Single-pass compilation
            - dark_mode: Dark theme
            - engine: Compilation engine (auto/tectonic/latexmk/3pass)
            - timeout: Maximum compilation time

    Returns:
        JSON string with compilation result including parsed errors and suggestions
    """
    from sciwriter._compiler import compile_document, get_project_info

    project_dir = Path(arguments["project_dir"])
    doc_type = arguments.get("doc_type", "manuscript")
    timeout = arguments.get("timeout", 300)

    # Pre-flight check: project directory
    if not project_dir.exists():
        return json.dumps(
            {
                "success": False,
                "error": f"Project directory not found: {project_dir}",
                "suggestion": "Provide a valid project path or registered project name",
            }
        )

    # Pre-flight check: is it a sciwriter project?
    info = get_project_info(project_dir)
    if not info.get("has_makefile"):
        return json.dumps(
            {
                "success": False,
                "error": f"Not a sciwriter project: {project_dir}",
                "missing": "Makefile",
                "suggestion": "Use 'sciwriter init' to create a new project",
            }
        )

    # Pre-flight check: dependencies
    deps = _check_dependencies()
    missing_deps = [name for name, available in deps.items() if not available]
    critical_missing = [d for d in missing_deps if d in ["pdflatex", "make"]]

    if critical_missing:
        return json.dumps(
            {
                "success": False,
                "error": f"Missing critical dependencies: {', '.join(critical_missing)}",
                "all_missing": missing_deps,
                "suggestion": "Install LaTeX (texlive-full) and make",
            }
        )

    # Pre-flight check: bibliography (warning only)
    bib_issues = _check_bibliography(project_dir, doc_type)

    # Compile document
    result = compile_document(
        doc_type=doc_type,
        project_dir=project_dir,
        quiet=arguments.get("quiet", False),
        verbose=arguments.get("verbose", False),
        generate_diff=not arguments.get("no_diff", False),
        crop_tif=arguments.get("crop_tif", False),
        process_figures=not arguments.get("no_figs", False),
        process_tables=not arguments.get("no_tables", False),
        dark_mode=arguments.get("dark_mode", False),
        draft=arguments.get("draft", False),
        timeout=timeout,
    )

    if result.success:
        response = {
            "success": True,
            "message": f"Compiled {doc_type} successfully",
            "output_path": str(result.output_path),
            "duration": f"{result.duration:.1f}s",
            "project_dir": str(project_dir),
            "doc_type": doc_type,
        }
        # Include warnings if any
        if bib_issues:
            response["warnings"] = bib_issues
        if missing_deps:
            response["missing_optional_deps"] = missing_deps
        return json.dumps(response)
    else:
        # Parse errors from output
        all_output = f"{result.stdout}\n{result.stderr}"
        parsed_errors = _parse_latex_errors(all_output)

        # Add bibliography issues as potential causes
        all_issues = parsed_errors + bib_issues

        response = {
            "success": False,
            "error": result.error[:500] if result.error else "Compilation failed",
            "project_dir": str(project_dir),
            "doc_type": doc_type,
            "duration": f"{result.duration:.1f}s" if result.duration else None,
        }

        if all_issues:
            response["issues"] = all_issues
            # Generate summary suggestion
            if parsed_errors:
                response["suggestion"] = parsed_errors[0].get(
                    "suggestion", "Check the log file for details"
                )
            elif bib_issues:
                response["suggestion"] = bib_issues[0].get("suggestion")

        # Include raw output for debugging (truncated)
        if result.stderr:
            response["stderr_tail"] = result.stderr[-500:]

        return json.dumps(response)


__all__ = ["compile_handler"]

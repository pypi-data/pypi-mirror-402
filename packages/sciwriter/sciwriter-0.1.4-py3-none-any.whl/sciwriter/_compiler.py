"""Compiler wrapper for sciwriter.

Thin Python wrapper that delegates to make/shell scripts.
Projects remain self-contained - shell scripts work without Python.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

PathLike = Union[str, Path]


@dataclass
class CompileResult:
    """Result of a compilation operation."""

    success: bool
    output_path: Optional[Path] = None
    error: Optional[str] = None
    duration: float = 0.0
    stdout: str = ""
    stderr: str = ""


def check_dependencies() -> dict[str, bool]:
    """Check availability of required tools."""
    tools = {
        "make": "make",
        "pdflatex": "pdflatex",
        "bibtex": "bibtex",
        "latexmk": "latexmk",
        "latexdiff": "latexdiff",
        "tectonic": "tectonic",
    }

    result = {}
    for name, cmd in tools.items():
        result[name] = shutil.which(cmd) is not None

    return result


def get_project_info(project_dir: PathLike) -> dict:
    """Get information about a sciwriter project."""
    project_dir = Path(project_dir)
    info = {
        "path": str(project_dir),
        "has_manuscript": (project_dir / "01_manuscript").exists(),
        "has_supplementary": (project_dir / "02_supplementary").exists(),
        "has_revision": (project_dir / "03_revision").exists(),
        "has_makefile": (project_dir / "Makefile").exists(),
        "has_compile_script": (
            project_dir / "scripts" / "shell" / "compile.sh"
        ).exists(),
    }

    return info


def compile_document(
    doc_type: str,
    project_dir: PathLike,
    quiet: bool = False,
    verbose: bool = False,
    generate_diff: bool = True,
    crop_tif: bool = False,
    process_figures: bool = True,
    process_tables: bool = True,
    dark_mode: bool = False,
    draft: bool = False,
    timeout: int = 300,
    **kwargs,  # Ignore unknown options for forward compatibility
) -> CompileResult:
    """Compile a LaTeX document by delegating to make.

    Args:
        doc_type: Type of document (manuscript, supplementary, revision)
        project_dir: Path to the project directory
        quiet: Suppress output (-q)
        verbose: Show detailed output (-v)
        generate_diff: Generate diff document (default True, use -nd to skip)
        crop_tif: Crop TIF images (--crop-tif)
        process_figures: Process figures (default True, use -nf to skip)
        process_tables: Process tables (default True, use -nt to skip)
        dark_mode: Compile with dark theme (--dark-mode)
        draft: Single-pass compilation for speed (--draft)
        timeout: Maximum compilation time in seconds

    Returns:
        CompileResult with success status and output path
    """
    start_time = time.time()
    project_dir = Path(project_dir)

    # Validate doc_type
    valid_types = ["manuscript", "supplementary", "revision"]
    if doc_type not in valid_types:
        return CompileResult(
            success=False,
            error=f"Invalid doc_type: {doc_type}. Must be one of: {valid_types}",
        )

    # Check if project has Makefile
    makefile = project_dir / "Makefile"
    if not makefile.exists():
        return CompileResult(
            success=False,
            error=f"No Makefile found in {project_dir}. Is this a sciwriter project?",
        )

    # Build options string for OPTS variable
    opts = []
    if quiet:
        opts.append("-q")
    if verbose:
        opts.append("-v")
    if not generate_diff:
        opts.append("-nd")
    if not process_figures:
        opts.append("-nf")
    if not process_tables:
        opts.append("-nt")
    if draft:
        opts.append("--draft")
    if dark_mode:
        opts.append("--dark-mode")
    if crop_tif:
        opts.append("--crop-tif")

    opts_str = " ".join(opts)

    # Build make command
    cmd = ["make", doc_type]
    if opts_str:
        cmd.append(f"OPTS={opts_str}")

    try:
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "TERM": "dumb"},  # Disable colors for parsing
        )

        duration = time.time() - start_time

        # Determine output PDF path
        type_to_dir = {
            "manuscript": "01_manuscript",
            "supplementary": "02_supplementary",
            "revision": "03_revision",
        }
        pdf_path = project_dir / type_to_dir[doc_type] / f"{doc_type}.pdf"

        if result.returncode == 0 and pdf_path.exists():
            return CompileResult(
                success=True,
                output_path=pdf_path,
                duration=duration,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        else:
            error_msg = result.stderr or result.stdout or "Compilation failed"
            return CompileResult(
                success=False,
                error=error_msg[-1000:],  # Last 1000 chars
                duration=duration,
                stdout=result.stdout,
                stderr=result.stderr,
            )

    except subprocess.TimeoutExpired:
        return CompileResult(
            success=False,
            error=f"Compilation timed out after {timeout}s",
        )
    except Exception as e:
        return CompileResult(
            success=False,
            error=str(e),
        )


def compile_manuscript(project_dir: PathLike, **kwargs) -> CompileResult:
    """Compile the manuscript document."""
    return compile_document("manuscript", project_dir, **kwargs)


def compile_supplementary(project_dir: PathLike, **kwargs) -> CompileResult:
    """Compile the supplementary materials."""
    return compile_document("supplementary", project_dir, **kwargs)


def compile_revision(project_dir: PathLike, **kwargs) -> CompileResult:
    """Compile the revision response document."""
    return compile_document("revision", project_dir, **kwargs)


def clean_project(project_dir: PathLike) -> int:
    """Clean compilation artifacts by calling make clean."""
    project_dir = Path(project_dir)
    makefile = project_dir / "Makefile"

    if makefile.exists():
        result = subprocess.run(
            ["make", "clean"],
            cwd=project_dir,
            capture_output=True,
            timeout=30,
        )
        # Return a rough count (make clean doesn't report count)
        return 0 if result.returncode != 0 else 1

    # Fallback: manual cleanup if no Makefile
    patterns = [
        "*.aux",
        "*.bbl",
        "*.blg",
        "*.fdb_latexmk",
        "*.fls",
        "*.log",
        "*.out",
        "*.synctex.gz",
        "*.toc",
    ]

    cleaned = 0
    for pattern in patterns:
        for f in project_dir.rglob(pattern):
            try:
                f.unlink()
                cleaned += 1
            except OSError:
                pass

    return cleaned


def get_status(project_dir: PathLike) -> dict:
    """Get compilation status by calling make status."""
    project_dir = Path(project_dir)
    makefile = project_dir / "Makefile"

    status = {
        "manuscript": (project_dir / "01_manuscript" / "manuscript.pdf").exists(),
        "supplementary": (
            project_dir / "02_supplementary" / "supplementary.pdf"
        ).exists(),
        "revision": (project_dir / "03_revision" / "revision.pdf").exists(),
    }

    if makefile.exists():
        result = subprocess.run(
            ["make", "status"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        status["make_output"] = result.stdout

    return status


__all__ = [
    "CompileResult",
    "check_dependencies",
    "get_project_info",
    "compile_document",
    "compile_manuscript",
    "compile_supplementary",
    "compile_revision",
    "clean_project",
    "get_status",
]

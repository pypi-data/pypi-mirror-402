"""Version management and diff viewing for LaTeX documents.

Uses git for versioning - no separate version counter files needed.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

DOC_DIRS = {
    "manuscript": "01_manuscript",
    "supplementary": "02_supplementary",
    "revision": "03_revision",
}

DOC_FILES = {
    "manuscript": "manuscript.tex",
    "supplementary": "supplementary.tex",
    "revision": "revision.tex",
}


def _run_git(args: list[str], cwd: Path) -> tuple[bool, str]:
    """Run a git command and return (success, output)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, ""


def _is_git_repo(project_dir: Path) -> bool:
    """Check if project is a git repository."""
    success, _ = _run_git(["rev-parse", "--git-dir"], project_dir)
    return success


def list_versions(
    project_dir: Path,
    doc_type: str = "manuscript",
    limit: int = 20,
) -> list[dict]:
    """List git commits that modified the document.

    Args:
        project_dir: Path to the project directory
        doc_type: Document type (manuscript, supplementary, revision)
        limit: Maximum number of versions to return

    Returns:
        List of version info dicts with keys:
        - commit: Short commit hash
        - date: Commit date (ISO format)
        - author: Commit author
        - message: Commit message (first line)
        - is_head: True if this is the current HEAD
    """
    if not _is_git_repo(project_dir):
        return []

    doc_dir = DOC_DIRS.get(doc_type)
    if not doc_dir:
        return []

    # Get commits that touched this document directory
    # Format: hash|date|author|message
    format_str = "%h|%aI|%an|%s"
    doc_path = f"{doc_dir}/"

    success, output = _run_git(
        [
            "log",
            f"--pretty=format:{format_str}",
            f"-n{limit}",
            "--",
            doc_path,
        ],
        project_dir,
    )

    if not success or not output:
        return []

    # Get current HEAD for comparison
    _, head_hash = _run_git(["rev-parse", "--short", "HEAD"], project_dir)

    versions = []
    for line in output.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 3)
        if len(parts) >= 4:
            commit_hash = parts[0]
            versions.append(
                {
                    "commit": commit_hash,
                    "date": parts[1],
                    "author": parts[2],
                    "message": parts[3],
                    "is_head": commit_hash == head_hash,
                }
            )

    return versions


def view_diff(
    project_dir: Path,
    commit1: Optional[str] = None,
    commit2: Optional[str] = None,
    doc_type: str = "manuscript",
) -> Optional[str]:
    """View diff between document versions using git.

    Args:
        project_dir: Path to the project directory
        commit1: First commit hash (default: HEAD~1)
        commit2: Second commit hash (default: HEAD)
        doc_type: Document type

    Returns:
        Unified diff content or None if not available
    """
    if not _is_git_repo(project_dir):
        return None

    doc_dir = DOC_DIRS.get(doc_type)
    if not doc_dir:
        return None

    # Default to comparing HEAD~1 with HEAD
    if not commit1:
        commit1 = "HEAD~1"
    if not commit2:
        commit2 = "HEAD"

    # Get diff for the document directory
    doc_path = f"{doc_dir}/"

    success, output = _run_git(
        ["diff", "--unified=3", commit1, commit2, "--", doc_path],
        project_dir,
    )

    if not success:
        return None

    return output if output else "(no changes)"


def get_file_at_commit(
    project_dir: Path,
    commit: str,
    doc_type: str = "manuscript",
) -> Optional[str]:
    """Get the content of the main document file at a specific commit.

    Args:
        project_dir: Path to the project directory
        commit: Commit hash or ref (e.g., HEAD, HEAD~1, abc1234)
        doc_type: Document type

    Returns:
        File content at that commit, or None if not found
    """
    if not _is_git_repo(project_dir):
        return None

    doc_dir = DOC_DIRS.get(doc_type)
    doc_file = DOC_FILES.get(doc_type)
    if not doc_dir or not doc_file:
        return None

    file_path = f"{doc_dir}/{doc_file}"

    success, output = _run_git(
        ["show", f"{commit}:{file_path}"],
        project_dir,
    )

    return output if success else None


def get_current_commit(project_dir: Path) -> Optional[str]:
    """Get the current commit hash.

    Args:
        project_dir: Path to the project directory

    Returns:
        Short commit hash or None if not a git repo
    """
    success, output = _run_git(["rev-parse", "--short", "HEAD"], project_dir)
    return output if success else None


def get_commit_info(project_dir: Path, commit: str) -> Optional[dict]:
    """Get information about a specific commit.

    Args:
        project_dir: Path to the project directory
        commit: Commit hash or ref

    Returns:
        Dict with commit info or None if not found
    """
    format_str = "%h|%H|%aI|%an|%s"
    success, output = _run_git(
        ["log", "-1", f"--pretty=format:{format_str}", commit],
        project_dir,
    )

    if not success or not output:
        return None

    parts = output.split("|", 4)
    if len(parts) >= 5:
        return {
            "short_hash": parts[0],
            "full_hash": parts[1],
            "date": parts[2],
            "author": parts[3],
            "message": parts[4],
        }

    return None


__all__ = [
    "list_versions",
    "view_diff",
    "get_file_at_commit",
    "get_current_commit",
    "get_commit_info",
]

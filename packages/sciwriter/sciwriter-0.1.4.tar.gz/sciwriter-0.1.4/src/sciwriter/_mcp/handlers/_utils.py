"""Shared utilities for MCP handlers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def resolve_project(project: str) -> Path | None:
    """Resolve project path or name to Path."""
    path = Path(project)
    if path.exists():
        return path

    from sciwriter._project import resolve_project as _resolve

    return _resolve(project)


def run_cli(args: list[str], timeout: int = 300) -> tuple[bool, str, str]:
    """Run sciwriter CLI command and return (success, stdout, stderr)."""
    cmd = [sys.executable, "-m", "sciwriter._cli"] + args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return (
            result.returncode == 0,
            result.stdout,
            result.stderr,
        )
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return False, "", str(e)

"""Project management for sciwriter.

Internal module - not part of public API.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

# Registry location
_REGISTRY_DIR = Path.home() / ".sciwriter"
_REGISTRY_FILE = _REGISTRY_DIR / "projects.json"

# Template location (bundled zip)
_TEMPLATE_ZIP = Path(__file__).parent / "templates" / "project.zip"


@dataclass
class _Project:
    """Internal: Represents a sciwriter project."""

    name: str
    path: str
    description: str = ""
    created_at: str = ""
    is_active: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "_Project":
        return cls(**data)


class _Registry:
    """Internal: Manages project registry."""

    def __init__(self):
        _REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
        self._projects: dict[str, _Project] = {}
        self._load()

    def _load(self):
        if _REGISTRY_FILE.exists():
            try:
                data = json.loads(_REGISTRY_FILE.read_text())
                self._projects = {
                    name: _Project.from_dict(proj) for name, proj in data.items()
                }
            except (json.JSONDecodeError, KeyError):
                self._projects = {}

    def _save(self):
        data = {name: proj.to_dict() for name, proj in self._projects.items()}
        _REGISTRY_FILE.write_text(json.dumps(data, indent=2))

    def register(self, name: str, path: Path, description: str = "") -> None:
        from datetime import datetime

        self._projects[name] = _Project(
            name=name,
            path=str(path.resolve()),
            description=description,
            created_at=datetime.now().isoformat(),
            is_active=False,
        )
        self._save()

    def unregister(self, name: str) -> bool:
        if name in self._projects:
            del self._projects[name]
            self._save()
            return True
        return False

    def get(self, name: str) -> Optional[_Project]:
        return self._projects.get(name)

    def list(self) -> list[dict]:
        """Return projects as simple dicts (not exposing internal class)."""
        return [p.to_dict() for p in self._projects.values()]

    def set_active(self, name: str) -> bool:
        if name not in self._projects:
            return False
        for proj in self._projects.values():
            proj.is_active = False
        self._projects[name].is_active = True
        self._save()
        return True

    def get_active(self) -> Optional[_Project]:
        for proj in self._projects.values():
            if proj.is_active:
                return proj
        return None


# =============================================================================
# Public Functions
# =============================================================================


def init_project(
    name: str,
    target_dir: Optional[Path] = None,
    description: str = "",
) -> tuple[bool, str, Optional[Path]]:
    """Initialize a new sciwriter project from bundled template.

    Args:
        name: Project name (used as directory name)
        target_dir: Parent directory (defaults to current directory)
        description: Optional project description

    Returns:
        Tuple of (success, message, project_path)
    """
    # Determine target
    if target_dir is None:
        project_path = Path.cwd() / name
    else:
        project_path = Path(target_dir) / name

    if project_path.exists():
        return False, f"Directory already exists: {project_path}", None

    # Check template exists
    if not _TEMPLATE_ZIP.exists():
        return False, f"Template not found: {_TEMPLATE_ZIP}", None

    try:
        # Extract template with permission preservation
        with zipfile.ZipFile(_TEMPLATE_ZIP, "r") as zf:
            zf.extractall(project_path)
            # Restore Unix permissions from ZIP external_attr
            for info in zf.infolist():
                extracted_path = project_path / info.filename
                if extracted_path.exists() and info.external_attr:
                    # High 16 bits contain Unix permissions
                    unix_mode = info.external_attr >> 16
                    if unix_mode:
                        os.chmod(extracted_path, unix_mode)

        # Initialize git
        subprocess.run(
            ["git", "init"],
            cwd=project_path,
            capture_output=True,
            timeout=30,
        )

        # Reset version counters to ensure fresh start
        for doc_dir in ["01_manuscript", "02_supplementary", "03_revision"]:
            counter_file = project_path / doc_dir / "archive" / ".version_counter.txt"
            counter_file.parent.mkdir(parents=True, exist_ok=True)
            counter_file.write_text("000\n")

        # Register
        registry = _Registry()
        registry.register(name, project_path, description)
        registry.set_active(name)

        return True, f"Project created: {project_path}", project_path

    except Exception as e:
        # Cleanup on failure
        if project_path.exists():
            shutil.rmtree(project_path, ignore_errors=True)
        return False, f"Error: {e}", None


def list_projects() -> list[dict]:
    """List all registered projects.

    Returns:
        List of project info dicts with keys: name, path, description, is_active
    """
    return _Registry().list()


def get_active_project_dir() -> Optional[Path]:
    """Get path to the currently active project."""
    project = _Registry().get_active()
    if project:
        return Path(project.path)
    return None


def unregister_project(name: str) -> tuple[bool, str]:
    """Remove a project from the registry (does not delete files).

    Args:
        name: Project name to unregister

    Returns:
        Tuple of (success, message)
    """
    if _Registry().unregister(name):
        return True, f"Unregistered: {name}"
    return False, f"Project not found: {name}"


def get_project_path(name: str) -> Optional[Path]:
    """Get path for a registered project by name.

    Args:
        name: Project name to look up

    Returns:
        Path to project directory, or None if not found
    """
    project = _Registry().get(name)
    if project:
        path = Path(project.path)
        if path.exists():
            return path
    return None


def resolve_project(value: str) -> Optional[Path]:
    """Resolve a project reference to a path.

    Accepts either:
    - A path (absolute or relative, e.g., '.', './my-paper', '/path/to/project')
    - A registered project name

    Args:
        value: Path string or project name

    Returns:
        Resolved Path, or None if not found
    """
    # First, try as a path
    path = Path(value).resolve()
    if path.exists() and path.is_dir():
        return path

    # Try as a registered project name
    return get_project_path(value)

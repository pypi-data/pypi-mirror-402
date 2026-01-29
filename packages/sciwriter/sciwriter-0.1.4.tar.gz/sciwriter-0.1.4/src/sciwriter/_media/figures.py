"""Figure management for sciwriter LaTeX documents.

CRUD operations for figures: list, get, create, update, delete.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from ._utils import DOC_DIRS, parse_caption_file

PathLike = Union[str, Path]


@dataclass
class FigureInfo:
    """Information about a figure."""

    id: str  # e.g., "01_example_figure"
    label: str  # e.g., "fig:example_figure_01"
    caption: str
    caption_file: Path
    media_files: list[Path] = field(default_factory=list)
    compiled_file: Optional[Path] = None
    panels: list[str] = field(default_factory=list)  # e.g., ["a", "b", "c"]


def _get_figures_dir(project_dir: PathLike, doc_type: str) -> Optional[Path]:
    """Get the figures directory."""
    project_dir = Path(project_dir)
    doc_dir = DOC_DIRS.get(doc_type)
    if not doc_dir:
        return None
    return project_dir / doc_dir / "contents" / "figures"


def _find_media_files(
    caption_media_dir: Path, base_id: str, extensions: tuple[str, ...]
) -> tuple[list[Path], list[str]]:
    """Find media files matching a base ID."""
    media_files = []
    panels = []

    if not caption_media_dir.exists():
        return media_files, panels

    base_num = base_id.split("_")[0]

    for ext in extensions:
        direct = caption_media_dir / f"{base_id}{ext}"
        if direct.exists():
            media_files.append(direct)

        for f in caption_media_dir.glob(f"{base_num}[a-zA-Z]_*{ext}"):
            if f not in media_files:
                media_files.append(f)
                panel_match = re.match(rf"{base_num}([a-zA-Z])_", f.name)
                if panel_match:
                    panel = panel_match.group(1).lower()
                    if panel not in panels:
                        panels.append(panel)

    panels.sort()
    return media_files, panels


def list_figures(
    project_dir: PathLike,
    doc_type: str = "manuscript",
) -> list[FigureInfo]:
    """List all figures in a document."""
    figures_dir = _get_figures_dir(project_dir, doc_type)
    if not figures_dir:
        return []

    caption_media_dir = figures_dir / "caption_and_media"
    compiled_dir = figures_dir / "compiled"
    jpg_dir = caption_media_dir / "jpg_for_compilation"

    if not caption_media_dir.exists():
        return []

    figures = []
    image_extensions = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".pdf", ".svg")

    for caption_file in sorted(caption_media_dir.glob("[0-9][0-9]_*.tex")):
        base_id = caption_file.stem
        caption, label = parse_caption_file(caption_file)
        media_files, panels = _find_media_files(
            caption_media_dir, base_id, image_extensions
        )

        if jpg_dir.exists():
            for ext in (".jpg", ".jpeg"):
                jpg_file = jpg_dir / f"{base_id}{ext}"
                if jpg_file.exists() and jpg_file not in media_files:
                    media_files.append(jpg_file)

        compiled_file = None
        if compiled_dir.exists():
            compiled_tex = compiled_dir / f"{base_id}.tex"
            if compiled_tex.exists():
                compiled_file = compiled_tex

        figures.append(
            FigureInfo(
                id=base_id,
                label=label,
                caption=caption,
                caption_file=caption_file,
                media_files=media_files,
                compiled_file=compiled_file,
                panels=panels,
            )
        )

    return figures


def get_figure(
    project_dir: PathLike,
    figure_id: str,
    doc_type: str = "manuscript",
) -> Optional[FigureInfo]:
    """Get information about a specific figure."""
    figures = list_figures(project_dir, doc_type)

    for fig in figures:
        if fig.id == figure_id or fig.id.startswith(f"{figure_id}_"):
            return fig

    return None


def create_figure(
    project_dir: PathLike,
    figure_id: str,
    caption: str,
    doc_type: str = "manuscript",
    image_path: Optional[PathLike] = None,
) -> Optional[FigureInfo]:
    """Create a new figure with caption and optional image.

    Args:
        project_dir: Project directory path
        figure_id: Figure identifier (e.g., '01_overview')
        caption: Figure caption text
        doc_type: Document type
        image_path: Optional path to image file (PNG, PDF, TIF, etc.) to copy
    """

    figures_dir = _get_figures_dir(project_dir, doc_type)
    if not figures_dir:
        return None

    caption_media_dir = figures_dir / "caption_and_media"
    caption_media_dir.mkdir(parents=True, exist_ok=True)

    caption_file = caption_media_dir / f"{figure_id}.tex"
    if caption_file.exists():
        return None

    name_part = "_".join(figure_id.split("_")[1:])
    num_part = figure_id.split("_")[0]
    label = f"fig:{name_part}_{num_part}"

    content = f"""%% -*- coding: utf-8 -*-
\\caption{{{caption}}}
\\label{{{label}}}
%%%% EOF"""

    caption_file.write_text(content, encoding="utf-8")

    # Symlink image if provided
    media_files = []
    if image_path:
        image_source = Path(image_path).resolve()
        if image_source.exists():
            # Use figure_id as base name, keep original extension
            dest_file = caption_media_dir / f"{figure_id}{image_source.suffix}"
            if dest_file.exists():
                dest_file.unlink()
            dest_file.symlink_to(image_source)
            media_files.append(dest_file)

    return FigureInfo(
        id=figure_id,
        label=label,
        caption=caption,
        caption_file=caption_file,
        media_files=media_files,
        panels=[],
    )


def update_figure(
    project_dir: PathLike,
    figure_id: str,
    caption: str,
    doc_type: str = "manuscript",
) -> bool:
    """Update a figure's caption."""
    fig = get_figure(project_dir, figure_id, doc_type)
    if not fig or not fig.caption_file.exists():
        return False

    content = fig.caption_file.read_text(encoding="utf-8")
    new_content = re.sub(
        r"\\caption\{[^}]*\}",
        f"\\\\caption{{{caption}}}",
        content,
    )
    fig.caption_file.write_text(new_content, encoding="utf-8")
    return True


def delete_figure(
    project_dir: PathLike,
    figure_id: str,
    doc_type: str = "manuscript",
) -> bool:
    """Delete a figure and its associated files."""
    fig = get_figure(project_dir, figure_id, doc_type)
    if not fig:
        return False

    if fig.caption_file.exists():
        fig.caption_file.unlink()

    for media_file in fig.media_files:
        if media_file.exists():
            media_file.unlink()

    if fig.compiled_file and fig.compiled_file.exists():
        fig.compiled_file.unlink()

    return True


__all__ = [
    "FigureInfo",
    "list_figures",
    "get_figure",
    "create_figure",
    "update_figure",
    "delete_figure",
]

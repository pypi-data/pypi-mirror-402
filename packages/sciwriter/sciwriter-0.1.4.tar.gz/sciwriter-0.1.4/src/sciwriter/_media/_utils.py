"""Shared utilities for media management."""

from __future__ import annotations

import re
from pathlib import Path

# Directory mappings
DOC_DIRS = {
    "manuscript": "01_manuscript",
    "supplementary": "02_supplementary",
    "revision": "03_revision",
}


def parse_caption_file(caption_file: Path) -> tuple[str, str]:
    """Parse a caption file to extract caption and label.

    Returns:
        Tuple of (caption_text, label)
    """
    if not caption_file.exists():
        return "", ""

    content = caption_file.read_text(encoding="utf-8")

    # Extract caption
    caption_match = re.search(r"\\caption\{(.+?)\}(?:\s*%|$)", content, re.DOTALL)
    caption = ""
    if caption_match:
        caption = caption_match.group(1).strip()
        # Clean up LaTeX formatting for display
        caption = re.sub(r"\\textbf\{([^}]*)\}", r"\1", caption)
        caption = re.sub(r"\\smallskip\s*\\\\", " ", caption)
        caption = re.sub(r"\s+", " ", caption).strip()

    # Extract label
    label_match = re.search(r"\\label\{([^}]+)\}", content)
    label = label_match.group(1) if label_match else ""

    return caption, label

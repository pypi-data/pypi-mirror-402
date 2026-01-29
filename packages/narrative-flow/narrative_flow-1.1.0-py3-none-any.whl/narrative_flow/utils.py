"""Utility helpers for narrative_flow."""

from __future__ import annotations

import os
import re


def sanitize_filename_component(value: str) -> str:
    """Sanitize a filename component for safe filesystem usage.

    Args:
        value: Raw value to sanitize.

    Returns:
        A safe filename component string.
    """
    cleaned = value.replace(os.sep, "_")
    if os.altsep:
        cleaned = cleaned.replace(os.altsep, "_")
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", cleaned)
    cleaned = re.sub(r"\.{2,}", ".", cleaned).strip("._")
    return cleaned or "workflow"

"""
Replace this file with your actual image generation implementation.

Contract:
    generate_image_bytes(prompt) -> (raw_bytes, mime_type, width, height)

This file is intentionally isolated so the rest of the bridge system stays the same.
"""

from __future__ import annotations


def generate_image_bytes(prompt: str) -> tuple[bytes, str, int | None, int | None]:
    raise NotImplementedError(
        "Implement generate_image_bytes(prompt) in backend/providers/generator.py"
    )

"""
Replace this file with your actual image generation implementation.

Contract:
    generate_image_bytes(prompt) -> (raw_bytes, mime_type, width, height)

This file is intentionally isolated so the rest of the bridge system stays the same.
"""

from __future__ import annotations


def generate_image_bytes(prompt: str) -> tuple[bytes, str, int | None, int | None]:
    """
    Demo generator that returns a small gray placeholder image.
    In production, replace this with a real AI image provider (e.g., DALL-E, Stability).
    """
    # A tiny 1x1 gray pixel PNG for demo purposes
    # Source: https://stackoverflow.com/questions/60186637/how-to-create-a-1x1-pixel-png-image-using-python
    import base64
    placeholder_png = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
        b'\x00\x00\x00\nIDATx\x9cc\xaa\xa8\xa8\x00\x00\x01\x02\x00\x01E\x02\x05\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return placeholder_png, "image/png", 1, 1

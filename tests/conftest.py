"""Shared fixtures for real (no-mock) tests -- matching private-agent's
own tests/ convention of testing against the real on-device model rather
than a stub."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _skip_if_apple_intelligence_unavailable():
    """Vision extraction doesn't need Apple Intelligence, but narration
    (backend.describe()) hands Vision's output to the on-device Foundation
    Model -- skip on a machine where it isn't available/enabled rather than
    failing with a confusing error, matching private-agent's own skip
    fixture."""
    from langchain_apple_foundation_models import ChatAppleFoundationModels

    try:
        ChatAppleFoundationModels()
    except Exception as e:
        pytest.skip(f"Apple Foundation Models not available: {e}")


@pytest.fixture
def text_image_path(tmp_path: Path) -> str:
    """A real, deterministic PNG with known text rendered into it, for a
    genuine (not mocked, not ambient-screen-dependent) OCR test.

    Uses Pillow rather than Quartz/CoreText directly -- simpler to get right
    for "draw one line of text," and this is test-only tooling, not part of
    the shipped package (see pyproject.toml's dev extra)."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (600, 200), color="white")
    draw = ImageDraw.Draw(img)
    # Default bitmap font is small but Vision's OCR handles it fine at this
    # size/contrast -- no need to hunt for a specific system font file.
    draw.text((20, 80), "LANTERN TEST STRING 4471", fill="black")

    out_path = tmp_path / "ocr_test.png"
    img.save(out_path)
    return str(out_path)


@pytest.fixture
def blank_image_path(tmp_path: Path) -> str:
    """A real, genuinely blank image -- for testing the 'nothing
    recognizable' path honestly, not just the happy path."""
    from PIL import Image

    img = Image.new("RGB", (600, 200), color="white")
    out_path = tmp_path / "blank.png"
    img.save(out_path)
    return str(out_path)

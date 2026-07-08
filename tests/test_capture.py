"""Real (no-mock) tests for capture.py's screen capture path.

Camera capture isn't tested here -- it needs a physical camera and an
interactive one-time permission grant (System Settings > Privacy & Security
> Camera) that can't be driven from an automated test run. It's exercised
manually via `lantern camera` instead; see README's testing section."""

import os

from lantern.capture import capture_screen


def test_capture_screen_produces_real_image():
    path = capture_screen()
    try:
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        with open(path, "rb") as f:
            header = f.read(8)
        # Real PNG magic bytes -- confirms this is an actual image file,
        # not just an empty/placeholder path.
        assert header[:4] == b"\x89PNG"
    finally:
        os.remove(path)

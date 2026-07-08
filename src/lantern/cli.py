"""Simple CLI entrypoint for testing lantern without the menu bar shell."""

import os
import sys

from lantern.backends import active_backend_name, get_backend
from lantern.capture import capture_camera, capture_screen
from lantern.speech import speak


def main() -> None:
    args = sys.argv[1:]
    source = args[0] if args else "screen"
    if source not in ("screen", "camera"):
        print("Usage: lantern [screen|camera]")
        sys.exit(1)

    image_path = capture_screen() if source == "screen" else capture_camera()
    try:
        backend = get_backend()
        description = backend.describe(image_path)
    finally:
        # The captured frame (a photo of the user, for `camera`, or
        # whatever's on their screen) has no reason to exist on disk once
        # it's been described -- delete it even if describe() raises,
        # rather than leaving a capture behind on every run.
        os.remove(image_path)

    print(f"[{active_backend_name()}] {description}")
    speak(description)


if __name__ == "__main__":
    main()

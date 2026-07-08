"""Simple CLI entrypoint for testing lantern without the menu bar shell."""

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
    backend = get_backend()
    description = backend.describe(image_path)

    print(f"[{active_backend_name()}] {description}")
    speak(description)


if __name__ == "__main__":
    main()

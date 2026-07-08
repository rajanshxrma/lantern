"""Menu bar shell for lantern, via rumps -- matching private-agent's own
menubar.py shape (same framework, same "menu items call straight into the
plain functions, no extra indirection" pattern)."""

from __future__ import annotations

import os

import rumps

from lantern.backends import active_backend_name, get_backend
from lantern.capture import CaptureError, capture_camera, capture_screen
from lantern.speech import speak


class LanternApp(rumps.App):
    def __init__(self):
        super().__init__("lantern", title="\U0001f3ee")  # lantern emoji as the menu bar glyph

    @rumps.clicked("Describe screen")
    def describe_screen(self, _):
        self._describe(capture_screen)

    @rumps.clicked("Describe camera")
    def describe_camera(self, _):
        self._describe(capture_camera)

    def _describe(self, capture_fn):
        try:
            image_path = capture_fn()
        except CaptureError as e:
            rumps.notification("lantern", "Capture failed", str(e))
            return

        try:
            backend = get_backend()
            description = backend.describe(image_path)
        finally:
            # Same reasoning as cli.py: nothing captured should outlive its
            # own description, on disk, on every single run.
            os.remove(image_path)

        rumps.notification(f"lantern ({active_backend_name()})", "", description)
        speak(description)


def main() -> None:
    LanternApp().run()


if __name__ == "__main__":
    main()

"""Real evals for lantern: latency and narration accuracy for the vision
backend, on a fixed set of generated test images -- no mocks, matching
private-agent's own eval_agent.py discipline (real prompts/real model, real
measured numbers, nothing invented for the README).

Native backend isn't included here -- it's unimplemented until the beta
SDK's real image-input API is verified (see backends.py). This script
reports "vision" results only and says so explicitly in its output, so a
README table built from this never silently implies a native-path number
that was never actually measured.

Usage: python3 scripts/eval_lantern.py
"""

import statistics
import time

from PIL import Image, ImageDraw

from lantern.backends import VisionOCRBackend, active_backend_name

# Fixed, deterministic test set -- regenerated each run rather than checked
# into the repo as binary fixtures, so there's nothing stale to go out of
# sync with what the eval actually measures.
CASES = [
    ("single word", "CALENDAR"),
    ("short phrase", "MEETING AT 3PM ROOM 204"),
    ("longer line", "PLEASE SIGN IN AT THE FRONT DESK BEFORE ENTERING"),
]


def _make_test_image(text: str, path: str) -> str:
    img = Image.new("RGB", (700, 200), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 80), text, fill="black")
    img.save(path)
    return path


def _make_blank_image(path: str) -> str:
    Image.new("RGB", (700, 200), color="white").save(path)
    return path


def run() -> None:
    backend_name = active_backend_name()
    print(f"lantern eval -- backend: {backend_name}\n")
    if backend_name != "vision":
        print("(unexpected: native backend is unimplemented, this script assumes 'vision')")

    backend = VisionOCRBackend()
    latencies = []
    hits = 0

    for label, text in CASES:
        path = _make_test_image(text, f"/tmp/lantern_eval_{label.replace(' ', '_')}.png")
        start = time.monotonic()
        description = backend.describe(path)
        elapsed = time.monotonic() - start
        latencies.append(elapsed)

        # Loose containment check against the actual rendered text, same
        # reasoning as the test suite: the model paraphrases, so this checks
        # real engagement with what Vision extracted, not exact wording.
        recognized = any(word.upper() in description.upper() for word in text.split() if len(word) > 3)
        hits += int(recognized)
        print(f"[{label}] {elapsed:.2f}s -- recognized key content: {recognized}")
        print(f"  text: {text!r}")
        print(f"  narration: {description}\n")

    blank_path = _make_blank_image("/tmp/lantern_eval_blank.png")
    start = time.monotonic()
    blank_description = backend.describe(blank_path)
    blank_elapsed = time.monotonic() - start
    print(f"[blank image] {blank_elapsed:.2f}s")
    print(f"  narration: {blank_description}\n")

    print("--- summary (measured, this run, this machine) ---")
    print(f"backend: {backend_name}")
    print(f"text cases: {hits}/{len(CASES)} recognized key content")
    print(f"latency -- median: {statistics.median(latencies):.2f}s, "
          f"mean: {statistics.mean(latencies):.2f}s, "
          f"range: {min(latencies):.2f}s-{max(latencies):.2f}s")
    print(f"blank-image latency: {blank_elapsed:.2f}s")


if __name__ == "__main__":
    run()

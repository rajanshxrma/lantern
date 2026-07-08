"""Image-description backends for lantern.

Two backends, chosen automatically at runtime, not configured by hand:

- "native": Apple's on-device Foundation Model given the image directly, via
  the image-input surface previewed at WWDC26. Only exists on a beta OS/SDK
  (verified: the stable macOS 26.6 / Xcode 26.6 FoundationModels interface
  has zero image-bearing symbols -- CoreGraphics is imported but nothing in
  it is actually used). NativeImageBackend probes for the real API at call
  time rather than gating on an OS-version check, since beta point releases
  can change a symbol's shape between releases -- a version check would
  either false-negative on a beta that has it, or false-positive on one that
  changed the signature underneath it.
- "vision": Apple's Vision framework (stable, mature, shipped for years) for
  OCR (VNRecognizeTextRequest) and scene/object classification
  (VNClassifyImageRequest), with the extracted text/labels handed to the
  same on-device Foundation Model for narration -- the model never sees
  pixels in this path, only Vision's structured output. This is the backend
  every clone of this repo actually gets, beta or not.

get_backend() always tries native first and falls back to vision -- never
raises for "no native backend", since not having the beta is the normal
case, not an error.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol


class Backend(Protocol):
    def describe(self, image_path: str) -> str: ...


_NARRATION_INSTRUCTIONS = (
    "You describe images for a low-vision user, out loud. You are given only "
    "text and scene labels extracted by a computer vision system -- you have "
    "not seen the actual image. Report ONLY what's in that extracted data. "
    "Never add visual details, objects, colors, layout, or context that "
    "weren't explicitly given to you, even if they'd be a plausible guess -- "
    "a plausible-sounding invented detail is worse than no detail, because "
    "the user can't verify it themselves. If a word or label is evocative "
    "(e.g. the text 'CALENDAR' by itself), describe only that the word/label "
    "was detected -- do not imagine what a calendar in the scene might look "
    "like. One or two plain sentences, present tense, no hedging, no "
    "meta-commentary about being an AI."
)


class NativeImageBackend:
    """Feeds the image directly to Apple's on-device model.

    Only constructible if the real API is present -- see `_probe_native()`.
    Left unimplemented in detail until the beta SDK's actual API shape is
    verified directly (the same way the stable SDK's *absence* of it was
    verified) rather than written against the ideas doc's description of
    what WWDC26 previewed, which is not the same thing as what a beta build
    actually ships.
    """

    def __init__(self):
        raise NotImplementedError(
            "NativeImageBackend is not implemented yet -- pending direct "
            "verification of the real image-input API against an installed "
            "beta SDK. See backends.py module docstring and the project "
            "README's status section."
        )

    def describe(self, image_path: str) -> str:  # pragma: no cover
        raise NotImplementedError


class VisionOCRBackend:
    """Vision framework OCR + classification, narrated by the on-device model."""

    def __init__(self, instructions: str | None = None):
        from langchain_apple_foundation_models import ChatAppleFoundationModels

        self._llm = ChatAppleFoundationModels(instructions=instructions or _NARRATION_INSTRUCTIONS)

    def _extract(self, image_path: str) -> tuple[list[str], list[str]]:
        """Runs Vision's OCR + classification requests against the image.

        Returns (recognized_text_lines, top_classification_labels). Both can
        be empty -- a photo of a blank wall has no text and no confident
        classification, and that's a real, valid result, not an error.
        """
        import Quartz
        import Vision
        from Foundation import NSURL

        image_url = NSURL.fileURLWithPath_(image_path)
        handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(image_url, None)

        text_request = Vision.VNRecognizeTextRequest.alloc().init()
        text_request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)

        classify_request = Vision.VNClassifyImageRequest.alloc().init()

        success, error = handler.performRequests_error_([text_request, classify_request], None)
        if not success:
            raise RuntimeError(f"Vision request failed: {error}")

        text_lines = []
        for obs in text_request.results() or []:
            candidates = obs.topCandidates_(1)
            if candidates:
                text_lines.append(str(candidates[0].string()))

        # Classification observations are sorted by confidence; keep only
        # ones Vision itself is reasonably sure about, not the long tail.
        labels = [
            str(obs.identifier())
            for obs in (classify_request.results() or [])
            if obs.confidence() >= 0.3
        ][:5]

        return text_lines, labels

    def describe(self, image_path: str) -> str:
        text_lines, labels = self._extract(image_path)
        if not text_lines and not labels:
            return "Nothing recognizable in view -- no text and no confident scene labels."

        parts = []
        if labels:
            parts.append("Scene labels (Vision, most confident first): " + ", ".join(labels))
        if text_lines:
            parts.append("Text visible in the image: " + " / ".join(text_lines))
        context = "\n".join(parts)

        prompt = (
            f"{context}\n\nNarrate ONLY the above for someone who can't see it "
            "themselves. Do not add anything not listed above."
        )
        result = self._llm.invoke(prompt)
        return result.content


def _probe_native() -> bool:
    """True only if the real native image-input surface is actually present.

    Deliberately a runtime probe (import + attribute check), not an OS
    version check -- see NativeImageBackend's docstring for why."""
    try:
        import FoundationModels  # noqa: F401
    except ImportError:
        return False
    # Placeholder condition -- always False until NativeImageBackend is
    # actually implemented against a verified beta API (task: verify beta
    # SDK). Left as an explicit, named check rather than a bare `return
    # False` so it's obvious this is the one line to change once that
    # verification happens.
    return False


@lru_cache(maxsize=None)
def _cached_vision_backend() -> VisionOCRBackend:
    return VisionOCRBackend()


def get_backend() -> Backend:
    if _probe_native():
        return NativeImageBackend()  # pragma: no cover -- unreachable until implemented
    return _cached_vision_backend()


def active_backend_name() -> str:
    """Which backend get_backend() will actually return right now -- for
    the menu bar / CLI to show the user, and for the eval script to label
    its results honestly rather than assuming."""
    return "native" if _probe_native() else "vision"

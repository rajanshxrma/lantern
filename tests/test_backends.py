"""Real (no-mock) tests for backends.py -- against actual Vision framework
calls and the actual on-device model, matching private-agent/orchard's own
"no mocks" test philosophy."""


def test_vision_backend_reads_real_text(text_image_path):
    from lantern.backends import VisionOCRBackend

    backend = VisionOCRBackend()
    text_lines, labels = backend._extract(text_image_path)
    # "contains", not exact match -- Vision's OCR can return the string with
    # different casing/spacing than what Pillow rendered, and this test
    # cares whether OCR actually recognized the content, not byte-exact
    # reproduction (same lesson as private-agent's reminder test).
    joined = " ".join(text_lines).upper()
    assert "LANTERN" in joined
    assert "4471" in joined


def test_vision_backend_handles_blank_image_honestly(blank_image_path):
    from lantern.backends import VisionOCRBackend

    backend = VisionOCRBackend()
    text_lines, labels = backend._extract(blank_image_path)
    assert text_lines == []
    # A blank white image may still get a low-confidence classification
    # label or two from Vision -- the 0.3 confidence floor in _extract is
    # what actually matters here, not that labels is necessarily empty.


def test_describe_narrates_real_text(text_image_path):
    from lantern.backends import VisionOCRBackend

    backend = VisionOCRBackend()
    description = backend.describe(text_image_path)
    assert len(description) > 0
    # Loose check on content, not exact wording -- the model paraphrases;
    # what matters is it actually engaged with what Vision extracted rather
    # than returning something generic.
    assert "4471" in description or "lantern" in description.lower()


def test_describe_handles_nothing_recognizable(blank_image_path):
    from lantern.backends import VisionOCRBackend

    backend = VisionOCRBackend()
    description = backend.describe(blank_image_path)
    assert len(description) > 0


def test_active_backend_name_reflects_reality():
    from lantern.backends import active_backend_name

    # NativeImageBackend is intentionally unimplemented (see backends.py) --
    # this must report "vision" honestly, never claim "native" for a path
    # that doesn't actually work yet.
    assert active_backend_name() == "vision"


def test_get_backend_returns_working_backend():
    from lantern.backends import get_backend

    backend = get_backend()
    assert hasattr(backend, "describe")

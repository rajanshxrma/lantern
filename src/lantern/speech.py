"""On-device speech output via AVSpeechSynthesizer.

Note: AVSpeechSynthesizer lives in AVFoundation, not the separate Speech
framework -- Speech.framework is for speech *recognition* (audio to text),
the opposite direction from what lantern needs here. Easy mix-up; worth
stating explicitly since it's the kind of thing that looks right in an
import list without actually working.
"""

from __future__ import annotations

import time


def speak(text: str, rate: float | None = None) -> None:
    """Speaks `text` out loud via the system voice, on-device, blocking
    until speech finishes.

    `rate` is AVSpeechUtterance's 0.0-1.0 rate scale if given; None uses the
    system default rate.
    """
    import AVFoundation

    synthesizer = AVFoundation.AVSpeechSynthesizer.alloc().init()
    utterance = AVFoundation.AVSpeechUtterance.speechUtteranceWithString_(text)
    if rate is not None:
        utterance.setRate_(rate)

    synthesizer.speakUtterance_(utterance)
    # speakUtterance_ is fire-and-forget; poll isSpeaking rather than block
    # on a delegate callback, matching capture.py's "simple beats proper
    # async plumbing for a one-shot CLI-style call" choice.
    while synthesizer.isSpeaking():
        time.sleep(0.1)

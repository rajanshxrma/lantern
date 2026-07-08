# lantern

An on-device accessibility agent for macOS. Describes what's on your screen or in front of your camera, out loud -- entirely offline.

![demo](assets/demo.gif)

Runs on Apple's Vision framework plus the on-device Foundation Model via [langchain-apple-foundation-models](https://github.com/rajanshxrma/langchain-apple-foundation-models) -- no API key, no network call, nothing leaves the machine.

## Install

```
pip install -e .
lantern screen    # describes the current screen, out loud
lantern camera    # describes what the camera sees, out loud
```

Or run it as a menu bar app:

```
lantern-menubar
```

First run of `lantern screen`/`lantern camera` triggers macOS's one-time permission prompts (Screen Recording, Camera) -- grant them once, they stick. `lantern camera` briefly lights up the camera indicator for each capture, same as any app taking a photo.

Requires macOS 26+, Apple Silicon.

## How it works

Two backends, chosen automatically -- never configured by hand:

| | Native | Vision (what you actually get today) |
|---|---|---|
| **Requires** | A beta OS/SDK (WWDC26 previewed native image input to Apple's on-device model; the stable SDK doesn't have it yet -- verified directly against the real `FoundationModels` interface, not assumed) | Nothing beyond stable macOS 26+ |
| **How it sees** | The model reasons over the image directly | `VNRecognizeTextRequest` (OCR) + `VNClassifyImageRequest` (scene/object labels) extract structured data; the on-device model narrates *only* from that -- it never sees pixels |
| **Status** | Not yet implemented -- deliberately stubbed in `backends.py` until the real beta API is verified directly, the same way its absence from the stable SDK was verified, rather than built against a planning doc's description of what a beta *might* ship | Fully working, tested, benchmarked below |

`get_backend()` probes for the native API at runtime and falls back automatically -- this repo runs and demos correctly on stable macOS whether or not the native path ever lands, and picking up native support later is a change to one backend, not a rewrite.

## A real bug found during eval (and fixed)

Early testing found the narration step inventing plausible-sounding but entirely fictional detail: given an image containing only the word "CALENDAR" on a blank background, the model's first-draft narration was *"a calendar with multiple months visible, with dates present on each month page"* -- a fully invented scene. Vision's own extraction was correct (just the text "CALENDAR", no scene labels); the hallucination was purely in the narration prompt letting the model fill in a plausible-sounding scene from one evocative word.

This matters more here than in a general chatbot: someone using this *can't see the image themselves* to catch the error. Fixed by rewriting the narration instructions to explicitly forbid adding anything not in Vision's actual extracted output. Re-verified: the same input now correctly narrates only *"CALENDAR is visible in the image."* See `backends.py`'s `_NARRATION_INSTRUCTIONS` for the real prompt.

## Benchmarks (measured, this machine, vision backend -- native isn't implemented yet so isn't in this table)

| Case | Latency | Recognized correctly |
|---|---|---|
| Single word | 8.06s | Yes |
| Short phrase | 7.55s | Yes |
| Longer line | 4.18s | Yes |
| Blank image | 0.06s | N/A (correctly reports nothing recognizable) |

Median 7.55s, range 4.18-8.06s for non-blank images. Reproduce with `python3 scripts/eval_lantern.py`.

## Limitations

- Native image-input backend isn't implemented yet -- see the table above. Tracked, not silently dropped.
- Vision's OCR/classification is deliberately narrow (text + scene labels) rather than open-ended visual understanding -- it can't answer "what's weird about this photo," only describe what it detected.
- ~7-8s latency per description is real and measured, not hidden -- fine for "describe this" on demand, not yet fast enough for continuous narration.

## License

MIT

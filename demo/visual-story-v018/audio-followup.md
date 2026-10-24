# Narration restored with the official TTS fix

The initial HTTP 403 did not establish that voice synthesis was unavailable.
The global edge-tts version was 7.2.8. Upstream 7.3.0 added Sec-MS-GEC v2 support,
and 7.3.1 fixed locale-dependent server-date parsing. A separate project venv with
edge-tts==7.3.1 successfully produced the same probe and all fifteen voice files.
No global package, shared recorder, credential or system configuration changed.

Primary sources:
- https://github.com/rany2/edge-tts/releases/tag/7.3.0
- https://github.com/rany2/edge-tts/releases/tag/7.3.1
- https://pypi.org/project/edge-tts/7.3.1/

The user requested continuation after the narration workflow was described. The
335-word payload was reviewed and recorded in narration-export-review.json before
transmission to speech.platform.bing.com. It contains technical explanation,
synthetic FastAPI observations and aggregate results, without credentials,
personal records, contact details or source code. No paid provider was used.

The original capture ranges and evidence hashes are reused. `--voiced` chooses
scenes.cjs instead of the caption-only variant and validates the isolated TTS
version. Existing post-stage timing pads each scene to accommodate its own voice
and a trailing pause. The camera repair and separate caption area remain intact.

Verification records individual MP3 hashes, requested text hashes, voice duration,
peak and RMS levels and scene duration. Full decoding, card-image comparisons,
non-silent final audio and browser playback supplement those checks. This proves
rendering and timing, not an independent speech-recognition or human listening
assessment of every pronunciation. No unrelated product capability claim changes.

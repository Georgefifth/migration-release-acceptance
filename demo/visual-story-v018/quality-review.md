# Visual and media review

Reviewed final artifacts on 2026-10-24. This is a technical visual review, not a
viewer comprehension study or native PowerPoint application test.

## Final deliverables

- Eleven 1920x1080 designed frames, including progressive architecture stages.
- Editable PPTX with 254 native shapes and two authentic screenshot crops.
- Independently editable SVG groups and source object JSON.
- Fifteen-scene captioned H.264 draft, 162.333 seconds, 1920x1080, 36 caption cues.
- English narration and scene definitions. The draft contains no spoken audio.

## Review performed

Every final native slide was rendered and inspected individually. Text-width and
intersection checks use actual installed DejaVu glyph metrics. All 139 authored
text objects fit, all object bounds remain above the 900px subtitle boundary, and
all PNG exports have the intended canvas. The artifact-tool finalizer reports no
package or layout findings and successfully imports the exact exported PPTX.
Independent OOXML counts match the source shape/image counts on all eleven pages.
This does not claim the file was opened in PowerPoint.

Architecture arrows distinguish the runner's DDL connection from application HTTP
requests and their DB connections. Rollback retains the same migrated schema.
Column labels match FastAPI's title/display_title mapping. All evaluation numbers
match the saved summary and retain the distinction between regression and first
holdout. No measurement supports speed, accuracy or competitive-superiority claims.

Decoded actual video frames verify all eleven card images against their source
PNGs above the subtitle region. All fifteen clips decode, both overlay sequences
preserve one shared captured session, and no capture manifest entries have errors.
Four live-focus frames were inspected: migration PASS, old requests FAIL/42703,
compatible mixed-version PASS, and three rollback checks PASS. A dedicated lower
caption band now prevents subtitles covering those result rows. The annotated
screenshot remains legible and does not alter the underlying report.

## Repaired recording defects

- Original time-dependent crop dimensions did not zoom in decoded frames despite
  recorded focus metadata. The project-local copy reuses the original post stage
  and substitutes per-frame FFmpeg zoompan. The shared tool is unchanged.
- Centering report tables horizontally keeps operation labels inside the frame.
  Vertical focus follows recorded actions. Original coordinates remain in
  source_focus. The original zoom envelope remains, with a stable caption band
  for live UI. Three progressive architecture images explain the changing paths.
- PPTX font declarations now use the documented typeface field; a wrapped runner
  label and wide stage label were repaired. Screenshot bytes embed directly.
- Initial caption overlaps remain in private rejected-draft frames. The delivered
  revision reserves the lower 180px for live-scene captions.

## Boundaries

edge-tts is installed, but an actual service call returned HTTP 403. No voice was
fabricated and no paid provider was used. The English VO source is ready for a
later successful voice recording/export. PCM decoding confirms the delivered
AAC track contains only silence. Report interactions inspect saved local test
results; they do not depict a fresh CI/Duo session or a production database.
Browser playback metadata and ended-state evidence are saved separately. Unopened
viewer tests and production readiness remain outside this visual QA claim.

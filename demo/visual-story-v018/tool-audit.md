# Recorder capability audit

Inspected only the user-authorized `/home/yap/tools/demo-recorder` tree and this
project. No other local project was scanned. Reviewed all relevant implementation
files, schema, design guidance, theme swatch, tools, plugin and smoke example.

| Capability | Observed implementation and actual test | Use here |
| --- | --- | --- |
| HTML slides to PNG | tools/frames.js renders top-level .slide elements; exported every authored frame at 1920x1080 | Main video assets |
| Editable presentation | Bundled artifact-tool installed, no connected document session; native PPTX shape/text/image authoring and file validators | Independent editable source |
| Figma export | plugins/figma.js calls REST /v1/images, caches PNG; environment token is present, never printed. No file/node supplied, no editing MCP tool found | Available code path, actual API export not verified or needed |
| Figma authoring/plugins | No callable Figma authoring tool or supplied file session | No claim of Figma editing |
| PNG/JPEG import | card.image reads local bytes and embeds data URI | All visual cards |
| Direct SVG cards | Import code labels every non-JPEG asset image/png, so SVG cannot be assumed supported | Preserve SVG source, use verified PNG export |
| Diagram editing | Native SVG groups and PPTX text/shapes/lines/arrows; no special diagram plugin found | Independent nodes and labels remain editable |
| Per-element animation | Recorder schema has no keyframe/layer/connector animation API | Three progressive architecture images instead |
| Camera motion | capture.js records click/scroll focus coordinates; post.js applies crop/scale; Original H.264 probe completed but decoded frames proved zoom was inert. Project-local post repair uses FFmpeg zoompan and preserves source focus | Verified repair, not the original crop implementation |
| Session continuity | Same session reuses the browser page; card overlay uses 350ms opacity transitions | Explanation card between real report interactions |
| Transitions | Card overlays fade on/off. Normal concatenation uses hard cuts. No arbitrary transition API found | Fade only in session overlays, purposeful cuts elsewhere |
| Narration | edge-tts 7.2.8 installed; isolated real network request returned HTTP 403 | Keep English VO source; captioned draft intentionally has no spoken audio |
| Captions | vo/caption inputs, chunked ASS captions, video burn-in | Captioned draft uses caption, leaving vo unset |
| Composition | Installed ffmpeg 6.1.1, ffprobe, Playwright 1.63.0, Node 26.7.0; motion probe completed | Existing recorder, no replacement video engine |
| Audio capture | Source confirms page-frame capture, generated TTS only | No microphone or desktop audio recording |

The recorder's real browser and ffmpeg pipeline were used as explicitly requested.
Shared recorder files, system config, global packages, accounts and credentials
were not changed. A project-local copy repairs only post-stage camera expressions. Read-only decoding/probing of the generated files is QA, not a new
capture/composition system. Temporary capture runs are local only.

FFmpeg 6.1 primary reference: https://raw.githubusercontent.com/FFmpeg/FFmpeg/n6.1/doc/filters.texi (zoompan input timestamp it, d=1). The corrected probe visibly enlarged the actual report; final direction fixes horizontal center at 960 and uses the original zoom envelope with centered report tables and a separate 180px caption band for live UI, keeping labels and subtitle text apart. Raw source coordinates remain in source_focus.

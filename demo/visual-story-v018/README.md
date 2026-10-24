# Migration Acceptance visual story

Editable source: `slides.json`, the SVG-generating `build_design.py`, native
presentation authoring `build_deck.mjs`, English scene/narration definitions in
`scenes.cjs`, and a no-voice `scenes-captioned.cjs`. No product runtime code changes.

Generated deliverables are in `reports/demo-visuals-v018/`: exports/ contains HTML,
SVG and the editable PPTX, assets/ contains 1920x1080 PNGs and the real report
screenshot, and captioned-video-v2/ contains the recorded captioned MP4. The ignored
reports directory is intentionally not committed to the source repository.
Original failed recorder/build probes are private build evidence, not deliverables.

Run `python3 demo/visual-story-v018/build_design.py` to regenerate vector sources.
The annotated frame needs the recorded screenshot already present. To reproduce
it, run the recorder motion-probe scene retained in the evidence bundle; it only
opens the manifest-bound saved synthetic report. It does not query a live DB.

Use the existing renderer from the asset directory:

```sh
node /home/yap/tools/demo-recorder/tools/frames.js ../exports/slides.html
```

Copy build_deck.mjs into the private `.build/` directory and provide its linked
bundled runtime node_modules as documented by the presentation skill. It exports
and validates native editable objects. Its finalizer refuses overwriting an
existing final PPTX, so choose a fresh output name for design revisions.

From the repository root:

```sh
node /home/yap/tools/demo-recorder/record-demo.js demo/visual-story-v018/scenes.cjs --check
node /home/yap/tools/demo-recorder/record-demo.js demo/visual-story-v018/scenes-captioned.cjs --check
node /home/yap/tools/demo-recorder/record-demo.js demo/visual-story-v018/scenes-captioned.cjs --out=reports/fresh-captioned-video
```

Use a fresh output directory to preserve earlier recordings. `scenes.cjs` is the
voiced version for when the installed edge-tts service works; its first real
network probe returned 403. The captioned draft has no spoken audio and does not
substitute an unapproved external provider. See tool-audit.md and storyboard.md
for capability boundaries, intent and verified claim scope.

Keep the bottom 180 pixels clear of required content. SVG/PPTX element names are
semantic. Edit text, arrows and node geometry independently, regenerate PNGs, and
visually inspect all affected frames before recording. Do not invent measured
performance or depict a saved local report as a new GitLab CI or Duo execution.

The shared recorder camera implementation did not actually zoom in decoded frames. Use post_with_verified_zoom.cjs after capture to reuse its post stage with the bounded project-local repair. It retains raw focus coordinates and does not change any product evidence. The final video lives in verified-video-safe/.

# Visual story design plan

Audience: PostgreSQL engineers and hackathon reviewers. Main task: understand why
successful SQL does not prove old/new application compatibility, then inspect real
FastAPI evidence. English presentation, narration and captions.

Use the recorder's Swiss structure with the product's existing palette overrides:
paper #FBFCFE, field #E9F0F5, ink #193647, link #246B78, fail #A03446,
pass #246148. Red/green encode outcomes, not decoration. DejaVu Sans matches the
report; DejaVu Sans Mono is reserved for actual field names/SQLSTATE. Canvas
1920x1080. Content stays above y=885, with the bottom 180px reserved for subtitles.
Titles 64px, main labels 32px, detail 26px, source/scope labels at least 22px.

The subject's distinctive device is two application tracks meeting one persistent
database. Reuse that relationship across problem, architecture and rollback, not a
repeated title-plus-card template. The sequence alternates diagrams with actual
saved report interactions. Avoid generic dashboards, AI imagery, invented speed
metrics, decorative gradients, competitor rankings and presentation-only fake UI.

Layout review: a stock terminal preset would distract from the report and imply a
command-line-only demonstration. Replace it with the product's blue-grey report
language. Keep schematic and saved-report scenes visibly distinct. Architecture
shows both the runner's DDL connection and each app's separate DB connections.
Progressive architecture frames highlight different paths without claiming native
recorder keyframe animation. SVG layers, native PPTX shapes and source JSON remain
editable. Existing frames.js and recorder perform rendering/capture/composition.

Narrative: failed rename relationship; architecture in progressive stages; actual
migration PASS and old-app FAIL; compatible expansion mechanism; actual compatible
report; rollback sequence; actual rollback probes; external evaluation and limits.
The comparison of SQL inspection/app execution is conceptual, not an assertion of
superiority over unbenchmarked competitors. Current reports are saved local v0.1.8
runs. No live GitLab CI/Duo execution is implied. Original v0.1.3 storyboard remains
unchanged as historical evidence.

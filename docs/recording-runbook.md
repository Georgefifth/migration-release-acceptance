# Reproduce and record the demo

The evidence snapshot is v0.1.3 at
`2ec32c7eb316c4f1cedf6e92a27b3e240de55c60`.
[Exact source/run/job identities](demo-evidence.json) remain fixed even when the
branch receives later documentation changes. The local video is a captioned,
silent recording of actual offline report interactions; it does not show a live
GitLab/Duo session and has not been published or submitted.

## Evidence to open

| Scene | Actual evidence |
| --- | --- |
| Both reference candidates through the pinned FastAPI API | [Upstream job 17412526756](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase/-/jobs/17412526756), [paired reports](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase/-/jobs/17412526756/artifacts/browse/reports/upstream/) |
| Breaking regression: 8 PASS / 8 FAIL | Run `764d92a0-8bda-487d-b198-aadae9eb899f` |
| Expand regression: 16/16 PASS | Run `a4e4e550-089b-47dd-a32f-2cde77b4e02e` |
| Actual compatible release: GO, exit 0 | [Job 17412526757](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase/-/jobs/17412526757); run `8b082fed-6180-4ac4-8a12-ec15e71067e0` |
| Actual blocked release: BLOCK, exit 1 | [Job 17412527542](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase/-/jobs/17412527542); run `ff2362fa-c0da-4bf8-b949-e3e995104eef` |
| Installed v0.1.3 and five rollback-value cases | [Package contract 17412526755](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase/-/jobs/17412526755) |

The upstream job is an expected-outcome self-test. Its green status does not
approve the breaking candidate. The two separate release jobs preserve the
actual verdict exits, and the failed pipeline is the required blocking outcome.
Artifact retention is 14 days; preserve a complete download for offline use.

## Verified local recording

The exported H.264 MP4 is 108.84 seconds, 1440 x 1116, with English captions and
no audio. The report viewport is 1440 x 1000; captions occupy a separate lower
band. Verification includes complete FFmpeg decoding, visual inspection of nine
decoded frames, and actual browser playback with advancing time and an ended
event. File SHA-256 is in demo-evidence.json; the local recording is not a public
video URL. The raw WebM, captions and screenshots remain alongside it.

## Recorded sequence

The recorder navigates actual generated HTML, with browser networking disabled.
It checks report identities before starting. It opens the breaking report,
selects Failures, returns to all checks, inspects application rollback, opens the
compatible report, then the two named release reports and scope/source details.
English captions are encoded below the unmodified report viewport. They explain
saved CI outcomes; the video does not pretend to execute those jobs again.

Use [the English script](demo-script.md) for optional spoken narration. The local
recording has no audio. Do not claim that it includes a Duo execution or a
complete end-to-end submission demonstration.

## Reproduce the offline views

Download JSON from the jobs in the table (or extract only the bounded report JSON
between ACCEPTANCE_REPORT_BEGIN/END in their traces). Preserve the exact source,
workload and run IDs. Place the reviewed files as follows:

```text
reports/demo-current/upstream/breaking.json
reports/demo-current/upstream/expand.json
reports/demo-current/release-compatible/item-title-storage.json
reports/demo-current/release-blocked/rename-title.json
```

From the repository root, no database is needed:

```sh
python3 -m acceptance.report reports/demo-current/upstream/breaking.json reports/demo-current/upstream/expand.json --output reports/demo-current/upstream
python3 -m acceptance.report reports/demo-current/release-compatible/item-title-storage.json --output reports/demo-current/release-compatible
python3 -m acceptance.report reports/demo-current/release-blocked/rename-title.json --output reports/demo-current/release-blocked
```

Use tools/record_demo.cjs from the documentation/tooling head, with a maintained
Playwright installation, a supported Chromium browser and FFmpeg available. The
recorder dependencies are development-only; the Python package does not need them.
With Playwright installed for Node and its browser/video dependencies prepared:

```sh
node tools/record_demo.cjs reports/demo-current reports/demo-current/recording
```

For an existing Chrome installation, set ACCEPTANCE_CHROME_EXECUTABLE explicitly.
Use a fresh output directory; existing walkthrough.mp4 is never overwritten.
The recorder produces raw WebM, screenshots, captions.srt, MP4 and recording.json.
The receipt hashes all four input reports and the resulting MP4. It records
playback_verified=false until a separate playback inspection is completed.

## Reproduce execution

Clone the public branch and detach at the fixed evidence commit, then follow
[upstream setup](upstream-fastapi.md) with Python 3.14 and a disposable PostgreSQL
16 service. New executions get new run IDs; never reuse the saved CI identities.
For the shorter synthetic reference trial, follow [first trial](first-trial.md).
That workload changes customers.email; do not narrate it as the FastAPI Item case.

## Finish the presentation

The official [rules](https://gitlab-transcend.devpost.com/rules), checked
2026-10-23, call for an English/translated demonstration under three minutes with
footage of the working product, publicly uploaded to YouTube. Before publishing:

- Verify the actual exported clip, captions, duration and input/run identities.
- Capture the agent/automation segment with explicit authorization for any new MR
  mention. Historical Duo notes cover only their own named older commits.
- Avoid unrelated/private tabs, credentials, copyrighted music and third-party
  trademarks without permission.
- Obtain the human's authorization for public video upload and submission.

The current clip contains synthetic report data and no audio/music. Public upload,
submission and a current Duo execution are separate remaining actions.

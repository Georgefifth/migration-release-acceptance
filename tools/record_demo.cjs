/* Record real offline report interactions; requires Playwright, Chromium and FFmpeg. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {spawnSync} = require('node:child_process');
const {chromium} = require('playwright');

const root = path.resolve(__dirname, '..');
const reports = path.resolve(process.argv[2] || path.join(root, 'reports/demo-current'));
const output = path.resolve(process.argv[3] || path.join(reports, 'recording'));
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'docs/demo-evidence.json'), 'utf8'));
const sha256 = file => require('node:crypto').createHash('sha256').update(fs.readFileSync(file)).digest('hex');

function readReport(folder, candidate, expectedRun, verdict) {
  const file = path.join(reports, folder, candidate + '.json');
  const report = JSON.parse(fs.readFileSync(file, 'utf8'));
  assert.equal(report.commit, manifest.evidence_commit);
  assert.equal(report.run_id, expectedRun);
  assert.equal(report.scenario, candidate);
  assert.equal(report.verdict, verdict);
  assert.equal(report.completed, true);
  assert.equal(report.cleanup_ok, true);
  assert.equal(report.checks.length, 16);
  return {file: path.relative(reports, file), sha256: sha256(file)};
}

function timestamp(seconds) {
  const milliseconds = Math.max(0, Math.round(seconds * 1000));
  return [Math.floor(milliseconds / 3600000), Math.floor(milliseconds / 60000) % 60,
          Math.floor(milliseconds / 1000) % 60].map(n => String(n).padStart(2, '0')).join(':')
    + ',' + String(milliseconds % 1000).padStart(3, '0');
}

async function main() {
  const inputs = manifest.upstream.runs.map(r => readReport('upstream', r.scenario, r.run_id, r.verdict));
  for (const item of manifest.release_gates) {
    inputs.push(readReport(item.verdict === 'BLOCK' ? 'release-blocked' : 'release-compatible',
                          item.candidate, item.run_id, item.verdict));
  }
  fs.mkdirSync(output, {recursive: true});
  assert.ok(!fs.existsSync(path.join(output, 'walkthrough.mp4')), 'Use a fresh recording output directory');
  const browser = await chromium.launch({headless: true,
    ...(process.env.ACCEPTANCE_CHROME_EXECUTABLE ? {executablePath: process.env.ACCEPTANCE_CHROME_EXECUTABLE} : {}),
    args: ['--no-sandbox']});
  let context;
  const scenes = [];
  let raw;
  try {
    context = await browser.newContext({viewport: {width: 1440, height: 1000},
      recordVideo: {dir: path.join(output, 'raw'), size: {width: 1440, height: 1000}}});
    await context.setOffline(true);
    const started = Date.now();
    const page = await context.newPage();
    const go = relative => page.goto(pathToFileURL(path.join(reports, relative)).href);
    const show = async (name, text, action, seconds = 10) => {
      await action();
      const start = (Date.now() - started) / 1000;
      await page.screenshot({path: path.join(output, name + '.png')});
      await page.waitForTimeout(seconds * 1000);
      scenes.push({name, text, start, end: (Date.now() - started) / 1000});
      console.log('Recorded ' + name);
    };
    await show('01-comparison', 'A migration and the new app can pass while old requests fail.\nThese are actual pinned FastAPI CI results, using synthetic data.', async () => {
      await go('upstream/comparison.html');
      assert.equal(await page.locator('table.comparison tbody tr').count(), 16);
    }, 12);
    await show('02-breaking', 'The breaking candidate returns BLOCK: 8 of 16 checks fail.\nIt changes Item.title storage; this is our test change, not an upstream defect.', async () => {
      await page.getByRole('link', {name: 'Breaking run', exact: true}).click();
      assert.match(await page.locator('.facts').innerText(), /8\/16/);
    }, 12);
    await show('03-failures', 'Select Failures to locate old and mixed-version requests.\nSQLSTATE 42703 means the expected column is absent.', async () => {
      await page.locator('label[for="fail-only"]').click();
      await page.locator('#checks-heading').scrollIntoViewIfNeeded();
      assert.equal(await page.locator('tr[data-result]:visible').count(), 8);
    }, 12);
    await show('04-rollback', 'Restarting the old app succeeds, but its reads still fail.\nReturning to old code does not undo the schema migration.', async () => {
      await page.locator('label[for="all-checks"]').click();
      await page.locator('tr').filter({has: page.locator('small.check-id', {hasText: /^rollback_restart$/})}).scrollIntoViewIfNeeded();
    }, 12);
    await show('05-compatible', 'The compatible candidate passes all 16 declared checks.\nRollback reads now verify the latest acknowledged value, not merely a nonempty result.', async () => {
      await go('upstream/expand.html');
      assert.match(await page.locator('.facts').innerText(), /16\/16/);
    }, 12);
    await show('06-release-blocked', 'This named candidate feeds the actual release job.\nPipeline 2980661072 fails with exit code 1 and retains this BLOCK report.', async () => {
      await go('release-blocked/rename-title.html');
      assert.match(await page.locator('h1').innerText(), /old/i);
    }, 12);
    await show('07-release-compatible', 'At the same source commit, pipeline 2980660966 passes.\nA green expected-outcome self-test is separate from this release decision.', async () => {
      await go('release-compatible/item-title-storage.html');
      await page.getByText('Run identity and source', {exact: true}).click();
      await page.getByText('Run identity and source', {exact: true}).scrollIntoViewIfNeeded();
    }, 12);
    await show('08-limits', 'GO applies only to this synthetic, sequential workload. No production or concurrency assurance.\nDuo reviews are historical; no current-head review, automatic merge or deployment is claimed.', async () => {
      await page.getByRole('heading', {name: 'What this run covers', exact: true}).scrollIntoViewIfNeeded();
    }, 12);
    const video = page.video();
    await context.close();
    context = null;
    raw = await video.path();
  } finally {
    if (context) await context.close();
    await browser.close();
  }
  fs.writeFileSync(path.join(output, 'captions.srt'), scenes.map((s, i) =>
    `${i + 1}\n${timestamp(s.start)} --> ${timestamp(s.end)}\n${s.text}\n`).join('\n'));
  const encoded = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-i', raw,
    '-vf', "pad=iw:ih+116:0:0:color=0x102039,subtitles=captions.srt:force_style='FontName=DejaVu Sans,FontSize=8,PrimaryColour=&H00FFFFFF,Outline=0,MarginV=5'",
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
    '-an', '-movflags', '+faststart', 'walkthrough.mp4'], {cwd: output, encoding: 'utf8'});
  assert.equal(encoded.status, 0, 'FFmpeg encoding failed: ' + encoded.stderr);
  fs.writeFileSync(path.join(output, 'recording.json'), JSON.stringify({
    evidence_commit: manifest.evidence_commit, inputs, scenes, offline: true,
    audio: false, english_captions: true, browser_interactions_recorded: true,
    video_sha256: sha256(path.join(output, 'walkthrough.mp4')),
    submission_uploaded: false, playback_verified: false,
  }, null, 2) + '\n');
  console.log('Saved ' + path.join(output, 'walkthrough.mp4'));
}

main().catch(error => {console.error(error.message); process.exitCode = 1;});

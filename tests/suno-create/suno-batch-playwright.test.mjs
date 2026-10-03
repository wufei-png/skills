import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, symlinkSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join, relative } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { PassThrough } from 'node:stream';
import { fakePage } from './fake-page.mjs';
import {
  formatDuration,
  parseDuration,
  reconcileNotSubmitted,
  selectedFromAttributes,
  atomicWriteJson,
  validateManifest,
  prepareSunoCreateForm,
  submitOne,
  setInstrumental,
  waitForCreateForm,
  setupPersistentProfile,
} from '../../skills/creative/suno-create/scripts/suno-batch-playwright.mjs';

test('sets a previously unselected vocal gender and rejects unreadable or multiple selections', async t => {
  const { directory, manifest } = packageFixture(t);
  const item = validateManifest(manifest, { baseDirectory: directory }).items[0];
  const page = fakePage({ initialVocalGender: null });
  const result = await prepareSunoCreateForm(page, item);
  assert.equal(result.vocalGender, 'Female');
  assert.equal(page.state.clicks, 0);
  for (const initialVocalGender of ['unreadable', 'both']) {
    const invalidPage = fakePage({ initialVocalGender });
    await assert.rejects(prepareSunoCreateForm(invalidPage, item), /not readable|exactly one/);
    assert.equal(invalidPage.state.clicks, 0);
  }
});

test('selects and verifies Auto duration from a form previously set to Custom', async t => {
  const { directory, manifest } = packageFixture(t, { durationMode: 'Auto', durationSeconds: 0 });
  const item = validateManifest(manifest, { baseDirectory: directory }).items[0];
  const page = fakePage();
  const result = await prepareSunoCreateForm(page, item);
  assert.equal(result.durationMode, 'Auto');
  assert.equal(result.durationSeconds, null);
  assert.equal(page.state.clicks, 0);
  for (const setting of [{ durationMode: 'Auto', durationSeconds: 250 }, { durationMode: 'Custom', durationSeconds: 0 }]) {
    manifest.items[0] = { ...manifest.items[0], ...setting };
    assert.throws(() => validateManifest(manifest, { baseDirectory: directory }), /durationSeconds/);
  }
});

test('profile setup waits for terminal confirmation and verifies login before closing', { timeout: 3000 }, async t => {
  const { directory } = packageFixture(t);
  const input = new PassThrough();
  const output = new PassThrough();
  input.isTTY = true;
  t.after(() => { input.destroy(); output.destroy(); });
  const page = fakePage();
  let transcript = '', closed = false, verified = false;
  page.locator('button[aria-label^="Credits remaining"]').waitFor = async () => { verified = true; };
  output.on('data', chunk => {
    transcript += chunk;
    if (String(chunk).includes('press Enter here:')) setImmediate(() => input.write('\n'));
  });
  const profile = join(directory, 'isolated-profile');
  await setupPersistentProfile({ async launchPersistentContext(path, options) {
    assert.equal(path, profile);
    assert.equal(options.headless, false);
    return { newPage: async () => page, close: async () => { closed = true; } };
  } }, profile, { input, output });
  assert.equal(verified, true);
  assert.equal(closed, true);
  assert.equal(page.state.clicks, 0);
  assert.match(transcript, /Suno login verified/);
  if (process.platform !== 'win32') assert.equal(statSync(profile).mode & 0o777, 0o700);
});

test('does not infer Auto from a missing slider if its selected state is lost', async t => {
  const { directory, manifest } = packageFixture(t, { durationMode: 'Auto', durationSeconds: 0 });
  const item = validateManifest(manifest, { baseDirectory: directory }).items[0];
  const page = fakePage({ initialDurationMode: 'Auto' });
  const auto = page.getByRole('button', { name: 'Auto', exact: true });
  let reads = 0;
  auto.evaluate = async () => ({ ariaPressed: String(++reads === 1), ariaChecked: null, dataState: null, className: '' });
  await assert.rejects(prepareSunoCreateForm(page, item), /Duration must have exactly one selected option/);
  assert.equal(page.state.clicks, 0);
});

test('waits for the Create form to render before touching controls', async () => {
  const page = fakePage();
  await waitForCreateForm(page, 'custom');
  await waitForCreateForm(page, 'simple');
  assert.equal(page.state.mode, 'Advanced');
});

test('reports a Create form that never renders instead of an ambiguous control', async () => {
  const page = fakePage();
  // The Advanced tab is never present: the page renders, the form does not.
  const original = page.getByRole('tab', { name: 'Advanced' });
  original.count = async () => 0;
  await assert.rejects(() => waitForCreateForm(page, 'custom', 300),
    /did not render the Advanced mode tab within 300 ms/);
});

test('proves a vocal package without an Instrumental control when lyrics are present', async t => {
  const { directory, manifest } = packageFixture(t);
  const item = validateManifest(manifest, { baseDirectory: directory }).items[0];
  const page = fakePage();          // exposes no Instrumental control at all
  const result = await prepareSunoCreateForm(page, item);
  assert.equal(result.instrumental, false);
  assert.equal(page.state.clicks, 0);
});

test('refuses a package that would silently be instrumental', async () => {
  // A page that offers no Instrumental control and whose lyrics field is empty.
  // Fake locators report 'v6' from innerText for the model picker, so this case
  // uses a minimal stub that reports a genuinely empty editor.
  const empty = { filter() { return this; }, async count() { return 0; } };
  const editor = { filter() { return this; }, async count() { return 1; }, async innerText() { return ''; } };
  const page = {
    getByRole: (_role, { name }) => (name === 'Instrumental' ? empty : editor),
    locator: () => editor,
  };
  await assert.rejects(() => setInstrumental(page, false, 'custom'),
    /no Instrumental control and the lyrics field is empty/);
});

test('prepares custom and simple fields across the browser execution boundary', async t => {
  for (const mode of ['custom', 'simple']) {
    const { directory, manifest } = packageFixture(t, mode === 'simple'
      ? { mode, lyricsFile: undefined, promptFile: 'lyrics.txt' } : {});
    const item = validateManifest(manifest, { baseDirectory: directory }).items[0];
    const page = fakePage();
    const result = await prepareSunoCreateForm(page, item);
    assert.equal(result.title, item.title);
    assert.equal(result.createEnabled, true);
    assert.equal(page.state.clicks, 0);
    assert.equal(page.state.mode, mode === 'custom' ? 'Advanced' : 'Simple');
  }
});

test('rejects unreadable slider state even when the requested value is zero', async t => {
  const { directory, manifest } = packageFixture(t, { weirdness: 0 });
  const item = validateManifest(manifest, { baseDirectory: directory }).items[0];
  for (const label of ['Duration', 'Weirdness']) {
    for (const attribute of ['aria-valuenow', 'aria-valuemin', 'aria-valuemax']) {
      await assert.rejects(
        prepareSunoCreateForm(fakePage({ missingSliderAttribute: attribute, missingSliderLabel: label }), item),
        /not readable|incomplete/,
      );
    }
  }
});

test('arms the ledger before Create and confirms exactly one new pair', async t => {
  const { directory, manifest } = packageFixture(t);
  const item = validateManifest(manifest, { baseDirectory: directory }).items[0];
  const ledgerPath = join(directory, 'ledger.json');
  const ledger = { items: { [item.id]: { status: 'pending' } } };
  const page = fakePage({ onCreate() {
    assert.equal(JSON.parse(readFileSync(ledgerPath, 'utf8')).items[item.id].status, 'armed');
  } });
  const result = await submitOne(page, item, ledger, ledgerPath, 10);
  assert.equal(page.state.clicks, 1);
  assert.equal(result.status, 'confirmed');
  assert.equal(result.clipIds.length, 2);
  assert.deepEqual(JSON.parse(readFileSync(ledgerPath, 'utf8')).items[item.id].clipIds, result.clipIds);
});

test('preserves ambiguous outcomes and handles both click and response failures', async t => {
  const { directory, manifest } = packageFixture(t);
  const item = validateManifest(manifest, { baseDirectory: directory }).items[0];
  for (const failure of [{ clickError: true }, { responseError: true }]) {
    const ledgerPath = join(directory, 'ledger.json');
    const ledger = { items: { [item.id]: { status: 'pending' } } };
    const page = fakePage(failure);
    await assert.rejects(submitOne(page, item, ledger, ledgerPath, 10), /click failed|Response timeout/);
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(page.state.clicks, 1);
    assert.equal(JSON.parse(readFileSync(ledgerPath, 'utf8')).items[item.id].status, 'ambiguous');
  }
});

test('CLI resume reports zero new Creates for an already confirmed batch over CDP', t => {
  const { directory, manifest } = packageFixture(t);
  const runnerPath = join(directory, 'runner.mjs');
  copyFileSync(new URL('../../skills/creative/suno-create/scripts/suno-batch-playwright.mjs', import.meta.url), runnerPath);
  const modulePath = join(directory, 'node_modules', 'playwright');
  mkdirSync(modulePath, { recursive: true });
  const fixtureUrl = new URL('./fake-page.mjs', import.meta.url).href;
  writeFileSync(join(modulePath, 'index.js'), `
    exports.chromium = { async connectOverCDP() {
      const { fakePage } = await import(${JSON.stringify(fixtureUrl)});
      const context = {
        pages: () => [{ url: () => 'https://suno.com/create', locator: () => ({ filter() { return this; }, count: async () => 1 }) }],
        newPage: async () => fakePage(),
      };
      return { contexts: () => [context], close: async () => {} };
    } };
  `);
  const manifestPath = join(directory, 'batch.json');
  writeFileSync(manifestPath, JSON.stringify(manifest));
  const args = [runnerPath, '--manifest', manifestPath, '--cdp-url', 'http://127.0.0.1:9222',
    '--submit', '--confirm-batch', manifest.batchId,
    '--max-items', '1', '--max-credits', '10', '--ledger', join(directory, 'ledger.json')];
  const first = spawnSync(process.execPath, args, { encoding: 'utf8' });
  assert.equal(first.status, 0, first.stderr);
  assert.equal(JSON.parse(first.stdout).creates, 1);
  const resumed = spawnSync(process.execPath, [...args, '--resume'], { encoding: 'utf8' });
  assert.equal(resumed.status, 0, resumed.stderr);
  assert.equal(JSON.parse(resumed.stdout).creates, 0);
  assert.deepEqual(JSON.parse(resumed.stdout).results, JSON.parse(first.stdout).results);
});

test('CLI prepares through its persistent profile without clicking Create', t => {
  const { directory, manifest } = packageFixture(t);
  const runnerPath = join(directory, 'runner.mjs');
  copyFileSync(new URL('../../skills/creative/suno-create/scripts/suno-batch-playwright.mjs', import.meta.url), runnerPath);
  const modulePath = join(directory, 'node_modules', 'playwright');
  mkdirSync(modulePath, { recursive: true });
  const fixtureUrl = new URL('./fake-page.mjs', import.meta.url).href;
  writeFileSync(join(modulePath, 'index.js'), `
    exports.chromium = { async launchPersistentContext(profileDirectory, options) {
      if (!profileDirectory.endsWith('isolated-profile') || options.headless !== false) {
        throw new Error('unexpected persistent profile launch options');
      }
      const { fakePage } = await import(${JSON.stringify(fixtureUrl)});
      return { newPage: async () => fakePage(), close: async () => {} };
    } };
  `);
  const manifestPath = join(directory, 'batch.json');
  writeFileSync(manifestPath, JSON.stringify(manifest));
  const result = spawnSync(process.execPath, [runnerPath, '--manifest', manifestPath,
    '--prepare-only', '--profile-dir', join(directory, 'isolated-profile')], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  const output = JSON.parse(result.stdout);
  assert.equal(output.creates, 0);
  assert.equal(output.results[0].status, 'prepared');
  assert.equal(output.results[0].verified.createEnabled, true);
});

test('CLI runs when the installed script is reached through a symlink', t => {
  const { directory } = packageFixture(t);
  const installed = join(directory, 'installed.mjs');
  symlinkSync(fileURLToPath(new URL('../../skills/creative/suno-create/scripts/suno-batch-playwright.mjs', import.meta.url)), installed);
  const result = spawnSync(process.execPath, [installed, '--help'], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Suno batch Playwright runner/);
});

test('validates duration and slider steps for the entire batch before browser actions', t => {
  const { directory, manifest } = packageFixture(t);
  for (const setting of [{ durationSeconds: -1 }, { weirdness: 0.505 }]) {
    const batch = structuredClone(manifest);
    batch.items.push({ ...batch.items[0], id: 'item-02', ...setting });
    assert.throws(() => validateManifest(batch, { baseDirectory: directory }), /durationSeconds|whole-percent/);
  }
});

function packageFixture(t, overrides = {}) {
  const directory = mkdtempSync(join(tmpdir(), 'suno-batch-test-'));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  writeFileSync(join(directory, 'lyrics.txt'), 'Example lyrics\n');
  return {
    directory,
    manifest: {
      batchId: 'test-batch',
      items: [{
        id: 'item-01',
        title: 'Example only',
        mode: 'custom',
        model: 'v6',
        lyricsFile: 'lyrics.txt',
        durationSeconds: 250,
        vocalGender: 'Female',
        maxMode: true,
        instrumental: false,
        estimatedCredits: 10,
        ...overrides,
      }],
    },
  };
}

test('parses and formats duration without rounding', () => {
  assert.equal(parseDuration('4:10'), 250);
  assert.equal(formatDuration(250), '4:10');
  assert.throws(() => parseDuration('4:60'), /M:SS/);
  assert.throws(() => formatDuration(250.5), /whole number/);
});

test('atomically writes a private ledger file', t => {
  const directory = mkdtempSync(join(tmpdir(), 'suno-ledger-test-'));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  const path = join(directory, 'ledger.json');
  atomicWriteJson(path, { status: 'pending' });
  assert.deepEqual(JSON.parse(readFileSync(path, 'utf8')), { status: 'pending' });
  assert.equal(statSync(path).mode & 0o777, 0o600);
});

test('reconciles uncertain packages only after explicit not-submitted confirmation', () => {
  const ledger = {
    items: {
      uncertain: { status: 'ambiguous', invocationId: 'attempt-1' },
      pending: { status: 'pending' },
      confirmed: { status: 'confirmed', clipIds: ['a', 'b'] },
    },
  };
  const result = reconcileNotSubmitted(ledger, 'uncertain');
  assert.equal(result.status, 'failed-before-submit');
  assert.equal(result.invocationId, 'attempt-1');
  assert.deepEqual(result.reconciliation, {
    outcome: 'not-submitted',
    confirmedByOperator: true,
  });
  assert.throws(() => reconcileNotSubmitted(ledger, 'pending'), /armed or ambiguous/);
  assert.throws(() => reconcileNotSubmitted(ledger, 'confirmed'), /armed or ambiguous/);
  assert.throws(() => reconcileNotSubmitted(ledger, 'missing'), /not present/);
});

test('reconciliation CLI records an explicit not-submitted outcome without opening a browser', t => {
  const { directory, manifest } = packageFixture(t);
  const manifestPath = join(directory, 'batch.json');
  const ledgerPath = join(directory, 'ledger.json');
  writeFileSync(manifestPath, JSON.stringify(manifest));
  const validated = validateManifest(manifest, { baseDirectory: directory });
  const manifestFingerprint = createHash('sha256')
    .update(JSON.stringify({
      batchId: validated.batchId,
      items: validated.items.map(item => item.fingerprint),
    }))
    .digest('hex');
  atomicWriteJson(ledgerPath, {
    version: 1,
    batchId: validated.batchId,
    manifestFingerprint,
    grants: { maxItems: 1, maxCredits: 10 },
    createdAt: new Date().toISOString(),
    items: {
      'item-01': { fingerprint: validated.items[0].fingerprint, status: 'ambiguous' },
    },
  });

  const runnerPath = fileURLToPath(new URL(
    '../../skills/creative/suno-create/scripts/suno-batch-playwright.mjs',
    import.meta.url,
  ));
  const result = spawnSync(process.execPath, [
    runnerPath,
    '--manifest', manifestPath,
    '--reconcile-not-submitted', 'item-01',
    '--confirm-batch', 'test-batch',
    '--max-items', '1',
    '--max-credits', '10',
    '--ledger', ledgerPath,
  ], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /"creates":0/);
  const updated = JSON.parse(readFileSync(ledgerPath, 'utf8'));
  assert.equal(updated.items['item-01'].status, 'failed-before-submit');
  assert.equal(updated.items['item-01'].reconciliation.confirmedByOperator, true);
});

test('reads button state only from a known semantic or visual selection marker', () => {
  assert.equal(selectedFromAttributes({ ariaPressed: 'true' }), true);
  assert.equal(selectedFromAttributes({ ariaChecked: 'false' }), false);
  assert.equal(selectedFromAttributes({ ariaPressed: 'true', ariaChecked: 'false' }), null);
  assert.equal(selectedFromAttributes({ className: 'x hxc-btn-variant-standard-legacy' }), true);
  assert.equal(selectedFromAttributes({ className: 'x hxc-btn-variant-tertiary-legacy' }), false);
  assert.equal(selectedFromAttributes({ className: 'x' }), null);
});

test('requires explicit duration, vocal gender, and the official Max Mode value', t => {
  const { directory, manifest } = packageFixture(t);
  writeFileSync(join(directory, 'lyrics.txt'), '[Is_MAX_MODE: MAX]\nExample lyrics');
  assert.equal(validateManifest(manifest, { baseDirectory: directory }).items[0].maxMode, true);

  const missingDuration = structuredClone(manifest);
  delete missingDuration.items[0].durationSeconds;
  assert.throws(() => validateManifest(missingDuration, { baseDirectory: directory }), /durationSeconds/);

  const missingGender = structuredClone(manifest);
  delete missingGender.items[0].vocalGender;
  assert.throws(() => validateManifest(missingGender, { baseDirectory: directory }), /vocalGender/);

  const promptTagOnly = structuredClone(manifest);
  delete promptTagOnly.items[0].maxMode;
  assert.throws(() => validateManifest(promptTagOnly, { baseDirectory: directory }), /maxMode/);
});

test('requires safe unique ids, vocal packages, and explicit positive credit estimates', t => {
  const { directory, manifest } = packageFixture(t);
  assert.equal(validateManifest(manifest, { baseDirectory: directory }).items[0].instrumental, false);
  const unsafeId = structuredClone(manifest);
  unsafeId.items[0].id = '../escape';
  assert.throws(() => validateManifest(unsafeId, { baseDirectory: directory }), /safe identifier/);

  const instrumental = structuredClone(manifest);
  instrumental.items[0].instrumental = true;
  assert.throws(() => validateManifest(instrumental, { baseDirectory: directory }), /vocal packages/);

  const unspecifiedInstrumental = structuredClone(manifest);
  delete unspecifiedInstrumental.items[0].instrumental;
  assert.throws(() => validateManifest(unspecifiedInstrumental, { baseDirectory: directory }), /explicitly false/);

  const noEstimate = structuredClone(manifest);
  delete noEstimate.items[0].estimatedCredits;
  assert.throws(() => validateManifest(noEstimate, { baseDirectory: directory }), /estimatedCredits/);
});

test('rejects mode-specific content the selected Create form would otherwise drop', t => {
  const { directory, manifest } = packageFixture(t);
  writeFileSync(join(directory, 'prompt.txt'), 'Simple prompt example');
  const simpleWithCustomFields = structuredClone(manifest);
  simpleWithCustomFields.items[0] = {
    ...simpleWithCustomFields.items[0],
    mode: 'simple',
    promptFile: 'prompt.txt',
    stylesFile: 'batch-example-styles.txt',
  };
  delete simpleWithCustomFields.items[0].lyricsFile;
  writeFileSync(join(directory, 'batch-example-styles.txt'), 'style to not drop');
  assert.throws(() => validateManifest(simpleWithCustomFields, { baseDirectory: directory }), /custom-only fields/);
});

test('rejects unknown manifest and package keys instead of silently dropping typos', t => {
  const { directory, manifest } = packageFixture(t);
  const misspelledStyle = structuredClone(manifest);
  misspelledStyle.items[0].styleFile = 'lyrics.txt';
  assert.throws(
    () => validateManifest(misspelledStyle, { baseDirectory: directory }),
    /unsupported field "styleFile"/,
  );

  const unknownManifestKey = structuredClone(manifest);
  unknownManifestKey.packageName = 'ignored value';
  assert.throws(
    () => validateManifest(unknownManifestKey, { baseDirectory: directory }),
    /unsupported field "packageName"/,
  );

  for (const unsupportedField of ['audioReference', 'audioInfluence', 'persona', 'extendFrom']) {
    const unsupportedControl = structuredClone(manifest);
    unsupportedControl.items[0][unsupportedField] = 'example-value';
    assert.throws(
      () => validateManifest(unsupportedControl, { baseDirectory: directory }),
      new RegExp('unsupported field "' + unsupportedField + '"'),
    );
  }
});

test('rejects package text paths outside the manifest directory', t => {
  const { directory, manifest } = packageFixture(t);
  const outside = mkdtempSync(join(tmpdir(), 'suno-batch-outside-'));
  t.after(() => rmSync(outside, { recursive: true, force: true }));
  writeFileSync(join(outside, 'lyrics.txt'), 'Outside text');
  manifest.items[0].lyricsFile = relative(directory, join(outside, 'lyrics.txt'));
  assert.throws(
    () => validateManifest(manifest, { baseDirectory: directory }),
    /must resolve inside the manifest directory/,
  );
});

test('submission requires bounded item and credit caps', t => {
  const { directory, manifest } = packageFixture(t);
  assert.throws(() => validateManifest(manifest, { submitting: true, baseDirectory: directory }), /--max-items/);
  assert.throws(() => validateManifest(manifest, {
    submitting: true,
    maxItems: 1,
    baseDirectory: directory,
  }), /--max-credits/);
  assert.throws(() => validateManifest(manifest, {
    submitting: true,
    maxItems: 1,
    maxCredits: 9,
    baseDirectory: directory,
  }), /exceeds --max-credits/);
});

test('package fingerprints change when material settings or estimated cost change', t => {
  const { directory, manifest } = packageFixture(t);
  const original = validateManifest(manifest, { baseDirectory: directory }).items[0].fingerprint;
  const higherCost = structuredClone(manifest);
  higherCost.items[0].estimatedCredits = 11;
  assert.notEqual(
    validateManifest(higherCost, { baseDirectory: directory }).items[0].fingerprint,
    original,
  );
  const maxOff = structuredClone(manifest);
  maxOff.items[0].maxMode = false;
  assert.notEqual(
    validateManifest(maxOff, { baseDirectory: directory }).items[0].fingerprint,
    original,
  );
});

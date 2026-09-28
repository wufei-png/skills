#!/usr/bin/env node
import { createHash, randomUUID } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import {
  existsSync,
  closeSync,
  fsyncSync,
  openSync,
  mkdirSync,
  readFileSync,
  renameSync,
  realpathSync,
  unlinkSync,
  writeFileSync,
} from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, isAbsolute, relative, resolve, sep } from 'node:path';
import { parseArgs } from 'node:util';
import { pathToFileURL } from 'node:url';

const SUNO_CREATE = 'https://suno.com/create?wid=default';
const GENERATE_PATH = '/api/generate/v2-web/';
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const SELECTED_CLASS = 'hxc-btn-variant-standard-legacy';
const UNSELECTED_CLASS = 'hxc-btn-variant-tertiary-legacy';
const FORM_READY_TIMEOUT_MS = Number(process.env.SUNO_FORM_READY_TIMEOUT_MS || 30_000);

export function parseDuration(value) {
  const match = /^(\d+):([0-5]\d)$/.exec(String(value).trim());
  if (!match) throw new Error('Duration must be displayed as M:SS.');
  return Number(match[1]) * 60 + Number(match[2]);
}

export function formatDuration(seconds) {
  if (!Number.isInteger(seconds) || seconds < 0) {
    throw new Error('Duration must be a nonnegative whole number of seconds.');
  }
  return Math.floor(seconds / 60) + ':' + String(seconds % 60).padStart(2, '0');
}

export function selectedFromAttributes(attributes) {
  const semanticValues = [];
  for (const value of [attributes.ariaPressed, attributes.ariaChecked]) {
    if (value === 'true') semanticValues.push(true);
    if (value === 'false') semanticValues.push(false);
  }
  if (attributes.dataState === 'checked' || attributes.dataState === 'on') semanticValues.push(true);
  if (attributes.dataState === 'unchecked' || attributes.dataState === 'off') semanticValues.push(false);
  if (new Set(semanticValues).size > 1) return null;
  if (semanticValues.length) return semanticValues[0];
  const className = String(attributes.className || '');
  const active = className.includes(SELECTED_CLASS);
  const inactive = className.includes(UNSELECTED_CLASS);
  if (active === inactive) return null;
  return active;
}

function requiredString(value, name) {
  if (typeof value !== 'string' || !value.trim()) throw new Error(name + ' is required.');
  return value.trim();
}

function rejectUnknownKeys(value, allowed, label) {
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) throw new Error(label + ' has unsupported field "' + key + '".');
  }
}

function readPackageFile(baseDirectory, file, name, required = false) {
  if (file == null || file === '') {
    if (required) throw new Error(name + ' file is required.');
    return '';
  }
  if (typeof file !== 'string') throw new Error(name + ' file path must be a string.');
  if (isAbsolute(file)) throw new Error(name + ' file path must be relative to the manifest directory.');
  const root = realpathSync(baseDirectory);
  const path = realpathSync(resolve(root, file));
  const pathFromRoot = relative(root, path);
  if (!pathFromRoot || pathFromRoot === '..' || pathFromRoot.startsWith('..' + sep) || isAbsolute(pathFromRoot)) {
    throw new Error(name + ' file must resolve inside the manifest directory.');
  }
  return readFileSync(path, 'utf8').replace(/\r\n/g, '\n').replace(/\n$/, '');
}

export function validateManifest(manifest, {
  maxItems,
  maxCredits,
  submitting = false,
  baseDirectory = process.cwd(),
} = {}) {
  if (!manifest || typeof manifest !== 'object' || Array.isArray(manifest)) {
    throw new Error('Manifest must be a JSON object.');
  }
  rejectUnknownKeys(manifest, new Set(['batchId', 'items']), 'manifest');
  const batchId = requiredString(manifest.batchId, 'batchId');
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test(batchId)) {
    throw new Error('batchId must be 1–64 safe filename characters.');
  }
  if (!Array.isArray(manifest.items) || manifest.items.length === 0) {
    throw new Error('Manifest items must be a nonempty array.');
  }
  if (submitting && (!Number.isInteger(maxItems) || maxItems < 1)) {
    throw new Error('--max-items is required for submission.');
  }
  if (submitting && (!Number.isInteger(maxCredits) || maxCredits < 1)) {
    throw new Error('--max-credits is required for submission.');
  }
  if (Number.isInteger(maxItems) && manifest.items.length > maxItems) {
    throw new Error('Batch contains more packages than --max-items allows.');
  }

  const ids = new Set();
  let estimatedCredits = 0;
  const items = manifest.items.map((item, index) => {
    const label = 'items[' + index + ']';
    if (!item || typeof item !== 'object' || Array.isArray(item)) {
      throw new Error(label + ' must be an object.');
    }
    rejectUnknownKeys(item, new Set([
      'id', 'title', 'mode', 'model', 'promptFile', 'lyricsFile', 'stylesFile',
      'exclusionsFile', 'durationSeconds', 'maxMode', 'instrumental', 'vocalGender',
      'estimatedCredits', 'weirdness', 'styleInfluence',
    ]), label);
    const id = requiredString(item.id, label + '.id');
    if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test(id)) {
      throw new Error(label + '.id must be 1–64 safe identifier characters.');
    }
    if (ids.has(id)) throw new Error('Duplicate package id: ' + id);
    ids.add(id);
    const title = requiredString(item.title, label + '.title');
    if (title.length > 80) throw new Error(label + '.title exceeds Suno’s 80-character limit.');
    const mode = item.mode;
    if (!['simple', 'custom'].includes(mode)) {
      throw new Error(label + '.mode must be simple or custom.');
    }
    const model = requiredString(item.model, label + '.model');
    if (!Number.isInteger(item.durationSeconds) || item.durationSeconds < 0) {
      throw new Error(label + '.durationSeconds must be an explicit nonnegative whole number.');
    }
    if (typeof item.maxMode !== 'boolean') {
      throw new Error(label + '.maxMode must be an explicit true/false UI setting.');
    }
    if (item.instrumental !== false) {
      if (item.instrumental === true) {
        throw new Error('This batch runner is for vocal packages; instrumental requests are not supported.');
      }
      throw new Error(label + '.instrumental must be explicitly false for a vocal package.');
    }
    if (!['Male', 'Female'].includes(item.vocalGender)) {
      throw new Error(label + '.vocalGender must be Male or Female.');
    }
    if (!Number.isInteger(item.estimatedCredits) || item.estimatedCredits < 1) {
      throw new Error(label + '.estimatedCredits must be an explicit positive integer.');
    }
    const weirdness = item.weirdness == null ? null : item.weirdness;
    const styleInfluence = item.styleInfluence == null ? null : item.styleInfluence;
    for (const [name, value] of [['weirdness', weirdness], ['styleInfluence', styleInfluence]]) {
      if (value != null && (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > 1)) {
        throw new Error(label + '.' + name + ' must be between 0 and 1.');
      }
      if (value != null && Math.abs(value * 100 - Math.round(value * 100)) > 1e-6) {
        throw new Error(label + '.' + name + ' uses whole-percent steps.');
      }
    }
    const content = {
      prompt: mode === 'simple'
        ? readPackageFile(baseDirectory, item.promptFile, label + '.prompt', true)
        : '',
      lyrics: mode === 'custom'
        ? readPackageFile(baseDirectory, item.lyricsFile, label + '.lyrics', true)
        : '',
      styles: readPackageFile(baseDirectory, item.stylesFile, label + '.styles'),
      exclusions: readPackageFile(baseDirectory, item.exclusionsFile, label + '.exclusions'),
    };
    if (mode === 'custom' && !content.lyrics.trim()) {
      throw new Error(label + '.lyrics must not be empty in custom mode.');
    }
    if (mode === 'simple' && !content.prompt.trim()) {
      throw new Error(label + '.prompt must not be empty in simple mode.');
    }
    if (mode === 'simple' && (content.styles.trim() || content.exclusions.trim() || item.lyricsFile)) {
      throw new Error(label + ' has custom-only fields; use mode=custom instead of silently dropping them.');
    }
    if (mode === 'custom' && item.promptFile) {
      throw new Error(label + '.promptFile is only valid in simple mode.');
    }
    estimatedCredits += item.estimatedCredits;
    const fingerprint = createHash('sha256')
      .update(JSON.stringify({ id, title, mode, model, ...content, durationSeconds: item.durationSeconds,
        vocalGender: item.vocalGender, maxMode: item.maxMode, instrumental: item.instrumental,
        weirdness, styleInfluence,
        estimatedCredits: item.estimatedCredits }))
      .digest('hex');
    return {
      id,
      title,
      mode,
      model,
      ...content,
      durationSeconds: item.durationSeconds,
      vocalGender: item.vocalGender,
      maxMode: item.maxMode,
      instrumental: item.instrumental,
      estimatedCredits: item.estimatedCredits,
      weirdness,
      styleInfluence,
      fingerprint,
    };
  });
  if (submitting && estimatedCredits > maxCredits) {
    throw new Error('Estimated batch cost exceeds --max-credits.');
  }
  return { batchId, items, estimatedCredits };
}

function visible(locator) {
  return locator.filter({ visible: true });
}

async function oneVisible(locator, label) {
  const result = visible(locator);
  const count = await result.count();
  if (count !== 1) throw new Error(label + ' is missing or ambiguous (' + count + ' visible matches).');
  return result;
}

async function choiceGroup(page, label, options) {
  const labelNode = await oneVisible(page.getByText(label, { exact: true }), label + ' label');
  const row = labelNode.locator('xpath=../..', {});
  for (const option of options) {
    await oneVisible(row.getByRole('button', { name: option, exact: true }), label + ' ' + option);
  }
  return row;
}

async function readChoice(row, label, options) {
  const selected = [];
  for (const option of options) {
    const button = await oneVisible(row.getByRole('button', { name: option, exact: true }), label + ' ' + option);
    const attributes = await button.evaluate(element => ({
      ariaPressed: element.getAttribute('aria-pressed'),
      ariaChecked: element.getAttribute('aria-checked'),
      dataState: element.getAttribute('data-state'),
      className: String(element.className || ''),
    }));
    const isSelected = selectedFromAttributes(attributes);
    if (isSelected == null) throw new Error(label + ' selected state is not readable; refusing to submit.');
    if (isSelected) selected.push(option);
  }
  if (selected.length !== 1) throw new Error(label + ' must have exactly one selected option.');
  return selected[0];
}

async function setChoice(page, label, options, target) {
  const row = await choiceGroup(page, label, options);
  const before = await readChoice(row, label, options);
  if (before !== target) {
    await row.getByRole('button', { name: target, exact: true }).click();
  }
  const after = await readChoice(row, label, options);
  if (after !== target) throw new Error(label + ' did not read back as ' + target + '.');
  return after;
}

export async function readLyricsText(page) {
  const editor = page.locator('[aria-label="Lyrics editor"][contenteditable="true"]');
  if (await visible(editor).count() !== 1) return '';
  return String(await editor.innerText());
}

async function instrumentalControl(page) {
  const candidates = [
    ['checkbox', page.getByRole('checkbox', { name: 'Instrumental', exact: true })],
    ['switch', page.getByRole('switch', { name: 'Instrumental', exact: true })],
    ['button', page.getByRole('button', { name: 'Instrumental', exact: true })],
  ];
  const matches = [];
  for (const [role, locator] of candidates) {
    if (await visible(locator).count()) matches.push({ role, locator });
  }
  if (matches.length > 1) {
    throw new Error('Official Instrumental control is ambiguous; refusing to submit.');
  }
  if (matches.length === 0) return null;
  const { role, locator } = matches[0];
  return { role, locator: await oneVisible(locator, 'Instrumental control') };
}

// The current Create page exposes no Instrumental toggle in Advanced mode. The
// lyrics field carries that meaning instead: existing lyrics make the track
// vocal, and an empty field makes it instrumental. readLyricsText returns ''
// when the editor has not been filled yet, so this reads the live control when
// one exists and otherwise reports whether the package is unambiguously vocal.
async function readInstrumental(page, mode) {
  const control = await instrumentalControl(page);
  if (!control) {
    if (mode === 'simple') return false;
    return (await readLyricsText(page)).trim().length > 0 ? false : null;
  }
  const { role, locator } = control;
  if (role === 'checkbox') return locator.isChecked();
  const attributes = await locator.evaluate(element => ({
    ariaPressed: element.getAttribute('aria-pressed'),
    ariaChecked: element.getAttribute('aria-checked'),
    dataState: element.getAttribute('data-state'),
    className: String(element.className || ''),
  }));
  const selected = selectedFromAttributes(attributes);
  if (selected == null) throw new Error('Instrumental selected state is not readable; refusing to submit.');
  return selected;
}

export async function setInstrumental(page, target, mode) {
  const control = await instrumentalControl(page);
  if (!control) {
    const current = await readInstrumental(page, mode);
    if (current === target) return;
    if (current == null) {
      throw new Error('The Create page has no Instrumental control and the lyrics field is empty; ' +
        'the resulting track would be instrumental. Refusing to submit.');
    }
    throw new Error('This Create page has no Instrumental control, so the requested state cannot be set.');
  }
  const { role, locator } = control;
  const before = await readInstrumental(page, mode);
  if (before !== target) {
    if (role === 'checkbox') await locator.setChecked(target);
    else await locator.click();
  }
  if (await readInstrumental(page, mode) !== target) {
    throw new Error('Instrumental did not read back as ' + (target ? 'On' : 'Off') + '.');
  }
}

export async function waitForCreateForm(page, mode, timeoutMs = FORM_READY_TIMEOUT_MS) {
  const name = mode === 'custom' ? 'Advanced' : 'Simple';
  const deadline = Date.now() + timeoutMs;
  const notReady = (what) => new Error('Suno Create form did not render ' + what + ' within ' +
    timeoutMs + ' ms after navigation; the page layout may have changed.');
  // The mode tab paints well before the rest of the form, so treat the model
  // picker, which every package needs, as the signal that the form is usable.
  const stages = [
    ['the ' + name + ' mode tab', page.getByRole('tab', { name, exact: true })],
    ['the model picker', page.locator('button[aria-haspopup="menu"]').filter({ hasText: /^v[0-9]/ })],
  ];
  for (const [what, locator] of stages) {
    for (;;) {
      if (await visible(locator).count() === 1) break;
      if (Date.now() >= deadline) throw notReady(what);
      await page.waitForTimeout(250);
    }
  }
}

async function setMode(page, mode) {
  const name = mode === 'custom' ? 'Advanced' : 'Simple';
  const tab = await oneVisible(page.getByRole('tab', { name, exact: true }), name + ' tab');
  if (await tab.getAttribute('aria-selected') !== 'true') {
    await tab.click();
    await page.waitForTimeout(250);
  }
  if (await tab.getAttribute('aria-selected') !== 'true') {
    throw new Error('Suno Create mode did not read back as ' + name + '.');
  }
}

async function openMoreOptions(page) {
  let maxLabel = visible(page.getByText('Max Mode', { exact: true }));
  if (await maxLabel.count() === 0) {
    const more = await oneVisible(page.getByRole('button', { name: /More Options/ }), 'More Options');
    await more.click();
    await page.waitForTimeout(200);
    maxLabel = visible(page.getByText('Max Mode', { exact: true }));
  }
  if (await maxLabel.count() !== 1) throw new Error('Official Max Mode control is not uniquely visible.');
}

async function modelPicker(page) {
  return oneVisible(
    page.locator('button[aria-haspopup="menu"]').filter({ hasText: /^v[0-9]/ }),
    'model picker',
  );
}

async function readModel(page) {
  const picker = await modelPicker(page);
  return (await picker.innerText()).trim().split(/\r?\n/)[0];
}

async function setModel(page, model) {
  if (await readModel(page) !== model) {
    const picker = await modelPicker(page);
    await picker.click();
    const option = await oneVisible(
      page.getByRole('menuitemradio', { name: model, exact: false }),
      'model option ' + model,
    );
    await option.click();
    await page.waitForTimeout(200);
  }
  if (await readModel(page) !== model) throw new Error('Model did not read back as ' + model + '.');
}

async function durationControls(page) {
  const input = await oneVisible(page.locator('input[aria-label="Duration"]'), 'Duration input');
  const slider = await oneVisible(page.locator('[role="slider"][aria-label="Duration"]'), 'Duration slider');
  return { input, slider };
}

async function readDuration(page) {
  const { input, slider } = await durationControls(page);
  const display = String(await input.evaluate(element => element.value));
  const seconds = await readNumericAttribute(slider, 'aria-valuenow', 'Duration');
  const min = await readNumericAttribute(slider, 'aria-valuemin', 'Duration');
  const max = await readNumericAttribute(slider, 'aria-valuemax', 'Duration');
  if (!Number.isInteger(seconds) || !Number.isInteger(min) || !Number.isInteger(max)) {
    throw new Error('Duration slider state is incomplete; refusing to submit.');
  }
  if (parseDuration(display) !== seconds) throw new Error('Duration input and slider disagree.');
  return { display, seconds, min, max };
}

async function setDuration(page, seconds) {
  const { input } = await durationControls(page);
  const before = await readDuration(page);
  if (seconds < before.min || seconds > before.max) {
    throw new Error('Requested duration is outside the live Suno range (' + before.min + '–' + before.max + ' seconds).');
  }
  const display = formatDuration(seconds);
  if (before.seconds !== seconds) {
    await input.fill(display);
    await input.press('Enter');
    await page.waitForTimeout(250);
  }
  const after = await readDuration(page);
  if (after.seconds !== seconds || after.display !== display) {
    throw new Error('Duration did not read back as ' + display + ' (' + seconds + ' seconds).');
  }
  return after;
}

async function readNumericAttribute(locator, attribute, label) {
  const raw = await locator.getAttribute(attribute);
  if (raw == null || raw.trim() === '' || !Number.isInteger(Number(raw))) {
    throw new Error(label + ' ' + attribute + ' is not readable; refusing to submit.');
  }
  return Number(raw);
}

async function setSlider(page, label, value) {
  if (value == null) return null;
  const target = Math.round(value * 100);
  if (Math.abs(value * 100 - target) > 1e-6) {
    throw new Error(label + ' uses whole-percent steps; no submission was made.');
  }
  const slider = await oneVisible(
    page.locator('[role="slider"][aria-label="' + label + '"]'),
    label + ' slider',
  );
  const min = await readNumericAttribute(slider, 'aria-valuemin', label);
  const max = await readNumericAttribute(slider, 'aria-valuemax', label);
  if (!Number.isInteger(min) || !Number.isInteger(max) || target < min || target > max) {
    throw new Error(label + ' value is outside the live slider range.');
  }
  let current = await readNumericAttribute(slider, 'aria-valuenow', label);
  if (!Number.isInteger(current)) throw new Error(label + ' value is not readable.');
  if (current !== target) {
    await slider.click();
    await slider.press('Home');
    for (let step = min; step < target; step++) await slider.press('ArrowRight');
  }
  current = await readNumericAttribute(slider, 'aria-valuenow', label);
  if (current !== target) throw new Error(label + ' did not read back the requested value.');
  return current;
}

async function readSlider(page, label, expectedValue) {
  if (expectedValue == null) return null;
  const slider = await oneVisible(
    page.locator('[role="slider"][aria-label="' + label + '"]'),
    label + ' slider',
  );
  const value = await readNumericAttribute(slider, 'aria-valuenow', label);
  if (!Number.isInteger(value) || value !== Math.round(expectedValue * 100)) {
    throw new Error(label + ' did not read back the requested value; refusing to submit.');
  }
  return value;
}

async function readField(page, selector, label, contentEditable = false) {
  const field = await oneVisible(page.locator(selector), label);
  return String(await field.evaluate((element, editable) => editable ? element.innerText : element.value, contentEditable));
}

async function fillField(page, selector, value, label, contentEditable = false) {
  const field = await oneVisible(page.locator(selector), label);
  await field.fill(value);
  const readback = String(await field.evaluate((element, editable) => editable ? element.innerText : element.value, contentEditable));
  if (readback.replace(/\r\n/g, '\n').trim() !== String(value).replace(/\r\n/g, '\n').trim()) {
    throw new Error(label + ' did not read back correctly.');
  }
  return readback;
}

async function readCreditsRemaining(page) {
  const credits = await oneVisible(page.locator('button[aria-label^="Credits remaining"]'), 'credits remaining');
  const label = await credits.getAttribute('aria-label');
  const match = /^Credits remaining:\s*([\d,]+)$/.exec(label || '');
  if (!match) throw new Error('Exact remaining credit count is unavailable.');
  return Number(match[1].replace(/,/g, ''));
}

async function readPreSubmitState(page, item) {
  const titleValue = await readField(
    page,
    'input[placeholder="Song Title (Optional)"]',
    'song title input',
  );
  const contentSelectors = item.mode === 'custom'
    ? {
        lyrics: ['[aria-label="Lyrics editor"][contenteditable="true"]', true],
        styles: ['[data-testid="create-form-styles-wrapper"] textarea', false],
        exclusions: ['input[placeholder="Exclude styles"]', false],
      }
    : { prompt: ['textarea[rows="1"]:not([data-cowrite-input])', false] };
  for (const [key, [selector, contentEditable]] of Object.entries(contentSelectors)) {
    const observed = await readField(page, selector, key, contentEditable);
    const expected = item[key];
    if (observed.replace(/\r\n/g, '\n').trim() !== String(expected).replace(/\r\n/g, '\n').trim()) {
      throw new Error('Pre-submit readback mismatch for ' + key + '.');
    }
  }
  const duration = await readDuration(page);
  const vocalGender = await readChoice(
    await choiceGroup(page, 'Vocal Gender', ['Male', 'Female']),
    'Vocal Gender',
    ['Male', 'Female'],
  );
  const maxModeChoice = await readChoice(
    await choiceGroup(page, 'Max Mode', ['Off', 'On']),
    'Max Mode',
    ['Off', 'On'],
  );
  const instrumental = await readInstrumental(page);
  const model = await readModel(page);
  const weirdness = await readSlider(page, 'Weirdness', item.weirdness);
  const styleInfluence = await readSlider(page, 'Style Influence', item.styleInfluence);
  const create = await oneVisible(page.getByRole('button', { name: 'Create song', exact: true }), 'Create button');
  const enabled = await create.isEnabled();
  const state = {
    title: titleValue,
    durationSeconds: duration.seconds,
    vocalGender,
    maxMode: maxModeChoice === 'On',
    instrumental,
    model,
    weirdness,
    styleInfluence,
    contentVerified: Object.keys(contentSelectors),
    createEnabled: enabled,
  };
  for (const key of ['title', 'durationSeconds', 'vocalGender', 'maxMode', 'instrumental', 'model']) {
    if (state[key] !== item[key]) throw new Error('Pre-submit readback mismatch for ' + key + '.');
  }
  if (!state.createEnabled) throw new Error('Create is disabled; no submission was made.');
  return state;
}

export async function prepareSunoCreateForm(page, item) {
  await setMode(page, item.mode);
  await openMoreOptions(page);
  await setModel(page, item.model);
  if (item.mode === 'custom') {
    await fillField(page, '[aria-label="Lyrics editor"][contenteditable="true"]', item.lyrics, 'lyrics', true);
    await fillField(page, '[data-testid="create-form-styles-wrapper"] textarea', item.styles, 'styles');
    await fillField(page, 'input[placeholder="Exclude styles"]', item.exclusions, 'exclusions');
  } else {
    await fillField(page, 'textarea[rows="1"]:not([data-cowrite-input])', item.prompt, 'simple prompt');
  }
  // Read after the content is set: without an Instrumental control, filled
  // lyrics are what makes this package vocal instead of instrumental.
  await setInstrumental(page, false, item.mode);
  const title = await oneVisible(page.locator('input[placeholder="Song Title (Optional)"]'), 'song title input');
  await title.fill(item.title);
  if (String(await title.evaluate(element => element.value)) !== item.title) {
    throw new Error('Song title did not read back correctly.');
  }
  await setDuration(page, item.durationSeconds);
  await setChoice(page, 'Vocal Gender', ['Male', 'Female'], item.vocalGender);
  await setChoice(page, 'Max Mode', ['Off', 'On'], item.maxMode ? 'On' : 'Off');
  await setSlider(page, 'Weirdness', item.weirdness);
  await setSlider(page, 'Style Influence', item.styleInfluence);
  return readPreSubmitState(page, item);
}

export function atomicWriteJson(path, value) {
  const parent = dirname(path);
  mkdirSync(parent, { recursive: true });
  const temporary = path + '.' + process.pid + '.tmp';
  const fd = openSync(temporary, 'w', 0o600);
  try {
    writeFileSync(fd, JSON.stringify(value, null, 2) + '\n', 'utf8');
    fsyncSync(fd);
  } finally {
    closeSync(fd);
  }
  renameSync(temporary, path);
  const directoryFd = openSync(parent, 'r');
  try {
    fsyncSync(directoryFd);
  } finally {
    closeSync(directoryFd);
  }
}

function loadLedger(path, batchId, batchFingerprint, items, resume, grants, allowUncertain = false) {
  if (!existsSync(path)) {
    if (resume) throw new Error('--resume was requested but the ledger does not exist.');
    return {
      version: 1,
      batchId,
      manifestFingerprint: batchFingerprint,
      grants,
      createdAt: new Date().toISOString(),
      items: Object.fromEntries(items.map(item => [item.id, {
        fingerprint: item.fingerprint,
        status: 'pending',
      }])),
    };
  }
  if (!resume) throw new Error('Ledger already exists. Use --resume only after checking its states.');
  const ledger = JSON.parse(readFileSync(path, 'utf8'));
  if (ledger.batchId !== batchId || ledger.manifestFingerprint !== batchFingerprint) {
    throw new Error('Existing ledger does not match this batch manifest.');
  }
  if (JSON.stringify(ledger.grants) !== JSON.stringify(grants)) {
    throw new Error('Existing ledger has different batch limits; do not increase authorization while resuming.');
  }
  for (const item of items) {
    const entry = ledger.items?.[item.id];
    if (!entry || entry.fingerprint !== item.fingerprint) {
      throw new Error('Ledger package identity mismatch for ' + item.id + '.');
    }
    if (!['pending', 'armed', 'ambiguous', 'confirmed', 'failed-before-submit'].includes(entry.status)) {
      throw new Error('Ledger has an unknown status for package ' + item.id + '.');
    }
    if (!allowUncertain && ['armed', 'ambiguous'].includes(entry.status)) {
      throw new Error('Package ' + item.id + ' has an uncertain Create. Reconcile it before resuming.');
    }
  }
  return ledger;
}

export function reconcileNotSubmitted(ledger, packageId) {
  const entry = ledger.items?.[packageId];
  if (!entry) throw new Error('Package id is not present in the ledger.');
  if (!['armed', 'ambiguous'].includes(entry.status)) {
    throw new Error('Only an armed or ambiguous package can be reconciled as not submitted.');
  }
  ledger.items[packageId] = {
    ...entry,
    status: 'failed-before-submit',
    reconciledAt: new Date().toISOString(),
    reconciliation: {
      outcome: 'not-submitted',
      confirmedByOperator: true,
    },
  };
  return ledger.items[packageId];
}

function acquireLedgerLock(path) {
  const lockPath = path + '.lock';
  mkdirSync(dirname(path), { recursive: true });
  try {
    writeFileSync(lockPath, JSON.stringify({ pid: process.pid, createdAt: new Date().toISOString() }) + '\n', {
      flag: 'wx',
      mode: 0o600,
    });
  } catch (error) {
    if (error?.code === 'EEXIST') throw new Error('Batch ledger is already locked; inspect the running process or stale lock.');
    throw error;
  }
  return () => unlinkSync(lockPath);
}

function playwrightRequire() {
  try {
    return createRequire(import.meta.url)('playwright');
  } catch {}
  const locator = process.platform === 'win32' ? 'where.exe' : 'which';
  let cliPath;
  try {
    cliPath = execFileSync(locator, ['playwright-cli'], { encoding: 'utf8' }).trim().split(/\r?\n/)[0];
  } catch {
    throw new Error('Playwright is unavailable. Install @playwright/cli or add playwright to this project.');
  }
  const cliEntry = realpathSync(cliPath);
  return createRequire(cliEntry)('playwright');
}

async function findAuthenticatedContext(browser) {
  const matches = new Set();
  for (const context of browser.contexts()) {
    for (const page of context.pages()) {
      if (!/^https:\/\/suno\.com\//.test(page.url())) continue;
      try {
        if (await visible(page.locator('button[aria-label^="Credits remaining"]')).count()) {
          matches.add(context);
          break;
        }
      } catch {}
    }
  }
  if (matches.size !== 1) {
    throw new Error(matches.size
      ? 'More than one authenticated Suno browser context is available; select a single CDP profile.'
      : 'No authenticated Suno browser context is available on the configured CDP endpoint.');
  }
  return [...matches][0];
}

async function waitForSubmittedPair(page, requestCount, response, baselineIds, timeoutMs) {
  await page.waitForTimeout(750);
  if (requestCount() !== 1) throw new Error('Expected exactly one generation POST; outcome is ambiguous.');
  if (!response.ok()) throw new Error('Generation POST returned HTTP ' + response.status() + '; outcome is ambiguous.');
  const body = await response.json();
  const clips = Array.isArray(body?.clips) ? body.clips : [];
  const clipIds = clips.map(clip => clip?.id);
  if (clipIds.length !== 2 || new Set(clipIds).size !== 2 ||
      clipIds.some(id => !UUID.test(id || '') || baselineIds.has(id))) {
    throw new Error('Generation response did not contain exactly two new clip ids; outcome is ambiguous.');
  }
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const visibleIds = await page.locator('a[href^="/song/"]').evaluateAll(links =>
      links.map(link => (link.getAttribute('href') || '').split('/').pop()),
    );
    if (clipIds.every(id => visibleIds.includes(id))) return clipIds;
    await page.waitForTimeout(500);
  }
  throw new Error('Provider returned new clip ids, but the Create page did not show both; outcome is ambiguous.');
}

export async function submitOne(page, item, ledger, ledgerPath, remainingCredits) {
  const credits = await readCreditsRemaining(page);
  if (credits < remainingCredits) {
    throw new Error('Remaining Suno credits are below the outstanding batch estimate.');
  }
  const baselineIds = new Set((await page.locator('a[href^="/song/"]').evaluateAll(links =>
    links.map(link => (link.getAttribute('href') || '').split('/').pop()),
  )).filter(id => UUID.test(id)));
  const verified = await prepareSunoCreateForm(page, item);
  const finalVerified = await readPreSubmitState(page, item);
  if (JSON.stringify(verified) !== JSON.stringify(finalVerified)) {
    throw new Error('Form changed after read-back; no Create was submitted.');
  }
  ledger.items[item.id] = {
    ...ledger.items[item.id],
    status: 'armed',
    invocationId: randomUUID(),
    armedAt: new Date().toISOString(),
    verified: {
      durationSeconds: finalVerified.durationSeconds,
      vocalGender: finalVerified.vocalGender,
      maxMode: finalVerified.maxMode,
      instrumental: finalVerified.instrumental,
      model: finalVerified.model,
    },
  };
  atomicWriteJson(ledgerPath, ledger);

  const requests = [];
  const onRequest = request => {
    const url = new URL(request.url());
    if (url.pathname === GENERATE_PATH && request.method() === 'POST') requests.push(request);
  };
  page.on('request', onRequest);
  try {
    const create = await oneVisible(page.getByRole('button', { name: 'Create song', exact: true }), 'Create button');
    const [response] = await Promise.all([
      page.waitForResponse(response => {
        const url = new URL(response.url());
        return url.pathname === GENERATE_PATH && response.request().method() === 'POST';
      }, { timeout: 120_000 }),
      create.click(),
    ]);
    const clipIds = await waitForSubmittedPair(page, () => requests.length, response, baselineIds, 20_000);
    ledger.items[item.id] = {
      ...ledger.items[item.id],
      status: 'confirmed',
      completedAt: new Date().toISOString(),
      clipIds,
      links: clipIds.map(id => 'https://suno.com/song/' + id),
    };
    atomicWriteJson(ledgerPath, ledger);
    return { id: item.id, status: 'confirmed', clipIds };
  } catch (error) {
    ledger.items[item.id] = {
      ...ledger.items[item.id],
      status: 'ambiguous',
      error: String(error?.message || error).slice(0, 500),
      reconciledAt: null,
    };
    atomicWriteJson(ledgerPath, ledger);
    throw error;
  } finally {
    page.off('request', onRequest);
  }
}

function cliOptions() {
  return parseArgs({
    options: {
      help: { type: 'boolean', short: 'h' },
      manifest: { type: 'string' },
      submit: { type: 'boolean', default: false },
      'prepare-only': { type: 'boolean', default: false },
      resume: { type: 'boolean', default: false },
      ledger: { type: 'string' },
      'cdp-url': { type: 'string', default: 'http://127.0.0.1:9222' },
      'max-items': { type: 'string' },
      'max-credits': { type: 'string' },
      'confirm-batch': { type: 'string' },
      'reconcile-not-submitted': { type: 'string' },
    },
    allowPositionals: false,
    strict: true,
  }).values;
}

function usage() {
  return [
    'Suno batch Playwright runner',
    '',
    'Validate without browser actions:',
    '  node suno-batch-playwright.mjs --manifest batch.json',
    'Fill each package and read fields back, without Create:',
    '  node suno-batch-playwright.mjs --manifest batch.json --prepare-only',
    'Submit a bounded serial batch:',
    '  node suno-batch-playwright.mjs --manifest batch.json --submit --confirm-batch batch-id --max-items 8 --max-credits 80 --ledger .suno-create/batches/run.json',
    'Resume only pending items after confirming no armed or ambiguous item exists:',
    '  node suno-batch-playwright.mjs --manifest batch.json --submit --resume --confirm-batch batch-id --max-items 8 --max-credits 80 --ledger .suno-create/batches/run.json',
    'After checking Suno Library/history, mark an uncertain package not submitted so it can resume:',
    '  node suno-batch-playwright.mjs --manifest batch.json --reconcile-not-submitted package-id --confirm-batch batch-id --max-items 8 --max-credits 80 --ledger .suno-create/batches/run.json',
    '',
    'The runner never downloads clips. It requires a logged-in Chrome session exposed through CDP.',
  ].join('\n');
}

async function main() {
  const options = cliOptions();
  if (options.help) {
    process.stdout.write(usage() + '\n');
    return;
  }
  if (!options.manifest) throw new Error('--manifest is required.');
  if (options.submit && options['prepare-only']) throw new Error('Choose either --submit or --prepare-only.');
  const reconcileId = options['reconcile-not-submitted'];
  const reconciling = reconcileId != null;
  if (reconciling && (options.submit || options['prepare-only'] || options.resume)) {
    throw new Error('--reconcile-not-submitted runs alone; do not combine it with --submit, --prepare-only, or --resume.');
  }
  if (options.resume && !options.submit) throw new Error('--resume applies only with --submit.');
  const manifestPath = resolve(options.manifest);
  const rawManifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  const maxItems = options['max-items'] == null ? undefined : Number(options['max-items']);
  const maxCredits = options['max-credits'] == null ? undefined : Number(options['max-credits']);
  const manifest = validateManifest(rawManifest, {
    maxItems,
    maxCredits,
    submitting: options.submit || reconciling,
    baseDirectory: dirname(manifestPath),
  });
  const fingerprint = createHash('sha256')
    .update(JSON.stringify({ batchId: manifest.batchId, items: manifest.items.map(item => item.fingerprint) }))
    .digest('hex');

  if (!options.submit && !options['prepare-only'] && !reconciling) {
    process.stdout.write(JSON.stringify({
      status: 'manifest-valid',
      batchId: manifest.batchId,
      itemCount: manifest.items.length,
      estimatedCredits: manifest.estimatedCredits,
      creates: 0,
    }) + '\n');
    return;
  }

  let ledger;
  let ledgerPath;
  let releaseLedgerLock = () => {};
  if (options.submit || reconciling) {
    if (!options.ledger) throw new Error('--ledger is required for submission or reconciliation.');
    if (options['confirm-batch'] !== manifest.batchId) {
      throw new Error('--confirm-batch must exactly match the manifest batchId for submission or reconciliation.');
    }
    ledgerPath = resolve(options.ledger);
    releaseLedgerLock = acquireLedgerLock(ledgerPath);
    try {
      ledger = loadLedger(
        ledgerPath,
        manifest.batchId,
        fingerprint,
        manifest.items,
        options.resume || reconciling,
        { maxItems, maxCredits },
        reconciling,
      );
    } catch (error) {
      releaseLedgerLock();
      throw error;
    }
  }

  let chromium;
  let browser;
  let page;
  let ambiguous = false;
  try {
    if (reconciling) {
      const entry = reconcileNotSubmitted(ledger, reconcileId);
      atomicWriteJson(ledgerPath, ledger);
      process.stdout.write(JSON.stringify({
        batchId: manifest.batchId,
        id: reconcileId,
        status: entry.status,
        reconciliation: entry.reconciliation,
        creates: 0,
      }) + '\n');
      return;
    }
    ({ chromium } = playwrightRequire());
    browser = await chromium.connectOverCDP(options['cdp-url'], { timeout: 5_000 });
    const context = await findAuthenticatedContext(browser);
    page = await context.newPage();
    await page.goto(SUNO_CREATE, { waitUntil: 'domcontentloaded' });
    await waitForCreateForm(page, manifest.items[0].mode);

    if (options['prepare-only']) {
      const results = [];
      for (const item of manifest.items) {
        results.push({ id: item.id, status: 'prepared', verified: await prepareSunoCreateForm(page, item) });
      }
      process.stdout.write(JSON.stringify({ batchId: manifest.batchId, creates: 0, results }) + '\n');
      return;
    }

    const results = [];
    let creates = 0;
    for (const item of manifest.items) {
      const prior = ledger.items[item.id];
      if (prior.status === 'confirmed') {
        results.push({ id: item.id, status: 'confirmed', clipIds: prior.clipIds });
        continue;
      }
      if (['armed', 'ambiguous'].includes(prior.status)) {
        throw new Error('Package ' + item.id + ' is ambiguous; reconcile before resuming.');
      }
      const outstanding = manifest.items
        .filter(candidate => !['confirmed'].includes(ledger.items[candidate.id].status))
        .reduce((sum, candidate) => sum + candidate.estimatedCredits, 0);
      try {
        results.push(await submitOne(page, item, ledger, ledgerPath, outstanding));
        creates++;
      } catch (error) {
        ambiguous = ledger.items[item.id].status === 'ambiguous';
        if (!ambiguous) {
          ledger.items[item.id] = {
            ...ledger.items[item.id],
            status: 'failed-before-submit',
            error: String(error?.message || error).slice(0, 500),
          };
          atomicWriteJson(ledgerPath, ledger);
        }
        throw error;
      }
    }
    process.stdout.write(JSON.stringify({ batchId: manifest.batchId, creates, results }) + '\n');
  } finally {
    if (page && !ambiguous) await page.close().catch(() => {});
    if (browser) await browser.close().catch(() => {});
    releaseLedgerLock();
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(realpathSync(resolve(process.argv[1]))).href) {
  main().catch(error => {
    process.stderr.write('suno-batch-playwright: ' + String(error?.message || error) + '\n');
    process.exitCode = 1;
  });
}

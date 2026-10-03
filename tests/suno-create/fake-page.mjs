import { runInNewContext } from 'node:vm';

// Evaluate serialized callbacks in a separate realm, as Playwright does.
export function fakePage({ missingSliderAttribute, missingSliderLabel = 'Weirdness', clickError = false, responseError = false, onCreate, initialVocalGender = 'Female', initialDurationMode = 'Custom' } = {}) {
  const controls = new Map();
  const listeners = new Map();
  const clipIds = ['11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222'];
  const existingId = '33333333-3333-3333-3333-333333333333';
  let responseResolve;
  const state = { clicks: 0, panelOpen: false, mode: 'Advanced', vocalGender: initialVocalGender, durationMode: initialDurationMode };
  function control(key) {
    if (controls.has(key)) return controls.get(key);
    const element = {
      value: key.includes('Duration') ? '4:10' : '',
      innerText: '',
      getAttribute(name) {
        if (name === 'aria-selected' && ['Advanced', 'Simple'].includes(key)) return String(state.mode === key);
        if (name === 'aria-pressed' && ['Male', 'Female'].includes(key)) {
          if (state.vocalGender === 'unreadable') return null;
          return String(state.vocalGender === key || state.vocalGender === 'both');
        }
        if (name === 'aria-pressed' && ['Auto', 'Custom'].includes(key)) return String(state.durationMode === key);
        return attributes[name] ?? null;
      },
    };
    const attributes = {
      'aria-selected': 'true',
      'aria-pressed': String(key === 'Female' || key === 'On' || key === 'Custom'),
      'aria-label': 'Credits remaining: 100',

      'aria-valuenow': key.includes('Duration') ? '250' : '0',
      'aria-valuemin': '0',
      'aria-valuemax': key.includes('Duration') ? '600' : '100',
    };
    if (key.includes('slider') && key.includes(missingSliderLabel) && missingSliderAttribute) delete attributes[missingSliderAttribute];
    const locator = {
      filter() { return this; },
      first() { return this; },
      async count() {
        if (key.startsWith('absent:')) return 0;
        if (key.includes('Lyrics editor') && state.mode !== 'Advanced') return 0;
        if (key.includes('textarea[rows="1"]') && state.mode !== 'Simple') return 0;
        // The options toggle is always present. The Duration row only exists
        // once that section is expanded.
        if ((key === 'Custom' || key === 'Auto') && !state.panelOpen) return 0;
        if (key.includes('Duration') && (key.includes('input[') || key.includes('slider')) && state.durationMode === 'Auto') return 0;
        return 1;
      },
      async waitFor() {
        if (await this.count() === 0) throw new Error('Requested content is not visible in this mode');
      },
      async scrollIntoViewIfNeeded() {},
      locator() { return this; },
      getByRole(_role, { name }) { return control(name); },
      async getAttribute(name) {
        if (name === 'aria-expanded' && key === 'More Options') return String(state.panelOpen);
        return element.getAttribute(name);
      },
      async evaluate(fn, arg) { return runInNewContext('(' + fn.toString() + ')(element, arg)', { element, arg }); },
      async evaluateAll(fn, arg) {
        const ids = state.clicks ? [existingId, ...clipIds] : [existingId];
        const elements = ids.map(id => ({ getAttribute: () => '/song/' + id }));
        return runInNewContext('(' + fn.toString() + ')(elements, arg)', { elements, arg });
      },
      async fill(value) { element.value = value; element.innerText = value; },
      async innerText() { return 'v6'; },
      async isChecked() { return false; },
      async isEnabled() { return true; },
      async click() {
        if (key === 'More options' || key === 'More Options') { state.panelOpen = true; return; }
        if (key === 'Advanced' || key === 'Simple') { state.mode = key; return; }
        if (key === 'Male' || key === 'Female') { state.vocalGender = key; return; }
        if (key === 'Auto' || key === 'Custom') { state.durationMode = key; return; }
        if (key !== 'Create song') return;
        state.clicks++;
        onCreate?.();
        if (clickError) throw new Error('Create click failed');
        listeners.get('request')?.({ url: () => 'https://studio-api.suno.ai/api/generate/v2-web/', method: () => 'POST' });
        if (!responseError) responseResolve?.({ ok: () => true, json: async () => ({ clips: clipIds.map(id => ({ id })) }) });
      },
    };
    controls.set(key, locator);
    return locator;
  }
  return {
    state,
    async goto() {},
    async close() {},
    locator(selector) {
      // The options toggle is addressed by its aria-expanded attribute.
      if (typeof selector === 'string' && selector.includes('aria-expanded')) return control('More Options');
      return control(selector);
    },
    getByRole(role, { name }) {
      return control(name === 'Instrumental' && role !== 'checkbox' ? 'absent:' + role : name);
    },
    // The Duration row lives inside the More Options panel: its label is not
    // visible until that panel is expanded.
    getByText(text, { exact } = {}) {
      if (text === 'Duration' && exact && !state.panelOpen) return control('absent:duration-label');
      return control(text);
    },
    async waitForTimeout() {},
    on(event, callback) { listeners.set(event, callback); },
    off(event) { listeners.delete(event); },
    waitForResponse() {
      return new Promise((resolve, reject) => {
        responseResolve = resolve;
        if (responseError || clickError) setImmediate(() => reject(new Error('Response timeout')));
      });
    },
  };
}

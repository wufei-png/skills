import { runInNewContext } from 'node:vm';

// Evaluate serialized callbacks in a separate realm, as Playwright does.
export function fakePage({ missingSliderAttribute, missingSliderLabel = 'Weirdness', clickError = false, responseError = false, onCreate } = {}) {
  const controls = new Map();
  const listeners = new Map();
  const clipIds = ['11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222'];
  const existingId = '33333333-3333-3333-3333-333333333333';
  let responseResolve;
  const state = { clicks: 0 };
  function control(key) {
    if (controls.has(key)) return controls.get(key);
    const element = {
      value: key.includes('Duration') ? '4:10' : '',
      innerText: '',
      getAttribute(name) { return attributes[name] ?? null; },
    };
    const attributes = {
      'aria-selected': 'true',
      'aria-pressed': String(key === 'Female' || key === 'On'),
      'aria-label': 'Credits remaining: 100',
      'aria-valuenow': key.includes('Duration') ? '250' : '0',
      'aria-valuemin': '0',
      'aria-valuemax': key.includes('Duration') ? '600' : '100',
    };
    if (key.includes('slider') && key.includes(missingSliderLabel) && missingSliderAttribute) delete attributes[missingSliderAttribute];
    const locator = {
      filter() { return this; },
      async count() { return key.startsWith('absent:') ? 0 : 1; },
      locator() { return this; },
      getByRole(_role, { name }) { return control(name); },
      async getAttribute(name) { return element.getAttribute(name); },
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
    locator: control,
    getByText: control,
    getByRole(role, { name }) {
      return control(name === 'Instrumental' && role !== 'checkbox' ? 'absent:' + role : name);
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

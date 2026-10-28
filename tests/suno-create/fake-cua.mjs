// A small form model for testing the CUA adapter without a live account.
export function fakeCua() {
  const state = {
    durationMode: 'Auto', seconds: 200, durationMismatch: false, createClicks: 0,
    vocal: 'Female', max: 'On', personalize: 'Off',
    title: '', lyrics: '', styles: '', exclusions: '',
    sliders: { Weirdness: 35, 'Style Influence': 82, Variety: 0 },
  };

  class Locator {
    constructor(kind, name = '') { this.kind = kind; this.name = name; }
    filter(options = {}) {
      return this.kind === 'group' && options.has ? new Locator('group', options.has.name) : this;
    }
    and() { return this; }
    locator(selector) {
      if (this.kind === 'group' && this.name === 'Duration' && selector.startsWith('svg.')) return new Locator('reset');
      throw Error('Unknown nested selector ' + selector);
    }
    getByRole(role, { name }) { return new Locator('choice', `${this.name}:${name}`); }
    async count() {
      if (this.kind === 'duration-input' || this.kind === 'duration-slider' || this.kind === 'reset') return state.durationMode === 'Custom' ? 1 : 0;
      if (this.kind === 'choice' && this.name.startsWith('Duration:')) return state.durationMode === 'Auto' ? 1 : 0;
      return 1;
    }
    async waitFor() { if (await this.count() !== 1) throw Error('Control not visible'); }
    async getAttribute(attribute) {
      if (attribute === 'aria-selected') return 'true';
      if (attribute === 'aria-expanded') return 'true';
      if (attribute === 'aria-label') return 'Credits remaining: 100';
      if (attribute === 'aria-valuemin') return '0';
      if (attribute === 'aria-valuemax') return this.kind === 'duration-slider' ? '600' : this.name === 'Variety' ? '4' : '100';
      if (attribute === 'aria-valuenow') return String(this.kind === 'duration-slider' ? state.seconds + Number(state.durationMismatch) : state.sliders[this.name]);
      return null;
    }
    async evaluate(fn) {
      const value = this.kind === 'duration-input'
        ? `${Math.floor(state.seconds / 60)}:${String(state.seconds % 60).padStart(2, '0')}`
        : state[this.name];
      return fn({ value, children: (state.lyrics || '').split('\n').map(textContent => ({ textContent })) });
    }
    async evaluateAll(fn) {
      const choices = {
        'Vocal Gender': [['Female', state.vocal === 'Female'], ['Male', state.vocal === 'Male']],
        'Max Mode': [['On', state.max === 'On'], ['Off', state.max === 'Off']],
        Personalize: [['On', state.personalize === 'On'], ['Off', state.personalize === 'Off']],
        Duration: state.durationMode === 'Auto' ? [['Auto', true], ['Custom', false]] : [],
      }[this.name];
      return fn([{ querySelectorAll: () => choices.map(([text, on]) => ({
        textContent: text, className: '', getAttribute: key => key === 'data-selected' ? String(on) : null,
      })) }]);
    }
    async click() {
      if (this.kind === 'reset') state.durationMode = 'Auto';
      if (this.kind === 'choice') {
        const [group, value] = this.name.split(':');
        if (group === 'Duration') state.durationMode = value;
        if (group === 'Vocal Gender') state.vocal = value;
        if (group === 'Max Mode') state.max = value;
        if (group === 'Personalize') state.personalize = value;
      }
      if (this.kind === 'create') state.createClicks++;
    }
    async fill(value) {
      if (this.kind === 'duration-input') {
        const [minutes, seconds] = value.split(':').map(Number);
        state.seconds = minutes * 60 + seconds;
      } else state[this.name] = value;
    }
    async press(key) {
      if (this.name === 'lyrics' && key === 'Backspace') state.lyrics = '';
      if (this.kind === 'slider' && key.startsWith('Arrow')) state.sliders[this.name] += key === 'ArrowRight' ? 1 : -1;
    }
    async innerText() { return this.name; }
    async isEnabled() { return true; }
  }

  const playwright = {
    locator(selector) {
      if (selector === 'div.css-gwrmef') return new Locator('group');
      if (selector === 'input[aria-label="Duration"]') return new Locator('duration-input');
      if (selector.startsWith('textarea')) return new Locator('textbox', 'styles');
      return new Locator('intersection');
    },
    getByText(name) { return new Locator('label', name); },
    getByRole(role, { name }) {
      if (role === 'slider') return new Locator(name === 'Duration' ? 'duration-slider' : 'slider', name);
      if (role === 'textbox') return new Locator('textbox', {
        'Lyrics editor': 'lyrics', 'Song Title (Optional)': 'title', 'Exclude styles': 'exclusions',
      }[name]);
      if (name === 'Create song') return new Locator('create');
      return new Locator('control', typeof name === 'string' ? name : 'Credits');
    },
  };
  return { tab: { playwright }, state };
}

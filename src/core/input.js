// InputRouter from docs/04_RUNTIME_ARCHITECTURE.md, with the default keys from docs/05_CONTROLS_EXPLORATION.md.
// No DOM, so it runs under node --test. Only one context is live at a time, which is what stops input overlapping.
const MOVE = {
  KeyW: 'MoveForward', ArrowUp: 'MoveForward', KeyS: 'MoveBack', ArrowDown: 'MoveBack',
  KeyA: 'MoveLeft', ArrowLeft: 'MoveLeft', KeyD: 'MoveRight', ArrowRight: 'MoveRight',
};
const NAV = {
  KeyW: 'MenuUp', ArrowUp: 'MenuUp', KeyS: 'MenuDown', ArrowDown: 'MenuDown',
  KeyA: 'MenuLeft', ArrowLeft: 'MenuLeft', KeyD: 'MenuRight', ArrowRight: 'MenuRight',
};

// [BETA PROPOSAL] defaults. Pass another table to InputRouter for remapping (B-021).
export const BINDINGS = Object.freeze({
  none: {},
  menu: { ...NAV, Enter: 'MenuConfirm', Space: 'MenuConfirm', KeyE: 'MenuConfirm', Escape: 'MenuBack' },
  exploration: {
    ...MOVE, ShiftLeft: 'Sprint', ShiftRight: 'Sprint', Space: 'Jump', KeyE: 'Interact', KeyF: 'EchoVision',
    KeyM: 'Map', KeyJ: 'Journal', Tab: 'PartyOverlay', Escape: 'Pause', PointerDrag: 'Look', PointerWheel: 'Zoom',
    Digit1: 'PartySelect1', Digit2: 'PartySelect2', Digit3: 'PartySelect3', Digit4: 'PartySelect4',
  },
  // Space and Q do nothing here, and E only confirms: they mean defense inside a live window.
  combat: {
    ...NAV, Enter: 'MenuConfirm', KeyE: 'MenuConfirm', Tab: 'SwitchSelect', Escape: 'Pause', PointerDrag: 'Look',
    Digit1: 'PartySwitch1', Digit2: 'PartySwitch2', Digit3: 'PartySwitch3', Digit4: 'PartySwitch4',
  },
  // Live defense window. Escape is unbound on purpose: docs/05 forbids pausing during one.
  defense: { KeyQ: 'DefenseDodge', KeyE: 'DefenseParry', Space: 'DefenseJump' },
  dialogue: { Enter: 'DialogueAdvance', Space: 'DialogueAdvance', KeyE: 'DialogueAdvance', Escape: 'Pause' },
  cutscene: { Escape: 'Pause' },
});

export const MODE_CONTEXT = Object.freeze({
  Boot: 'none', MainMenu: 'menu', Exploration: 'exploration', Dialogue: 'dialogue', Cutscene: 'cutscene',
  Combat: 'combat', Rewards: 'menu', DefeatScreen: 'menu', Paused: 'menu',
});

export class InputRouter {
  #bindings;
  #context = 'none';
  #down = new Set();
  #stale = new Set();   // keys already down when the context changed; ignored until released

  constructor(bindings = BINDINGS) { this.#bindings = bindings; }

  get context() { return this.#context; }

  setContext(name) {
    if (!this.#bindings[name]) throw new Error(`Unknown input context: ${name}`);
    if (name === this.#context) return;
    this.#context = name;
    this.#stale = new Set(this.#down);
  }

  // Returns the action for a fresh press in the live context, or null. OS key repeat counts as nothing.
  keyDown(code) {
    if (this.#down.has(code)) return null;
    this.#down.add(code);
    return this.#bindings[this.#context][code] ?? null;
  }
  keyUp(code) { this.#down.delete(code); this.#stale.delete(code); }

  held(action) {
    const map = this.#bindings[this.#context];
    for (const code of this.#down) if (map[code] === action && !this.#stale.has(code)) return true;
    return false;
  }
  allows(action) { return Object.values(this.#bindings[this.#context]).includes(action); }

  // For window blur: the keyup would otherwise never arrive and the key would stick.
  releaseAll() { this.#down.clear(); this.#stale.clear(); }
}

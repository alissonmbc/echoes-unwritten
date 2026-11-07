// GameModeManager from docs/04_RUNTIME_ARCHITECTURE.md. No DOM, so it runs under node --test.
export const Mode = Object.freeze({
  Boot: 'Boot', MainMenu: 'MainMenu', Exploration: 'Exploration', Dialogue: 'Dialogue', Cutscene: 'Cutscene',
  Combat: 'Combat', Rewards: 'Rewards', DefeatScreen: 'DefeatScreen', Paused: 'Paused',
});

// Paused isn't listed here: it's only reachable through pause(), so resume() always has somewhere to return to.
const NEXT = {
  Boot: ['MainMenu'],
  MainMenu: ['Exploration'],
  Exploration: ['Dialogue', 'Cutscene', 'Combat'],
  Dialogue: ['Exploration'],
  Cutscene: ['Exploration'],
  Combat: ['Rewards', 'DefeatScreen', 'Exploration'],   // Exploration is the Flee path
  Rewards: ['Exploration'],
  DefeatScreen: ['Exploration'],
  Paused: [],
};
const PAUSABLE = new Set(['Exploration', 'Dialogue', 'Cutscene', 'Combat']);

export class ModeMachine {
  #mode = Mode.Boot;
  #resumeTo = null;
  #eventId = 0;
  #listeners = new Set();

  get mode() { return this.#mode; }
  get resumeTo() { return this.#resumeTo; }

  onChange(fn) { this.#listeners.add(fn); return () => this.#listeners.delete(fn); }

  // Each returns false and changes nothing if the move isn't legal, so nested Combat can't happen.
  to(next) {
    if (!NEXT[this.#mode].includes(next)) return false;
    this.#set(next);
    return true;
  }
  pause() {
    if (!PAUSABLE.has(this.#mode)) return false;
    this.#resumeTo = this.#mode;
    this.#set(Mode.Paused);
    return true;
  }
  resume() {
    if (this.#mode !== Mode.Paused) return false;
    const back = this.#resumeTo;
    this.#resumeTo = null;
    this.#set(back);
    return true;
  }
  quitToMenu() {
    if (this.#mode !== Mode.Paused) return false;
    this.#resumeTo = null;
    this.#set(Mode.MainMenu);
    return true;
  }

  #set(to) {
    const event = { id: ++this.#eventId, type: 'ModeChanged', from: this.#mode, to };
    this.#mode = to;
    for (const fn of this.#listeners) fn(event);
  }
}

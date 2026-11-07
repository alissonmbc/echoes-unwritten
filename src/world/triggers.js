// Circular trigger volumes. They fire on each entry and report ids only, so QuestManager can apply its own exactly-once rule.
export class TriggerSet {
  #inside = new Set();
  #eventId = 0;

  constructor(triggers, emit) { this.triggers = triggers; this.emit = emit; }

  update(x, z) {
    for (const t of this.triggers) {
      const within = (x - t.x) ** 2 + (z - t.z) ** 2 <= t.r * t.r;
      if (within && !this.#inside.has(t.id)) {
        this.#inside.add(t.id);
        this.emit({ id: ++this.#eventId, type: 'TriggerEntered', triggerId: t.id });
      } else if (!within) this.#inside.delete(t.id);
    }
  }
  reset() { this.#inside.clear(); }
}

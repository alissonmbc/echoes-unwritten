// Static collision: the corridor plus vertical cylinders { x, z, r, top }. No Three.js, so it runs under node --test.
// Anything lower than the step height can be walked onto, and anything you're above can be landed on.
export class CollisionWorld {
  #cells = new Map();

  constructor({ corridor, colliders = [], wallS = Infinity, cell = 4 }) {
    Object.assign(this, { corridor, colliders, wallS, cell });
    for (const c of colliders) {
      for (let i = this.#key(c.x - c.r); i <= this.#key(c.x + c.r); i++) for (let j = this.#key(c.z - c.r); j <= this.#key(c.z + c.r); j++) {
        const k = `${i},${j}`;
        if (!this.#cells.has(k)) this.#cells.set(k, []);
        this.#cells.get(k).push(c);
      }
    }
  }
  #key(v) { return Math.floor(v / this.cell); }

  // Cylinders within reach of a point. reach must stay under one cell for the 3x3 search to be enough.
  #near(x, z) {
    const out = new Set(), ci = this.#key(x), cj = this.#key(z);
    for (let i = ci - 1; i <= ci + 1; i++) for (let j = cj - 1; j <= cj + 1; j++) for (const c of this.#cells.get(`${i},${j}`) ?? []) out.add(c);
    return out;
  }

  // The highest surface under (x, z) that a body at height y could stand on.
  groundAt(x, z, y, step) {
    let h = this.corridor.heightAt(x, z);
    for (const c of this.#near(x, z)) {
      if (c.top <= y + step && c.top > h && (x - c.x) ** 2 + (z - c.z) ** 2 < c.r * c.r) h = c.top;
    }
    return h;
  }

  // Pushes a body out of anything too tall to step onto, then back onto the corridor. Sliding falls out of this.
  slide(x, z, y, radius, step) {
    for (let pass = 0; pass < 3; pass++) {
      let moved = false;
      for (const c of this.#near(x, z)) {
        if (c.top <= y + step) continue;
        const dx = x - c.x, dz = z - c.z, reach = c.r + radius, d2 = dx * dx + dz * dz;
        if (d2 >= reach * reach) continue;
        const d = Math.sqrt(d2);
        if (d < 1e-6) x = c.x + reach;   // dead centre: any direction will do
        else { x = c.x + dx / d * reach; z = c.z + dz / d * reach; }
        moved = true;
      }
      if (!moved) break;
    }
    return this.corridor.clamp(x, z);
  }

  solidAt(x, y, z, pad = 0) {
    const { u, s } = this.corridor.project(x, z);
    if (s > this.wallS) return true;
    if (y < this.corridor.roadY(u) + this.corridor.offset(s) + pad) return true;
    for (const c of this.#near(x, z)) if (y < c.top + pad && (x - c.x) ** 2 + (z - c.z) ** 2 < (c.r + pad) ** 2) return true;
    return false;
  }

  // How far from a to b is clear (0..1). The camera boom uses this so it stops short of walls.
  clearFraction(a, b, pad = .3, steps = 16) {
    for (let i = 1; i <= steps; i++) {
      const t = i / steps;
      if (this.solidAt(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, a.z + (b.z - a.z) * t, pad)) return (i - 1) / steps;
    }
    return 1;
  }
}

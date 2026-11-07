// The player controller from docs/05_CONTROLS_EXPLORATION.md. No Three.js, so it runs under node --test.
// World units are about .86 m (the hero stands about 2 units tall). All values are [BETA PROPOSAL].
export const TUNING = Object.freeze({
  walk: 2.2, sprint: 4.2,          // units per second
  accel: 14, decel: 18, airAccel: 5,
  gravity: 18, jumpSpeed: 6.2,     // a jump clears about 1 unit
  coyote: .12, jumpBuffer: .12,    // seconds of grace after leaving an edge, and before landing
  radius: .35, step: .4, snap: .3,
  slopeMax: Math.tan(50 * Math.PI / 180),
  turnRate: 12,
  maxStep: 1 / 120,                // sub-steps keep jumps and collisions the same at any frame rate
});

const turn = (a, b, k) => { const d = ((b - a + Math.PI) % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2) - Math.PI; return a + d * k; };

export class PlayerMotor {
  x = 0; y = 0; z = 0; vx = 0; vy = 0; vz = 0; heading = 0; grounded = true;
  #coyote = 0; #buffer = 0;

  constructor(world, tuning = TUNING) { this.world = world; this.cfg = tuning; }

  get speed() { return Math.hypot(this.vx, this.vz); }

  teleport(x, z, heading = this.heading) {
    Object.assign(this, { x, z, heading, vx: 0, vy: 0, vz: 0, grounded: true });
    this.y = this.world.corridor.heightAt(x, z);
    this.#coyote = this.#buffer = 0;
  }

  jump() { this.#buffer = this.cfg.jumpBuffer; }

  // intent: desired world-space direction, length 0..1
  step(dt, intent) {
    if (!(dt > 0)) return;   // the first frame can be zero, and speed is worked out by dividing by the step
    const n = Math.max(1, Math.ceil(dt / this.cfg.maxStep)), h = dt / n;
    for (let i = 0; i < n; i++) this.#tick(h, intent);
  }

  #tick(h, { x: ix, z: iz, sprint }) {
    const c = this.cfg, len = Math.hypot(ix, iz), scale = (sprint ? c.sprint : c.walk) * (len > 1 ? 1 / len : 1);
    const tx = ix * scale, tz = iz * scale, dx = tx - this.vx, dz = tz - this.vz, gap = Math.hypot(dx, dz);
    const rate = (this.grounded ? (len > .01 ? c.accel : c.decel) : c.airAccel) * h;
    if (gap <= rate) { this.vx = tx; this.vz = tz; } else { this.vx += dx / gap * rate; this.vz += dz / gap * rate; }
    if (len > .01) this.heading = turn(this.heading, Math.atan2(ix, iz), 1 - Math.exp(-h * c.turnRate));

    this.#coyote = this.grounded ? c.coyote : this.#coyote - h;
    this.#buffer -= h;
    if (this.#buffer > 0 && this.#coyote > 0) {
      this.vy = c.jumpSpeed; this.grounded = false; this.#coyote = this.#buffer = 0;
    }

    const w = this.world;
    let { x, z } = w.slide(this.x + this.vx * h, this.z + this.vz * h, this.y, c.radius, c.step);
    if (this.grounded) {
      // terrain only: a step up is a jump in height, which would read as an impossible slope
      const dist = Math.hypot(x - this.x, z - this.z), rise = w.corridor.terrainAt(x, z) - w.corridor.terrainAt(this.x, this.z);
      if (dist > 1e-6 && rise / dist > c.slopeMax) { x = this.x; z = this.z; }
    }
    // keep only the speed that actually happened, so walls don't store it up
    this.vx = (x - this.x) / h; this.vz = (z - this.z) / h;
    this.x = x; this.z = z;

    const ground = w.groundAt(x, z, this.y, c.step);
    if (this.grounded) {
      if (ground >= this.y - c.snap) this.y = ground;
      else this.grounded = false;
    }
    if (!this.grounded) {
      // surfaces are looked up from before the fall, or a frame's fall would drop straight through them
      const under = w.groundAt(x, z, this.y, 0);
      this.vy -= c.gravity * h; this.y += this.vy * h;
      if (this.vy <= 0 && this.y <= under) { this.y = under; this.vy = 0; this.grounded = true; }
    }
  }
}

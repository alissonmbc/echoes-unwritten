// The walkable strip along the road, in road coordinates: u along it (0..1), s across it (+s is toward the cliff).
// No Three.js, so it runs under node --test. frames are plain { p:{x,y,z}, r:{x,z} } samples of the road.
const lerp = (a, b, t) => a + (b - a) * t;
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

export class RoadCorridor {
  // profile: ascending [s, heightOffset] pairs describing the road's cross-section
  constructor({ frames, profile, sMin, sMax, uMin = 0, uMax = 1 }) {
    Object.assign(this, { frames, profile, sMin, sMax, uMin, uMax });
    this.last = frames.length - 1;
  }

  #frame(u) {
    const f = clamp(u, 0, 1) * this.last, i = Math.min(Math.floor(f), this.last - 1), k = f - i, a = this.frames[i], b = this.frames[i + 1];
    return { x: lerp(a.p.x, b.p.x, k), y: lerp(a.p.y, b.p.y, k), z: lerp(a.p.z, b.p.z, k), rx: lerp(a.r.x, b.r.x, k), rz: lerp(a.r.z, b.r.z, k) };
  }

  // Nearest point on the road's centre line. Coarse pass, then a fine one around the winner.
  project(x, z) {
    const { frames, last } = this, dist = i => (frames[i].p.x - x) ** 2 + (frames[i].p.z - z) ** 2;
    let best = 0, bestD = Infinity;
    for (let i = 0; i <= last; i += 8) { const d = dist(i); if (d < bestD) { bestD = d; best = i; } }
    for (let i = Math.max(0, best - 8), end = Math.min(last, best + 8); i <= end; i++) { const d = dist(i); if (d < bestD) { bestD = d; best = i; } }
    // refine between frames so u doesn't snap as you walk
    const a = frames[Math.max(0, best - 1)].p, b = frames[Math.min(last, best + 1)].p, dx = b.x - a.x, dz = b.z - a.z;
    const t = clamp(((x - a.x) * dx + (z - a.z) * dz) / (dx * dx + dz * dz), 0, 1);
    const u = (Math.max(0, best - 1) + t * (Math.min(last, best + 1) - Math.max(0, best - 1))) / last, f = this.#frame(u);
    return { u, s: (x - f.x) * f.rx + (z - f.z) * f.rz };
  }

  point(u, s) { const f = this.#frame(u); return { x: f.x + f.rx * s, z: f.z + f.rz * s }; }

  offset(s) {
    const p = this.profile;
    if (s <= p[0][0]) return p[0][1];
    for (let i = 1; i < p.length; i++) if (s <= p[i][0]) return lerp(p[i - 1][1], p[i][1], (s - p[i - 1][0]) / (p[i][0] - p[i - 1][0]));
    return p[p.length - 1][1];
  }
  roadY(u) { return this.#frame(u).y; }
  heightAt(x, z) { const { u, s } = this.project(x, z); return this.roadY(u) + this.offset(s); }

  // Keeps a position on the strip. Past the edges it slides along them, so you can't walk off the cliff.
  clamp(x, z) {
    const { u, s } = this.project(x, z), cu = clamp(u, this.uMin, this.uMax), cs = clamp(s, this.sMin, this.sMax);
    return cu === u && cs === s ? { x, z } : this.point(cu, cs);
  }
}

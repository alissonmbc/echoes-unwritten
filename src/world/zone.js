// Walkable floors added to the road: the road corridor plus flat rectangles. No Three.js, so it runs under node --test.
import { RoadCorridor } from './corridor.js';

const inside = (f, x, z) => x >= f.x0 && x <= f.x1 && z >= f.z0 && z <= f.z1;
const clampTo = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

export class ZonedSurface extends RoadCorridor {
  constructor(road, { floors, walls = [] }) { super(road); this.floors = floors; this.walls = walls; }

  floorAt(x, z) {
    let best = null;
    for (const f of this.floors) if (inside(f, x, z) && (!best || f.y > best.y)) best = f;
    return best;
  }
  heightAt(x, z) { return this.floorAt(x, z)?.y ?? super.heightAt(x, z); }

  // Whichever walkable area is nearest wins, which also gives sliding along every edge.
  clamp(x, z) {
    if (this.floorAt(x, z)) return { x, z };
    let best = super.clamp(x, z), bestD = (best.x - x) ** 2 + (best.z - z) ** 2;
    for (const f of this.floors) {
      const cx = clampTo(x, f.x0, f.x1), cz = clampTo(z, f.z0, f.z1), d = (cx - x) ** 2 + (cz - z) ** 2;
      if (d < bestD) { bestD = d; best = { x: cx, z: cz }; }
    }
    return best;
  }

  solidBox(x, y, z, pad = 0) {
    for (const w of this.walls) {
      if (x > w.x0 - pad && x < w.x1 + pad && z > w.z0 - pad && z < w.z1 + pad && y > w.y0 - pad && y < w.y1 + pad) return true;
    }
    return false;
  }
}

// Returns a list of problems, empty when the zone is sound. step is the motor's step height.
export function validateZone(zone, step) {
  const problems = [], seen = new Set();
  for (const { id } of [zone.spawn, ...zone.floors, ...zone.colliders, ...zone.triggers, ...zone.anchors]) {
    if (!id) problems.push('entry without an id');
    else if (seen.has(id)) problems.push(`duplicate id ${id}`);
    seen.add(id);
  }
  const touch = (a, b) => a.x0 <= b.x1 && b.x0 <= a.x1 && a.z0 <= b.z1 && b.z0 <= a.z1;
  zone.floors.forEach((a, i) => {
    if (a.x0 >= a.x1 || a.z0 >= a.z1) problems.push(`${a.id} has no area`);
    for (const b of zone.floors.slice(i + 1)) {
      if (touch(a, b) && Math.abs(a.y - b.y) > step) problems.push(`${a.id} and ${b.id} touch but differ by more than a step`);
    }
  });
  if (!zone.floors.some(f => inside(f, zone.spawn.x, zone.spawn.z))) problems.push('spawn is not on a floor');
  for (const c of zone.colliders) if (!zone.floors.some(f => inside(f, c.x, c.z))) problems.push(`${c.id} is not on a floor`);
  for (const t of zone.triggers) if (!(t.r > 0)) problems.push(`${t.id} has no radius`);
  return problems;
}

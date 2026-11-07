// Draws a zone's data as one merged mesh, so the whole greybox costs a single draw call.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

const TEXTURE_SIZE = 4;   // world units per repeat of the wall texture

function box(w, h, d, x, y, z) {
  const g = new THREE.BoxGeometry(w, h, d), uv = g.attributes.uv, n = g.attributes.normal;
  for (let i = 0; i < uv.count; i++) {
    // scale each face by its real size, or big slabs would stretch the texture
    const su = Math.abs(n.getX(i)) > .5 ? d : w, sv = Math.abs(n.getY(i)) > .5 ? d : h;
    uv.setXY(i, uv.getX(i) * su / TEXTURE_SIZE, uv.getY(i) * sv / TEXTURE_SIZE);
  }
  g.translate(x, y, z);
  return g;
}
const FOUNDATION = 40, BRIDGE_DEPTH = 1.4;

export function buildZoneMesh(zone, material) {
  const parts = [];
  for (const f of zone.floors) {
    const depth = f.id.endsWith('bridge') ? BRIDGE_DEPTH : FOUNDATION;
    parts.push(box(f.x1 - f.x0, depth, f.z1 - f.z0, (f.x0 + f.x1) / 2, f.y - depth / 2, (f.z0 + f.z1) / 2));
  }
  for (const w of zone.walls) {
    const low = w.y0 === 0 ? -FOUNDATION : w.y0;   // walls that start at the ground run down with the foundations
    parts.push(box(w.x1 - w.x0, w.y1 - low, w.z1 - w.z0, (w.x0 + w.x1) / 2, (w.y0 === 0 ? w.y1 + low : w.y1 + w.y0) / 2, (w.z0 + w.z1) / 2));
  }
  for (const p of zone.props) parts.push(box(p.w, p.h, p.d, p.x, p.y + p.h / 2, p.z));
  const mesh = new THREE.Mesh(mergeGeometries(parts), material);
  mesh.name = zone.id; mesh.castShadow = mesh.receiveShadow = true;
  parts.forEach(g => g.dispose());
  return mesh;
}

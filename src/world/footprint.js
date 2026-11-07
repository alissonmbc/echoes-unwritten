// Turns the points of a shape into solid cylinders on a grid, so collision follows real geometry
// and stays right when the art is rebuilt. points is a flat [x, z, x, z, ...] list.
export function footprintColliders(points, { top, cell = 1, radius = .75 }) {
  const cells = new Map();
  for (let i = 0; i < points.length; i += 2) {
    const k = `${Math.floor(points[i] / cell)},${Math.floor(points[i + 1] / cell)}`;
    const c = cells.get(k) ?? cells.set(k, { x: 0, z: 0, n: 0 }).get(k);
    c.x += points[i]; c.z += points[i + 1]; c.n++;
  }
  return [...cells.values()].map(c => ({ x: c.x / c.n, z: c.z / c.n, r: radius, top }));
}

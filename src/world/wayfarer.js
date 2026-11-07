// Wayfarer Echo Ruin and road anchors, from docs/06_LUMINA_WORLD_LEVEL_DESIGN.md. Pure data, stable ids.
// The ruin sits behind the road's start (z=45), and you walk it toward -z:
// terrace, bridge, upper court with the plinth, stairs, lower court, gate, road.
// Heights and sizes are a greybox. Triggers and anchors keep their ids when the art moves them (docs/26).
const FLOOR_Y = 1.5, STAIRS = 6, RISE = FLOOR_Y / STAIRS, TREAD = .8, STAIR_Z = 62;

const stairs = Array.from({ length: STAIRS }, (_, i) => ({
  id: `floor.ruins.stairs_${i + 1}`, x0: -2.5, x1: 2.5, z0: STAIR_Z + i * TREAD, z1: STAIR_Z + (i + 1) * TREAD, y: RISE * (i + 1),
}));
const STAIR_END = STAIR_Z + STAIRS * TREAD;

export const WAYFARER = Object.freeze({
  id: 'zone.wayfarer_ruins', sourceStatus: 'beta-proposal',
  spawn: { id: 'spawn.ruins.approach', x: 0, z: 98, heading: Math.PI },

  floors: [
    { id: 'floor.ruins.gate', x0: -3, x1: 3, z0: 45, z1: 51.5, y: 0 },
    { id: 'floor.ruins.lower_court', x0: -8, x1: 8, z0: 51.5, z1: STAIR_Z, y: 0 },
    ...stairs,
    { id: 'floor.ruins.upper_court', x0: -9, x1: 9, z0: STAIR_END, z1: 79, y: FLOOR_Y },
    { id: 'floor.ruins.bridge', x0: -2, x1: 2, z0: 79, z1: 91, y: FLOOR_Y },
    { id: 'floor.ruins.terrace', x0: -7, x1: 7, z0: 91, z1: 103, y: FLOOR_Y },
  ],

  // Solid to the camera and drawn. The player is already kept out because no floor runs under them.
  walls: [
    { x0: -8.5, x1: -3, z0: 50.5, z1: 51.5, y0: 0, y1: 3.4 },       // gate, left half broken down
    { x0: 3, x1: 8.5, z0: 50.5, z1: 51.5, y0: 0, y1: 5.2 },
    { x0: -9, x1: -8, z0: 50.5, z1: STAIR_Z + 1, y0: 0, y1: 3.6 },
    { x0: 8, x1: 9, z0: 50.5, z1: STAIR_Z + 1, y0: 0, y1: 4.6 },
    { x0: -9, x1: -2.5, z0: STAIR_Z, z1: STAIR_END, y0: 0, y1: 2.1 }, // retaining wall either side of the stairs
    { x0: 2.5, x1: 9, z0: STAIR_Z, z1: STAIR_END, y0: 0, y1: 2.1 },
    { x0: -10, x1: -9, z0: STAIR_END, z1: 80, y0: 0, y1: 5 },
    { x0: 9, x1: 10, z0: STAIR_END, z1: 80, y0: 0, y1: 6 },
    { x0: -9, x1: -2, z0: 79, z1: 80, y0: 0, y1: 4.2 },
    { x0: 2, x1: 9, z0: 79, z1: 80, y0: 0, y1: 5.4 },
    { x0: -2.3, x1: -2, z0: 80, z1: 91, y0: 1.5, y1: 2.1 },         // bridge parapets
    { x0: 2, x1: 2.3, z0: 80, z1: 91, y0: 1.5, y1: 2.1 },
    { x0: -7.4, x1: -7, z0: 91, z1: 103.4, y0: 1.5, y1: 2.1 },
    { x0: 7, x1: 7.4, z0: 91, z1: 103.4, y0: 1.5, y1: 2.1 },
    { x0: -7, x1: 7, z0: 103, z1: 103.4, y0: 1.5, y1: 2.1 },
  ],

  // The broken archway at the bridge head, and the plinth, stand on floors, so these need real collision.
  colliders: [
    { id: 'solid.ruins.arch_left', x: -2.9, z: 91.8, r: .6, top: Infinity },
    { id: 'solid.ruins.arch_right', x: 2.9, z: 91.8, r: .6, top: Infinity },
    { id: 'solid.ruins.echo_plinth', x: 0, z: 73, r: .9, top: Infinity },
  ],
  props: [
    { x: -2.9, y: 1.5, z: 91.8, w: 1.1, h: 5.4, d: 1.1 },
    { x: 2.9, y: 1.5, z: 91.8, w: 1.1, h: 3.2, d: 1.1 },
    { x: -1.6, y: 6.9, z: 91.8, w: 3.8, h: .8, d: 1.1 },            // what's left of the lintel
    { x: 0, y: 1.5, z: 73, w: 1.7, h: .35, d: 1.7 },
    { x: 0, y: 1.85, z: 73, w: 1.1, h: .75, d: 1.1 },
  ],

  // Road points use u and s. The arch stands in for the bridge until B-004's road decision is made.
  triggers: [
    { id: 'world.ruins.marker', x: 0, z: 85, r: 4 },
    { id: 'world.ruins.plinth_area', x: 0, z: 73, r: 4 },
    { id: 'world.ruins.gate', x: 0, z: 48, r: 3.5 },
    { id: 'world.road.camp_approach', u: .4, s: 0, r: 5 },
    { id: 'world.bridge_trigger', u: .62, s: 0, r: 4 },
    { id: 'world.lumina_gate', u: .92, s: 0, r: 4 },
  ],
  anchors: [
    { id: 'world.ruins.echo_plinth', x: 0, z: 73 },
    { id: 'anchor.ruins.echoform', x: 0, z: 57 },
    { id: 'raider_near_cart', u: .44, s: 1 },
    { id: 'raider_hill', u: .46, s: 4 },
  ],
});

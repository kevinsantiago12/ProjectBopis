// Paper layout for the linear slum level (the missing patrolman, user's scenario 2026-11-07).
// One source for the drawing, the measured sightlines and the build data:
//   node Tools/LevelGen/layout_linear_slums.mjs
// writes Design Document/Linear_Slums_Layout.html and Design Document/Linear_Slums_Layout.json.
// Units are metres from the NW corner, x east, y south. Building faces sit on the 1.5 m grid (the 3 m wall kit);
// interior partitions and openings may sit off it. Floors: 0 ground, 1 = +4 m (the bodega mezzanine is +3), 2 = +8 m.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const OUT_HTML = path.join(ROOT, "Design Document", "Linear_Slums_Layout.html");
const OUT_JSON = path.join(ROOT, "Design Document", "Linear_Slums_Layout.json");

// ---------------------------------------------------------------------------------------------------------------
// Sections (streamed: each is an _Art and a _Gameplay sublevel of one small persistent map)
const SECTIONS = [
  { id: 1, name: "Main street", ground: "0", mins: [4, 6], kind: "walk-around",
    what: "Night, people still out. Walk to the patrolman's last reported spot: no car. The street dead-ends at a padlocked lane gate.",
    label: [6, 101.5] },
  { id: 2, name: "Eskinita", ground: "+1.8", mins: [3, 4], kind: "search",
    what: "Round the gate through the eskinita and a wash yard, following the trail. Ends at a door in the yard wall, with steps down into the yard.",
    label: [49, 99] },
  { id: 3, name: "The yard", ground: "0", mins: [3, 5], kind: "reveal + fight",
    what: "The patrol car under a tarp in an improvised garage, signs of a struggle. Inspecting it starts the first major firefight.",
    label: [70, 89.5] },
  { id: 4, name: "Row houses", ground: "0 / +4", mins: [6, 8], kind: "fights",
    what: "Four row houses the gang has knocked through: kitchen, joined front rooms, a stair, the bedrooms. Out down H4's back stair.",
    label: [62, 54.5] },
  { id: 5, name: "Covered alley + bodega", ground: "0 / +3", mins: [6, 8], kind: "fights",
    what: "A lean-to roofed alley lined with plywood rooms, then a storage bodega with a mezzanine.",
    label: [86, 80.5] },
  { id: 6, name: "Holding house", ground: "−1.8", mins: [4, 6], kind: "fight + reveal",
    what: "Down steps into a guard room, then a corridor of plywood cells: bedding, water, food, belongings. A child's things. No one left.",
    label: [113.5, 57] },
  { id: 7, name: "Trap house", ground: "−1.8 (G, +4, +8)", mins: [8, 11], kind: "fights + end",
    what: "A courtyard, then a three-level trap house: double-height hall, stair, rooms and gallery, a wooden top storey. The forged documents.",
    label: [127.5, 20.6] },
];

// Walkable areas. kind: open (outside), cov (outside, roofed), room (walled), void (no floor: seen through, not stood on),
// off (walkable but out of bounds: the car's lane, the escape roof).
const A = (id, sec, f, kind, x0, y0, x1, y1, label = "", o = {}) => ({ id, sec, f, kind, x0, y0, x1, y1, label, ...o });
const AREAS = [
  // 1 Main street (Z-shaped so no straight run is longer than ~28 m)
  A("ST_A", 1, 0, "open", 0, 90, 25.5, 97.5, ""),
  A("ST_B", 1, 0, "open", 18, 75, 25.5, 90, ""),
  A("ST_C", 1, 0, "open", 25.5, 75, 42, 82.5, ""),
  A("LANE", 3, 0, "off", 42, 76.5, 60, 81, "car lane (gated both ends)"),
  // 2 Eskinita (+1.8, 3 m wide)
  A("E1", 2, 0, "open", 37.5, 82.5, 40.5, 88.5, ""),
  A("E2", 2, 0, "open", 37.5, 88.5, 48, 91.5, ""),
  A("WASH", 2, 0, "open", 48, 85.5, 55.5, 93, "wash yard"),
  A("E3", 2, 0, "open", 55.5, 85.5, 63, 88.5, ""),
  A("E4", 2, 0, "open", 63, 85.5, 66, 91.5, ""),
  // 3 The yard
  A("YARD", 3, 0, "open", 60, 70.5, 78, 85.5, "yard"),
  // 4 Row houses H1-H4 (6 x 12 m, 2 storeys). Ground: H1 + H2 open, H3 shut, H4 only its back room.
  A("H1_K", 4, 0, "room", 60, 66, 66, 70.5, "kitchen"),
  A("H1_F", 4, 0, "room", 60, 58.5, 66, 66, "front room"),
  A("H2_K", 4, 0, "room", 66, 66, 72, 70.5, "kitchen"),
  A("H2_F", 4, 0, "room", 66, 58.5, 72, 66, "front room"),
  A("H4_K", 4, 0, "room", 78, 66, 84, 70.5, "back room"),
  A("H2_U", 4, 1, "room", 66, 58.5, 72, 70.5, "H2 up"),
  A("H2_SW", 4, 1, "void", 70.2, 59.5, 72, 65.7, ""),
  A("H3_UF", 4, 1, "room", 72, 58.5, 78, 64.5, "H3 front"),
  A("H3_UB", 4, 1, "room", 72, 64.5, 78, 70.5, "H3 back"),
  A("H4_UF", 4, 1, "room", 78, 58.5, 84, 64.5, "H4 front"),
  A("H4_UB", 4, 1, "room", 78, 64.5, 84, 70.5, "H4 back"),
  A("H4_SW", 4, 1, "void", 78, 66.9, 82.55, 70.5, ""),   // H4's back stairwell (was a one-way floor hole until 2026-11-08)
  // 5 Covered alley + plywood rooms + bodega
  A("CA1", 5, 0, "cov", 84, 66, 99, 70.5, "covered alley"),
  A("PR1", 5, 0, "room", 84, 70.5, 89, 75, "plywood"),
  A("PR2", 5, 0, "room", 89, 70.5, 94, 75, "plywood"),
  A("PR3", 5, 0, "room", 94, 70.5, 99, 75, "plywood"),
  A("CA2", 5, 0, "open", 99, 49.5, 103.5, 75, ""),
  A("BOD", 5, 0, "room", 94.5, 36, 112.5, 49.5, "bodega (6 m high)"),
  A("MEZZ", 5, 1, "room", 94.5, 36, 112.5, 39.75, "mezzanine +3"),
  // 6 Holding house (-1.8)
  A("PASS", 6, 0, "room", 112.5, 39, 115.5, 42, ""),
  A("GUARD", 6, 0, "room", 115.5, 36, 123, 43.5, "guard room"),
  A("CORR", 6, 0, "room", 115.5, 43.5, 130.5, 45.75, ""),
  A("N1", 6, 0, "room", 123, 36, 126.75, 43.5, "cell"),
  A("N2", 6, 0, "room", 126.75, 36, 130.5, 43.5, "cell"),
  A("S1C", 6, 0, "room", 115.5, 45.75, 119.25, 51, "cell"),
  A("S2C", 6, 0, "room", 119.25, 45.75, 123, 51, "cell"),
  A("S3C", 6, 0, "room", 123, 45.75, 126.75, 51, "cell"),
  A("S4C", 6, 0, "room", 126.75, 45.75, 130.5, 51, "cell"),
  // 7 Courtyard + trap house (15 x 18 m)
  A("CYARD", 7, 0, "open", 130.5, 36, 139.5, 51, "courtyard"),
  A("G1", 7, 0, "room", 139.5, 39, 148.5, 48, "hall (to +8)"),
  A("G2", 7, 0, "room", 148.5, 39, 154.5, 48, "stash"),
  A("G3", 7, 0, "room", 139.5, 30, 147, 39, "stair hall"),
  A("G4", 7, 0, "room", 147, 30, 154.5, 39, "back room"),
  A("LAND", 7, 1, "room", 139.5, 30, 148.5, 32.25, "landing"),
  A("SWELL", 7, 1, "void", 139.5, 32.25, 141.75, 39, ""),
  A("R1", 7, 1, "room", 141.75, 32.25, 148.5, 39, "sleeping"),
  A("R2", 7, 1, "room", 148.5, 30, 154.5, 39, "kitchen"),
  A("GAL_N", 7, 1, "open", 139.5, 39, 148.5, 41.25, ""),
  A("GAL_E", 7, 1, "open", 146.25, 41.25, 148.5, 48, ""),
  A("HALLV", 7, 1, "void", 139.5, 41.25, 146.25, 48, "open to the hall"),
  A("R3", 7, 1, "room", 148.5, 39, 154.5, 48, "bunks"),
  A("SR", 7, 2, "room", 144, 34.5, 154.5, 42.75, "staging room"),
  A("PHOTO", 7, 2, "room", 144, 30, 148.5, 34.5, "photo"),
  A("FORGE", 7, 2, "room", 148.5, 30, 154.5, 34.5, "forging"),
  A("WSTAIR", 7, 2, "void", 152.4, 35.5, 154.2, 39, ""),
  A("TER_W", 7, 2, "open", 139.5, 30, 144, 48, ""),
  A("TER_S", 7, 2, "open", 144, 42.75, 154.5, 48, "terrace"),
  A("PLANK", 7, 2, "off", 140.25, 28.5, 141.75, 30, ""),
  A("NROOF", 7, 2, "off", 136.5, 22.5, 145.5, 28.5, "neighbour's roof"),
];

// Openings (segments on a wall). k: door1 (1 m; 1.1 m where it's a swinging door's jamb), door (2.25 m), knock (knocked-through,
// 3 m), garage, front (open-fronted), open (a doorway with no door). No drops (user 2026-11-08: "We have doors now. The use of one
// way drops in the current level, I do not like."): every way on is a door or steps, both ways.
const O = (f, ax, ay, bx, by, k) => ({ f, a: [ax, ay], b: [bx, by], k });
const OPENINGS = [
  O(0, 63.95, 85.5, 65.05, 85.5, "door1"),   // eskinita (+1.8) -> the yard: a door in the yard wall, a landing and steps down
  O(0, 60.5, 70.5, 62.75, 70.5, "door"),     // yard -> H1 kitchen (west end)
  O(0, 63.5, 66, 65.75, 66, "door"),         // kitchen -> front room (east end: no line through both)
  O(0, 66, 60.75, 66, 63.75, "knock"),       // H1 | H2 front rooms
  O(0, 66.75, 66, 69, 66, "door"),           // H2 front -> kitchen (first aid)
  O(0, 84, 67.125, 84, 69.375, "door"),      // H4 back room -> covered alley
  O(1, 72, 66.75, 72, 69, "knock"),          // H2 up | H3 back
  O(1, 74.25, 64.5, 76.5, 64.5, "door"),     // H3 back -> front
  O(1, 78, 60, 78, 62.25, "knock"),          // H3 front | H4 front
  O(1, 80.25, 64.5, 82.5, 64.5, "door"),     // H4 front -> back
  O(0, 84.5, 70.5, 88.5, 70.5, "front"),
  O(0, 89.5, 70.5, 93.5, 70.5, "front"),
  O(0, 94.5, 70.5, 98.5, 70.5, "front"),
  O(0, 99.75, 49.5, 102.75, 49.5, "door"),   // alley -> bodega (3 m)
  O(0, 112.5, 39.75, 112.5, 42, "door"),     // bodega -> passage
  O(0, 115.5, 39.75, 115.5, 42, "open"),     // passage -> guard room: the steps' foot comes through it, 1.8 m down
  O(0, 118.5, 43.5, 120.75, 43.5, "door"),
  O(0, 124.35, 43.5, 125.35, 43.5, "door1"),
  O(0, 128.1, 43.5, 129.1, 43.5, "door1"),
  O(0, 116.85, 45.75, 117.85, 45.75, "door1"),
  O(0, 120.6, 45.75, 121.6, 45.75, "door1"),
  O(0, 124.35, 45.75, 125.35, 45.75, "door1"),
  O(0, 128.1, 45.75, 129.1, 45.75, "door1"),
  O(0, 130.5, 43.5, 130.5, 45.75, "door"),   // corridor -> courtyard
  O(0, 139.5, 42, 139.5, 45, "garage"),      // courtyard -> hall
  O(0, 139.5, 36.75, 139.5, 38.25, "door1"), // courtyard -> stair hall (their side door)
  O(0, 148.5, 42.75, 148.5, 45, "door"),
  O(0, 142.5, 39, 144.75, 39, "door"),       // hall -> stair hall
  O(0, 147, 34.5, 147, 36.75, "door"),       // stair hall -> back room
  O(1, 144, 32.25, 146.25, 32.25, "door"),   // landing -> R1
  O(1, 144, 39, 146.25, 39, "door"),         // R1 -> gallery
  O(1, 148.5, 43.5, 148.5, 45.75, "door"),   // gallery -> R3
  O(1, 149.25, 39, 151.5, 39, "door"),       // R3 -> R2
  O(2, 145.5, 34.5, 146.5, 34.5, "door1"),   // staging -> photo
  O(2, 150, 34.5, 151, 34.5, "door1"),       // staging -> forging
  O(2, 144, 37.5, 144, 39.75, "door"),       // staging -> terrace
];
// Closed barriers between open areas (block movement and sight)
const BARRIERS = [
  { f: 0, a: [42, 76.5], b: [42, 81], k: "gate", label: "padlocked gate" },
  { f: 0, a: [60, 76.5], b: [60, 81], k: "gate", label: "yard gate (shut)" },
  { f: 0, a: [60, 85.5], b: [63.95, 85.5], k: "wall", label: "yard wall" },     // the eskinita's north wall, either side of the door
  { f: 0, a: [65.05, 85.5], b: [66, 85.5], k: "wall", label: "yard wall" },
];
// Stairs: r on base floor f, up = direction you face going up; z0 = the foot's height above floor f's datum (default 0).
// New ones go at the end: the generator finds the mezzanine's stair by its index (2).
const STAIRS = [
  { f: 0, r: [37.5, 84, 40.5, 87], up: "S", rise: 1.8, label: "steps +1.8" },
  { f: 0, r: [70.2, 59.5, 72, 65.7], up: "S", rise: 4 },
  { f: 0, r: [94.75, 39.75, 96.55, 44.5], up: "N", rise: 3 },
  { f: 0, r: [139.75, 32.25, 141.55, 38.4], up: "N", rise: 4 },
  { f: 1, r: [152.4, 33, 154.2, 39], up: "S", rise: 4, label: "wooden" },
  // In place of the drops (2026-11-08). The kit's 36 degrees: 2.5 m of run for 1.8 m, 2.75 m for 2 m.
  { f: 0, r: [63.5, 81.5, 65.5, 84], up: "S", rise: 1.8, label: "steps +1.8" },          // the yard up to the landing at the door
  { f: 0, r: [79.8, 66.9, 82.55, 68.7], up: "W", rise: 2 },                             // H4 back stair, lower flight (foot by the back door)
  { f: 0, r: [79.8, 68.7, 82.55, 70.5], up: "E", rise: 2, z0: 2 },                      // H4 back stair, upper flight (top at +4)
  { f: 0, r: [113.6, 39.75, 116.1, 42], up: "W", rise: 1.8, z0: -1.8, label: "steps" },  // passage down into the guard room
];
// Landings: flat floor at z above floor f's datum, open beside it on the yard (railed)
const LANDINGS = [
  { f: 0, r: [63.5, 84, 65.5, 85.5], z: 1.8, label: "landing +1.8", rail: true },   // inside the yard door; overlooks the car
  { f: 0, r: [78, 66.9, 79.8, 70.5], z: 2, label: "+2" },                           // H4 back stair's half landing
];
// Cover: low = dive past, tall = blocks sight
const C = (f, x0, y0, x1, y1, tall, label = "") => ({ f, r: [x0, y0, x1, y1], tall, label });
const COVER = [
  C(0, 16.5, 90.6, 21, 92.8, true, "jeepney"),
  C(0, 19.5, 80.9, 21.3, 82.7, false, "table"),
  C(0, 26.5, 76, 28.3, 78.4, false, "tricycle"),
  C(0, 61.4, 72.2, 63.4, 76.8, false, "car + tarp"),
  C(0, 66, 80, 67.6, 81.4, false, "drums"),
  C(0, 71.5, 82.2, 74, 83.4, false, "blocks"),
  C(0, 73.8, 73.6, 75.8, 74.4, false, "motorbike"),
  C(0, 62.8, 62.6, 65.2, 63.5, false, "sofa"),
  C(0, 67.6, 61.2, 69.2, 62.8, false, "table"),
  C(0, 88.5, 67.4, 90.5, 68.6, false, "sacks"),
  C(0, 98.6, 44.6, 102.4, 46, true, "pallets"),
  C(0, 104.6, 41.6, 106.4, 44.6, true, "pallets"),
  C(0, 109.2, 39.3, 110.4, 42.45, true, "pallets"),
  C(0, 108.4, 45.4, 110.8, 47, false, "sacks"),
  C(0, 100.4, 40.8, 102, 42.2, false, "sacks"),
  C(0, 118.6, 38.4, 120, 39.8, false, "card table"),
  C(0, 133, 43.8, 137.4, 45.5, true, "van"),
  C(0, 134.4, 47.6, 138, 49.2, false, "owner-type jeep"),
  C(0, 50.5, 88, 53, 90.5, true, "tank + drums"),
  C(0, 99, 58.5, 101.7, 60, true, "crates"),
  C(0, 100.8, 63, 103.5, 64.5, true, "tank stand"),
  C(0, 131.4, 37.2, 132.9, 38.4, false, "drums"),
  C(0, 142.6, 43.2, 144.6, 45, false, "crates"),
  C(0, 150, 41.2, 152.6, 42.6, false, "table"),
  C(2, 147.2, 37.6, 150.4, 39.2, false, "table"),
  C(2, 141, 44, 142.2, 45.2, false, "drums"),
];
const ROOFS = [
  { f: 0, r: [60, 70.5, 67.5, 85.5], label: "garage roof" },
  { f: 0, r: [84, 66, 99, 70.5], label: "" },
];

// Fights: enemies (c = crouched), wave doors, label position
const FIGHTS = [
  { id: "F1", sec: 3, room: "Yard", start: 3, wave: 3, max: 4, trigger: "I3 done: they've seen you", f: 0,
    foes: [[63, 72.2], [68, 73.6], [71, 71.6]], waveDoors: [[78, 77.6]], lab: [73.4, 79],
    note: "The first major firefight. The three come out of H1's back door; the wave comes through the east door. The car is low cover under the garage roof." },
  { id: "F2", sec: 4, room: "H1 kitchen", start: 2, wave: 0, max: 2, trigger: "the back door", f: 0,
    foes: [[65, 67.4], [61, 68.6, "c"]], lab: [63.4, 69.7], note: "Close quarters, right inside the door." },
  { id: "F3", sec: 4, room: "H1 + H2 front rooms", start: 4, wave: 0, max: 4, trigger: "seen or heard, or the kitchen door", f: 0,
    foes: [[61.6, 60.2], [64, 64.4, "c"], [68.2, 59.8], [69.2, 64.2]], lab: [62.6, 65.2],
    note: "12 x 7.5 m once the party wall is knocked through. A sofa and a table. The stair up is in the far corner." },
  { id: "F4", sec: 4, room: "Upstairs H3 + H4", start: 3, wave: 0, max: 3, trigger: "the knock-through into H3", f: 1,
    foes: [[74.6, 61.2, "c"], [81.4, 60.4], [83.2, 67.6]], lab: [81, 63.7],
    note: "Room to room, never more than 9 m. One holds the head of H4's back stair, the way down and out." },
  { id: "F5", sec: 5, room: "Covered alley", start: 4, wave: 0, max: 4, trigger: "the alley", f: 0,
    foes: [[86.5, 73, "c"], [91.5, 73.4, "c"], [96.6, 72.4], [97.6, 67.4]], lab: [91.5, 64.8],
    note: "A low lean-to roof and three open-fronted plywood rooms on the south side. Dim." },
  { id: "F6", sec: 5, room: "Bodega", start: 4, wave: 2, max: 4, trigger: "the door", f: 0,
    foes: [[99.4, 47.6, "c"], [103.4, 43.4], [109.6, 44.2], [107, 37.9, "", 1]], waveDoors: [[112.5, 40.9]], lab: [104, 48.4],
    note: "Pallet stacks inside the door cut the 37 m line down the alley. One waits on the mezzanine." },
  { id: "F7", sec: 6, room: "Guard room", start: 3, wave: 0, max: 3, trigger: "the passage steps", f: 0,
    foes: [[118, 37.3, "c"], [121.8, 37.4], [121.4, 41.8]], lab: [119.2, 35],
    note: "A card table. Then the cells, quiet." },
  { id: "F8", sec: 7, room: "Courtyard", start: 4, wave: 0, max: 4, trigger: "the corridor's end door", f: 0,
    foes: [[136.4, 40], [137.6, 46.6], [132.6, 48.8, "c"], [138.2, 38.6]], waveDoors: [[139.5, 43.5], [139.5, 37.5]], lab: [134.8, 50.5],
    note: "They come out of the trap house as you leave the cells. The owner-type jeep is the cover." },
  { id: "F9", sec: 7, room: "Hall (G1)", start: 5, wave: 0, max: 5, trigger: "the garage door", f: 0,
    foes: [[142, 41.6], [145.4, 46.2, "c"], [147.2, 42], [141, 47], [147.4, 44.4, "", 1]], lab: [144, 49.6],
    note: "Double height. One on the gallery above, which you'll walk later." },
  { id: "F10", sec: 7, room: "Stair hall + landing", start: 3, wave: 0, max: 3, trigger: "the stair hall door", f: 0,
    foes: [[145, 36.6, "c"], [143, 31.2, "", 1], [146.8, 31, "", 1]], lab: [143.5, 29],
    note: "Two wait on the landing at +4, shooting down the stair." },
  { id: "F11", sec: 7, room: "+4 rooms + gallery", start: 3, wave: 0, max: 3, trigger: "the top of the stair", f: 1,
    foes: [[146.4, 36.4, "c"], [151.6, 46.2], [150.2, 35.6]], lab: [151.5, 49.2],
    note: "A loop: sleeping room, gallery, bunks, kitchen. The wooden stair up is in the kitchen." },
  { id: "F12", sec: 7, room: "Staging room (+8)", start: 4, wave: 2, max: 4, trigger: "the top of the wooden stair", f: 2,
    foes: [[146.4, 36.4], [149.6, 41.2, "c"], [151.2, 37.6], [147.4, 40.6]], waveDoors: [[142, 38.6]], lab: [147.6, 47.4],
    note: "The last fight and its kill cam. The wave comes in from the terrace. Survivors run for the plank to the neighbour's roof (“drives off”)." },
];
// Inspects (the new interactable): req = the route waits on it
const INSPECTS = [
  { id: "I1", f: 0, x: 33, y: 81.2, sec: 1, name: "Last reported spot", req: false,
    src: "scenario", what: "No patrol car where it should be.", sug: "Fresh tyre scuffs at the kerb, a broken tail-light lens.", does: "" },
  { id: "I2", f: 0, x: 40.8, y: 78.6, sec: 1, name: "Padlocked lane gate", req: false,
    src: "suggestion", what: "Signs of disturbance lead on.", sug: "A new padlock, a scrape of police paint on the post, tyre marks under the gate: the car went in here. You go round.", does: "" },
  { id: "I3", f: 0, x: 64.6, y: 75.6, sec: 3, name: "The patrol car", req: true,
    src: "scenario", what: "The missing car under a large tarp, pushed into an improvised garage.", sug: "", does: "Saves CP2, then starts F1." },
  { id: "I4", f: 0, x: 65, y: 79.2, sec: 3, name: "Signs of a struggle", req: false,
    src: "scenario", what: "Signs of a struggle around the car.", sug: "", does: "" },
  { id: "I5", f: 0, x: 121.1, y: 48.6, sec: 6, name: "A cell", req: false,
    src: "scenario", what: "Bedding, bottled water, food containers, personal items: people were held here, recently.", sug: "", does: "" },
  { id: "I6", f: 0, x: 124.9, y: 48.6, sec: 6, name: "A child's things", req: false,
    src: "scenario", what: "A child's backpack, small shoes, a school ID. Never graphic.", sug: "", does: "" },
  { id: "I7", f: 2, x: 146.25, y: 32.25, sec: 7, name: "Photo corner", req: false,
    src: "suggestion", what: "", sug: "A backdrop sheet, a camera, ID-size prints: where the photographs on the documents came from.", does: "" },
  { id: "I8", f: 2, x: 151.5, y: 32.2, sec: 7, name: "The forged documents", req: true,
    src: "scenario", what: "Forged IDs and passports for the missing: some incomplete, some with photos and false names. Navarro takes them.", sug: "", does: "Ends the level (ALevelExitTrigger::Fire)." },
];
const CHECKPOINTS = [
  { id: "CP1", f: 0, x: 3, y: 93.75, sec: 1, at: "level start" },
  { id: "CP2", f: 0, x: 66.6, y: 74.4, sec: 3, at: "the car inspected (before F1)" },
  { id: "CP3", f: 0, x: 61.6, y: 71.8, sec: 4, at: "H1's back door" },
  { id: "CP4", f: 0, x: 85.4, y: 68.25, sec: 5, at: "H4's back door, into the covered alley" },
  { id: "CP5", f: 0, x: 101.25, y: 53.4, sec: 5, at: "the alley before the bodega" },
  { id: "CP6", f: 0, x: 116.9, y: 40.9, sec: 6, at: "the foot of the passage steps" },
  { id: "CP7", f: 0, x: 131.6, y: 44.6, sec: 7, at: "the courtyard" },
  { id: "CP8", f: 1, x: 140.6, y: 31.1, sec: 7, at: "the landing at +4" },
];
// Level 1: no ammo, weapons or grenades are placed (user, 2026-11-07). Only first aid.
const PICKUPS = [
  { f: 0, x: 70.6, y: 69.2, label: "first aid" },
  { f: 0, x: 96.2, y: 47.8, label: "first aid" },
  { f: 0, x: 152.4, y: 33.4, label: "first aid" },
];
// Level 1 arms, for Navarro and the gunmen (user, 2026-11-07: "For Level 1, only .45 pistols and shotguns", then "and revolvers actually")
const ARMS = ".45 pistols, revolvers and shotguns only";
const CIVILIANS = [[35.4, 76.4], [36.8, 76.9], [38, 76.2], [19.3, 80.4], [21.6, 80.4], [19.3, 83.4], [21.6, 83.4], [12.2, 93.6], [7.6, 96.4], [23.2, 92.4], [30.4, 81.4], [49.4, 91.6]];
// Section borders. All two-way (2026-11-08): every one but the eskinita's mouth (a bend) is a swinging door.
const CONNECTORS = [
  { from: 1, to: 2, a: [37.5, 82.5], b: [40.5, 82.5], door: false, note: "the eskinita mouth" },
  { from: 2, to: 3, a: [63.95, 85.5], b: [65.05, 85.5], door: true, note: "a door in the yard wall, then steps down into the yard" },
  { from: 3, to: 4, a: [60.5, 70.5], b: [62.75, 70.5], door: true, note: "H1's back door" },
  { from: 4, to: 5, a: [84, 67.125], b: [84, 69.375], door: true, note: "H4's back door, at the foot of its back stair" },
  { from: 5, to: 6, a: [112.5, 39.75], b: [112.5, 42], door: true, note: "the bodega's back door, then steps down 1.8 m" },
  { from: 6, to: 7, a: [130.5, 43.5], b: [130.5, 45.75], door: true, note: "the corridor's end door" },
];
const STREAM_NOTE = "Every border is a swinging door (the eskinita's mouth is a bend), and every way through goes both ways: no drops. "
  + "Whichever way you walk, crossing into a section loads the next one beyond it and unloads the one furthest behind. "
  + "A border door stays shut until the section behind it is loaded, and unloading waits until you're a few metres past a door, so stepping back and forth through it doesn't reload anything. "
  + "A section remembers what's done (fights, pickups, inspects) when it unloads, so walking back never brings the dead back.";
const START = [3, 93.75];
const FLEE = [[150, 38.6], [144.4, 38.6], [141, 36], [141, 30], [141, 26.4]];

// ---------------------------------------------------------------------------------------------------------------
// Raster for sightlines (0.25 m cells). 0 solid, 1 open (stand + see), 2 see-through only (void, out of bounds)
const CELL = 0.25, GX0 = -10, GY0 = 14, GX1 = 166, GY1 = 106;
const NX = Math.round((GX1 - GX0) / CELL), NY = Math.round((GY1 - GY0) / CELL);
function rasterFloor(f) {
  const g = new Uint8Array(NX * NY), sec = new Uint8Array(NX * NY);
  const rect = (x0, y0, x1, y1, v, s) => {
    const i0 = Math.max(0, Math.round((x0 - GX0) / CELL)), i1 = Math.min(NX, Math.round((x1 - GX0) / CELL));
    const j0 = Math.max(0, Math.round((y0 - GY0) / CELL)), j1 = Math.min(NY, Math.round((y1 - GY0) / CELL));
    for (let j = j0; j < j1; j++) for (let i = i0; i < i1; i++) { g[j * NX + i] = v; if (s !== undefined) sec[j * NX + i] = s; }
  };
  const areas = AREAS.filter(a => a.f === f);
  for (const a of areas) rect(a.x0, a.y0, a.x1, a.y1, a.kind === "void" || a.kind === "off" ? 2 : 1, a.kind === "void" || a.kind === "off" ? 0 : a.sec);
  const W = 0.25;
  for (const a of areas.filter(a => a.kind === "room")) {
    rect(a.x0, a.y0, a.x1, a.y0 + W, 0); rect(a.x0, a.y1 - W, a.x1, a.y1, 0);
    rect(a.x0, a.y0, a.x0 + W, a.y1, 0); rect(a.x1 - W, a.y0, a.x1, a.y1, 0);
  }
  for (const o of OPENINGS.filter(o => o.f === f)) {
    const [ax, ay] = o.a, [bx, by] = o.b;
    if (ax === bx) for (const a of areas) { if (a.kind === "void") continue; if (ax >= a.x0 - 0.01 && ax <= a.x1 + 0.01 && Math.max(ay, a.y0) < Math.min(by, a.y1)) rect(ax - 0.3, Math.max(ay, a.y0 + W), ax + 0.3, Math.min(by, a.y1 - W), 1); }
    else for (const a of areas) { if (a.kind === "void") continue; if (ay >= a.y0 - 0.01 && ay <= a.y1 + 0.01 && Math.max(ax, a.x0) < Math.min(bx, a.x1)) rect(Math.max(ax, a.x0 + W), ay - 0.3, Math.min(bx, a.x1 - W), ay + 0.3, 1); }
  }
  for (const b of BARRIERS.filter(b => b.f === f)) rect(Math.min(b.a[0], b.b[0]) - 0.15, Math.min(b.a[1], b.b[1]) - 0.15, Math.max(b.a[0], b.b[0]) + 0.15, Math.max(b.a[1], b.b[1]) + 0.15, 0);
  for (const c of COVER.filter(c => c.f === f && c.tall)) rect(...c.r, 0);
  return { g, sec };
}
function longestSightlines(f) {
  const { g, sec } = rasterFloor(f);
  const see = (x, y) => { const i = Math.floor((x - GX0) / CELL), j = Math.floor((y - GY0) / CELL); return i >= 0 && j >= 0 && i < NX && j < NY && g[j * NX + i] > 0; };
  const best = {};
  const DIRS = 180, STEP = 0.25, HALF = 0.6;
  for (let y = GY0 + 0.375; y < GY1; y += 0.75) for (let x = GX0 + 0.375; x < GX1; x += 0.75) {
    const i = Math.floor((x - GX0) / CELL), j = Math.floor((y - GY0) / CELL), k = j * NX + i;
    if (g[k] !== 1 || !sec[k]) continue;
    const s = sec[k];
    for (let d = 0; d < DIRS; d++) {
      const t = (d / DIRS) * 2 * Math.PI, dx = Math.cos(t), dy = Math.sin(t), px = -dy * HALF, py = dx * HALF;
      if (!see(x + px, y + py) || !see(x - px, y - py)) continue;
      let L = 0;
      while (L < 120) { const nx = x + dx * (L + STEP), ny = y + dy * (L + STEP); if (!see(nx, ny) || !see(nx + px, ny + py) || !see(nx - px, ny - py)) break; L += STEP; }
      if (!best[s] || L > best[s].len) best[s] = { len: L, a: [x, y], b: [x + dx * L, y + dy * L], f };
    }
  }
  return best;
}
const SIGHT = {};
for (const f of [0, 1, 2]) { const b = longestSightlines(f); for (const s in b) if (!SIGHT[s] || b[s].len > SIGHT[s].len) SIGHT[s] = b[s]; }
// longest in a fight space: every floor, the street excluded
const fightMax = Math.max(...Object.entries(SIGHT).filter(([s]) => +s >= 3).map(([, v]) => v.len));

// Auto mass: built-up ground (0.75 m cells) within 7.5 m of any ground-floor walkable area, merged into rectangles
function autoMass() {
  const C2 = 0.75, mx0 = -9, my0 = 15, mnx = Math.round(174 / C2), mny = Math.round(90 / C2);
  const walk = new Uint8Array(mnx * mny);
  for (const a of AREAS.filter(a => a.f === 0)) {
    for (let j = Math.round((a.y0 - my0) / C2); j < Math.round((a.y1 - my0) / C2); j++)
      for (let i = Math.round((a.x0 - mx0) / C2); i < Math.round((a.x1 - mx0) / C2); i++) walk[j * mnx + i] = 1;
  }
  const R = 10, m = new Uint8Array(mnx * mny);
  for (let j = 0; j < mny; j++) for (let i = 0; i < mnx; i++) {
    if (walk[j * mnx + i]) continue;
    let near = false;
    for (let dj = -R; dj <= R && !near; dj++) for (let di = -R; di <= R; di++) {
      const ii = i + di, jj = j + dj; if (ii >= 0 && jj >= 0 && ii < mnx && jj < mny && walk[jj * mnx + ii]) { near = true; break; }
    }
    if (near) m[j * mnx + i] = 1;
  }
  const rects = [], open = {};
  for (let j = 0; j <= mny; j++) {
    const runs = [];
    if (j < mny) for (let i = 0; i < mnx;) { if (!m[j * mnx + i]) { i++; continue; } let e = i; while (e < mnx && m[j * mnx + e]) e++; runs.push([i, e]); i = e; }
    const next = {};
    for (const [i, e] of runs) { const key = i + ":" + e; if (open[key]) { next[key] = open[key]; delete open[key]; } else next[key] = { i, e, j0: j }; }
    for (const key in open) { const r = open[key]; rects.push([mx0 + r.i * C2, my0 + r.j0 * C2, mx0 + r.e * C2, my0 + j * C2]); }
    Object.keys(open).forEach(k => delete open[k]); Object.assign(open, next);
  }
  return rects;
}
const MASS = autoMass();

// ---------------------------------------------------------------------------------------------------------------
// Drawing
const r2 = v => Math.round(v * 100) / 100;
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
function wallSegments(a, f) {
  const segs = [];
  const edges = [[a.x0, a.y0, a.x1, a.y0], [a.x0, a.y1, a.x1, a.y1], [a.x0, a.y0, a.x0, a.y1], [a.x1, a.y0, a.x1, a.y1]];
  for (const [x0, y0, x1, y1] of edges) {
    const horiz = y0 === y1; let cuts = [];
    for (const o of OPENINGS.filter(o => o.f === f)) {
      if (horiz && o.a[1] === o.b[1] && Math.abs(o.a[1] - y0) < 0.01) cuts.push([o.a[0], o.b[0]]);
      if (!horiz && o.a[0] === o.b[0] && Math.abs(o.a[0] - x0) < 0.01) cuts.push([o.a[1], o.b[1]]);
    }
    let s0 = horiz ? x0 : y0; const s1 = horiz ? x1 : y1;
    cuts = cuts.map(([p, q]) => [Math.max(p, s0), Math.min(q, s1)]).filter(([p, q]) => q > p).sort((u, v) => u[0] - v[0]);
    for (const [p, q] of cuts) { if (p > s0) segs.push(horiz ? [s0, y0, p, y0] : [x0, s0, x0, p]); s0 = Math.max(s0, q); }
    if (s1 > s0) segs.push(horiz ? [s0, y0, s1, y0] : [x0, s0, x0, s1]);
  }
  return segs;
}
function stairSvg(s, t) {
  const [x0, y0, x1, y1] = s.r; let out = `<rect x="${x0}" y="${y0}" width="${r2(x1 - x0)}" height="${r2(y1 - y0)}" class="stair"/>`;
  const vert = s.up === "N" || s.up === "S", len = vert ? y1 - y0 : x1 - x0, n = Math.max(3, Math.round(len / 0.5));
  for (let k = 1; k < n; k++) { const p = (vert ? y0 : x0) + (len * k) / n; out += vert ? `<line x1="${x0}" y1="${r2(p)}" x2="${x1}" y2="${r2(p)}" class="tread"/>` : `<line x1="${r2(p)}" y1="${y0}" x2="${r2(p)}" y2="${y1}" class="tread"/>`; }
  const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, h = 0.55 * t;
  const tri = { N: `M${cx} ${y0 + 0.3} l${-h} ${h * 1.6} h${2 * h}z`, S: `M${cx} ${y1 - 0.3} l${-h} ${-h * 1.6} h${2 * h}z`, E: `M${x1 - 0.3} ${cy} l${-h * 1.6} ${-h} v${2 * h}z`, W: `M${x0 + 0.3} ${cy} l${h * 1.6} ${-h} v${2 * h}z` }[s.up];
  return out + `<path d="${tri}" class="arrowhead"/>`;
}
function plan(f, vb, opt = {}) {
  const [vx, vy, vw, vh] = vb, t = opt.t || 1, fs = n => r2(n * t);
  const inView = (x, y) => x >= vx - 1 && x <= vx + vw + 1 && y >= vy - 1 && y <= vy + vh + 1;
  let s = `<svg class="${opt.cls || "plan"}" viewBox="${vx} ${vy} ${vw} ${vh}" role="img" aria-label="${esc(opt.aria || "plan")}" style="--t:${t}">`;
  s += `<defs><pattern id="g1${opt.id}" width="1.5" height="1.5" patternUnits="userSpaceOnUse"><path d="M1.5 0V1.5H0" class="g1" fill="none"/></pattern>`
    + `<pattern id="g5${opt.id}" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="url(#g1${opt.id})"/><path d="M6 0V6H0" class="g5" fill="none"/></pattern>`
    + `<pattern id="hatch${opt.id}" width=".7" height=".7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2=".7" class="hl"/></pattern>`
    + `<pattern id="roof${opt.id}" width="1.2" height="1.2" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><line x1="0" y1="0" x2="0" y2="1.2" class="rl"/></pattern></defs>`;
  s += `<rect x="${vx}" y="${vy}" width="${vw}" height="${vh}" fill="url(#g5${opt.id})"/>`;
  // ground mass on the ground floor; on upper floors, the footprint of the building below
  if (f === 0) for (const [x0, y0, x1, y1] of MASS) s += `<rect x="${r2(x0)}" y="${r2(y0)}" width="${r2(x1 - x0)}" height="${r2(y1 - y0)}" class="blk"/>`;
  else for (const a of AREAS.filter(a => a.f === 0 && a.kind === "room")) s += `<rect x="${a.x0}" y="${a.y0}" width="${r2(a.x1 - a.x0)}" height="${r2(a.y1 - a.y0)}" class="below"/>`;
  const areas = AREAS.filter(a => a.f === f);
  for (const a of areas) {
    const cls = { open: "lane", cov: "lane", room: "room-f", void: "void", off: "offl" }[a.kind];
    s += `<rect x="${a.x0}" y="${a.y0}" width="${r2(a.x1 - a.x0)}" height="${r2(a.y1 - a.y0)}" class="${cls}"${a.kind === "void" ? ` fill="url(#hatch${opt.id})"` : ""}/>`;
  }
  for (const rf of ROOFS.filter(r => r.f === f)) { const [x0, y0, x1, y1] = rf.r; s += `<rect x="${x0}" y="${y0}" width="${r2(x1 - x0)}" height="${r2(y1 - y0)}" fill="url(#roof${opt.id})" class="roofo"/>`; }
  for (const a of areas.filter(a => a.kind === "void")) s += `<rect x="${a.x0}" y="${a.y0}" width="${r2(a.x1 - a.x0)}" height="${r2(a.y1 - a.y0)}" class="rail"/>`;
  for (const l of LANDINGS.filter(l => l.f === f)) {
    const [x0, y0, x1, y1] = l.r;
    s += `<rect x="${x0}" y="${y0}" width="${r2(x1 - x0)}" height="${r2(y1 - y0)}" class="stair"/>`;
    if (l.rail) s += `<path d="M${x0} ${y1}V${y0}M${x1} ${y0}V${y1}" class="rail"/>`;
    s += `<text x="${r2((x0 + x1) / 2)}" y="${r2(y0 + 0.62 * t)}" class="t-sub" text-anchor="middle" style="font-size:${fs(0.5)}px">${esc(l.label)}</text>`;   // top edge: the border pill sits on the bottom one
  }
  for (const st of STAIRS.filter(st => st.f === f)) s += stairSvg(st, t);
  for (const c of COVER.filter(c => c.f === f)) { const [x0, y0, x1, y1] = c.r; s += `<rect x="${x0}" y="${y0}" width="${r2(x1 - x0)}" height="${r2(y1 - y0)}" class="${c.tall ? "tall" : "cover"}"/>`; }
  for (const a of areas.filter(a => a.kind === "room")) for (const [x0, y0, x1, y1] of wallSegments(a, f)) s += `<line x1="${x0}" y1="${y0}" x2="${x1}" y2="${y1}" class="wallx"/>`;
  for (const o of OPENINGS.filter(o => o.f === f)) {
    if (o.k === "knock") s += `<line x1="${o.a[0]}" y1="${o.a[1]}" x2="${o.b[0]}" y2="${o.b[1]}" class="knockl"/>`;
  }
  for (const b of BARRIERS.filter(b => b.f === f)) s += `<line x1="${b.a[0]}" y1="${b.a[1]}" x2="${b.b[0]}" y2="${b.b[1]}" class="${b.k === "wall" ? "wallx" : "gate"}"/>`;
  // connectors (section borders)
  if (opt.connectors) for (const c of CONNECTORS) {
    const mx = (c.a[0] + c.b[0]) / 2, my = (c.a[1] + c.b[1]) / 2;
    s += `<line x1="${c.a[0]}" y1="${c.a[1]}" x2="${c.b[0]}" y2="${c.b[1]}" class="conn"/>`;
    s += `<g transform="translate(${mx} ${my})"><rect x="${fs(-1.55)}" y="${fs(-0.62)}" width="${fs(3.1)}" height="${fs(1.24)}" rx="${fs(0.62)}" class="connb"/><text y="${fs(0.27)}" class="t-conn" text-anchor="middle" style="font-size:${fs(0.78)}px">${c.from}↔${c.to}</text></g>`;
  }
  // sightlines
  const drawn = [], near = (p, q) => Math.hypot(p[0] - q[0], p[1] - q[1]) < 3;
  if (opt.sight) for (const [sid, v] of Object.entries(SIGHT)) {
    if (v.f !== f || !opt.sight.includes(+sid)) continue;
    // the same view seen from both ends (across a section border) is drawn once
    if (drawn.some(d => (near(d.a, v.a) && near(d.b, v.b)) || (near(d.a, v.b) && near(d.b, v.a)))) continue;
    drawn.push(v);
    s += `<line x1="${r2(v.a[0])}" y1="${r2(v.a[1])}" x2="${r2(v.b[0])}" y2="${r2(v.b[1])}" class="sight"/>`;
    const mx = (v.a[0] + v.b[0]) / 2, my = (v.a[1] + v.b[1]) / 2;
    s += `<text x="${r2(mx)}" y="${r2(my - 0.5 * t)}" class="t-a" text-anchor="middle" style="font-size:${fs(0.8)}px">${v.len.toFixed(1)} m</text>`;
  }
  // labels
  for (const a of areas) if (a.label && a.kind !== "void") {
    const cx = (a.x0 + a.x1) / 2, cy = (a.y0 + a.y1) / 2, w = a.x1 - a.x0;
    const size = Math.min(0.78 * t, w / Math.max(4, a.label.length) * 1.9);
    s += `<text x="${r2(cx)}" y="${r2(a.kind === "room" ? a.y0 + 1.15 * t : cy)}" class="t-sub" text-anchor="middle" style="font-size:${r2(size)}px">${esc(a.label)}</text>`;
  }
  for (const a of areas.filter(a => a.kind === "void" && a.label)) s += `<text x="${r2((a.x0 + a.x1) / 2)}" y="${r2((a.y0 + a.y1) / 2)}" class="t-sub" text-anchor="middle" style="font-size:${fs(0.62)}px">${esc(a.label)}</text>`;
  // markers
  for (const c of (f === 0 ? CIVILIANS : [])) if (inView(...c)) s += `<circle cx="${c[0]}" cy="${c[1]}" r="${fs(0.42)}" class="civ"/>`;
  for (const p of PICKUPS.filter(p => p.f === f)) s += `<rect x="${r2(p.x - 0.42 * t)}" y="${r2(p.y - 0.42 * t)}" width="${fs(0.84)}" height="${fs(0.84)}" class="pick" transform="rotate(45 ${p.x} ${p.y})"/><text x="${p.x}" y="${r2(p.y + 1.45 * t)}" class="t-p" text-anchor="middle" style="font-size:${fs(0.66)}px">${esc(p.label)}</text>`;
  for (const F of FIGHTS) {
    let any = false;
    for (const e of F.foes) { const ef = e[3] !== undefined ? e[3] : F.f; if (ef !== f) continue; any = true;
      s += e[2] === "c" ? `<circle cx="${e[0]}" cy="${e[1]}" r="${fs(0.5)}" class="foe-c"/><circle cx="${e[0]}" cy="${e[1]}" r="${fs(0.2)}" class="spawn-d"/>` : `<circle cx="${e[0]}" cy="${e[1]}" r="${fs(0.5)}" class="spawn-d"/>`; }
    if (F.f === f) for (const w of F.waveDoors || []) { s += `<circle cx="${w[0]}" cy="${w[1]}" r="${fs(0.8)}" class="spawn"/>`; any = true; }
    if (any && (F.f === f)) s += `<text x="${F.lab[0]}" y="${F.lab[1]}" class="t-w" text-anchor="middle" style="font-size:${fs(0.82)}px">${F.id} · ${F.start}${F.wave ? "+" + F.wave : ""}</text>`;
    else if (any) s += `<text x="${r2(F.foes.find(e => (e[3] ?? F.f) === f)[0] + 0.75 * t)}" y="${r2(F.foes.find(e => (e[3] ?? F.f) === f)[1] + 1.25 * t)}" class="t-w" style="font-size:${fs(0.62)}px">${F.id}</text>`;
  }
  for (const i of INSPECTS.filter(i => i.f === f)) s += `<g transform="translate(${i.x} ${i.y})"><circle r="${fs(0.62)}" class="insp${i.req ? " req" : ""}"/><line x1="${fs(0.44)}" y1="${fs(0.44)}" x2="${fs(0.95)}" y2="${fs(0.95)}" class="insp-h"/><text x="${fs(1.15)}" y="${fs(-0.5)}" class="t-i" style="font-size:${fs(0.72)}px">${i.id}</text></g>`;
  for (const c of CHECKPOINTS.filter(c => c.f === f)) s += `<g transform="translate(${c.x} ${c.y})"><path d="M0 ${fs(0.7)}V${fs(-0.85)}l${fs(1)} ${fs(0.35)}l${fs(-1)} ${fs(0.35)}" class="cp"/><text x="${fs(-0.3)}" y="${fs(1.55)}" class="t-cp" text-anchor="middle" style="font-size:${fs(0.6)}px">${c.id}</text></g>`;
  if (f === 0 && inView(...START)) s += `<circle cx="${START[0]}" cy="${START[1]}" r="${fs(0.6)}" class="start"/><text x="${START[0] + 1.2 * t}" y="${START[1] + 2 * t}" class="t-a" style="font-size:${fs(0.74)}px">START</text>`;
  if (f === 2) s += `<path d="${FLEE.map((p, k) => (k ? "L" : "M") + p[0] + " " + p[1]).join("")}" class="flee"/><text x="137" y="27.2" class="t-w" style="font-size:${fs(0.62)}px">survivors flee</text>`;
  if (opt.sections) for (const S of SECTIONS) s += `<text x="${S.label[0]}" y="${S.label[1]}" class="t-sec">${S.id} ${esc(S.name.toUpperCase())}</text>`;
  if (opt.extra) s += opt.extra;
  return s + "</svg>";
}

// ---------------------------------------------------------------------------------------------------------------
// Page
const totalFoes = FIGHTS.reduce((n, F) => n + F.start + F.wave, 0);
const mins = SECTIONS.reduce((m, S) => [m[0] + S.mins[0], m[1] + S.mins[1]], [0, 0]);
const sightRow = s => SIGHT[s] ? `${SIGHT[s].len.toFixed(1)} m${SIGHT[s].f ? ` (${["G", "+4", "+8"][SIGHT[s].f]})` : ""}` : "—";
const streetLen = SIGHT[1] ? SIGHT[1].len : 0;

// The route, written into the plan's empty south-east corner
const routeBox = (() => {
  let y = 66, s = `<text x="112" y="${y}" class="t-sec" style="font-size:1.6px">THE ROUTE</text>`;
  for (const S of SECTIONS) {
    y += 2.6;
    const fights = FIGHTS.filter(F => F.sec === S.id), foes = fights.reduce((n, F) => n + F.start + F.wave, 0);
    const out = CONNECTORS.find(c => c.from === S.id);
    s += `<text x="112" y="${y}" class="t-dim" style="font-size:1.05px"><tspan class="t-r">${S.id}</tspan>  ${esc(S.name)} · ${S.mins[0]}–${S.mins[1]} min · ${esc(S.kind)}${fights.length ? ` · ${fights.map(F => F.id).join(" ")} (${foes})` : ""}</text>`;
    s += `<text x="114.2" y="${y + 1.25}" class="t-sub" style="font-size:.85px">${out ? "on: " + esc(out.note) : "ends on the documents (I8)"}</text>`;
  }
  y += 3.4;
  s += `<text x="112" y="${y}" class="t-dim" style="font-size:1.05px">${SECTIONS.reduce((m, S) => m + S.mins[0], 0)}–${SECTIONS.reduce((m, S) => m + S.mins[1], 0)} min · ${FIGHTS.length} fights · ${FIGHTS.reduce((n, F) => n + F.start + F.wave, 0)} gunmen · night</text>`;
  return s;
})();
const overview = plan(0, [-9, 15, 174, 91], { id: "o", connectors: true, sections: true, extra: routeBox, sight: [1, 2, 3, 4, 5, 6, 7], aria: "Top-down ground plan of the whole level, seven sections from the main street to the trap house" });
const rowUp = plan(1, [58, 56.5, 28, 16], { id: "r", t: 0.8, cls: "plan-s", sight: [4], aria: "Row houses at +4 m" });
const mezz = plan(1, [92.5, 34, 22, 7.5], { id: "m", t: 0.7, cls: "plan-s", sight: [5], aria: "Bodega mezzanine at +3 m" });
const thG = plan(0, [129.5, 27.5, 26.5, 25], { id: "tg", t: 0.62, cls: "plan-s", aria: "Trap house ground floor" });
const th1 = plan(1, [137.5, 27.5, 18.5, 22], { id: "t1", t: 0.55, cls: "plan-s", sight: [7], aria: "Trap house at +4 m" });
const th2 = plan(2, [135, 21, 21, 28.5], { id: "t2", t: 0.55, cls: "plan-s", aria: "Trap house at +8 m" });
// override the S7 sightline: draw its per-floor maxima on the trap-house sheets
function floorMax(f, s) { const b = longestSightlines(f)[s]; return b; }
const s7 = [0, 1, 2].map(f => floorMax(f, 7));
function sightOn(svg, v) {
  if (!v) return svg;
  const add = `<line x1="${r2(v.a[0])}" y1="${r2(v.a[1])}" x2="${r2(v.b[0])}" y2="${r2(v.b[1])}" class="sight"/><text x="${r2((v.a[0] + v.b[0]) / 2)}" y="${r2((v.a[1] + v.b[1]) / 2 - 0.4)}" class="t-a" text-anchor="middle" style="font-size:.6px">${v.len.toFixed(1)} m</text>`;
  return svg.replace(/<\/svg>$/, add + "</svg>");
}
const thGs = sightOn(thG, s7[0]), th1s = th1.includes('class="sight"') ? th1 : sightOn(th1, s7[1]), th2s = sightOn(th2, s7[2]);

// Vertical route (schematic, not to scale in x)
const stack = (() => {
  const box = (x, y, w, label, sub, cls = "") => `<rect x="${x}" y="${y}" width="${w}" height="6.4" rx=".6" class="sbox ${cls}"/><text x="${x + w / 2}" y="${y + 2.9}" class="t-sb" text-anchor="middle">${label}</text><text x="${x + w / 2}" y="${y + 5.1}" class="t-sbs" text-anchor="middle">${sub}</text>`;
  const arr = (x1, y1, x2, y2, cls = "route") => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="${cls}" marker-end="url(#ah)"/>`;
  let g = `<svg viewBox="0 0 100 44" class="stack" role="img" aria-label="Schematic of the trap house route, floor by floor"><defs><marker id="ah" viewBox="0 0 4 4" refX="3" refY="2" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0L4 2L0 4z" class="ahd"/></marker></defs>`;
  g += `<text x="0" y="37" class="t-fl">G</text><text x="0" y="23.5" class="t-fl">+4</text><text x="0" y="10" class="t-fl">+8</text>`;
  g += `<line x1="6" y1="29.4" x2="100" y2="29.4" class="band"/><line x1="6" y1="15.9" x2="100" y2="15.9" class="band"/>`;
  g += box(6, 32, 16, "courtyard", "F8 · CP7") + arr(22.4, 35.2, 26.6, 35.2) + box(27, 32, 16, "hall", "F9 · open to +8") + arr(43.4, 35.2, 47.6, 35.2) + box(48, 32, 17, "stair hall", "F10");
  g += arr(56.5, 31.6, 13.5, 25.6) ;
  g += box(6, 18.5, 14, "landing", "CP8 · F10") + arr(20.4, 21.7, 23.6, 21.7) + box(24, 18.5, 14, "sleeping", "F11") + arr(38.4, 21.7, 41.6, 21.7) + box(42, 18.5, 14, "gallery", "over the hall") + arr(56.4, 21.7, 59.6, 21.7) + box(60, 18.5, 13, "bunks", "F11") + arr(73.4, 21.7, 76.6, 21.7) + box(77, 18.5, 14, "kitchen", "F11 · wooden stair");
  g += arr(84, 18.1, 50, 12.1);
  g += box(36, 5, 20, "staging room", "F12 · last fight") + arr(56.4, 8.2, 61.6, 8.2) + box(62, 5, 17, "forging room", "I8 · END", "end") + box(81, 5, 14, "photo", "I7 (optional)", "opt");
  g += `<line x1="56" y1="9.6" x2="80.6" y2="9.6" class="route" style="stroke-width:.25;stroke-dasharray:.6 .4"/>`;
  g += arr(35.6, 8.2, 22, 8.2, "flee") + box(6, 5, 15.6, "terrace → plank", "survivors flee", "fl");
  return g + "</svg>";
})();

const sectionRows = SECTIONS.map(S => {
  const cps = CHECKPOINTS.filter(c => c.sec === S.id).map(c => c.id).join(", ") || "—";
  const fights = FIGHTS.filter(F => F.sec === S.id).map(F => F.id).join(", ") || "—";
  const out = CONNECTORS.find(c => c.from === S.id);
  return `<tr><td>${S.id}</td><td><b>${esc(S.name)}</b><br><span class="small">${esc(S.what)}</span></td><td>${esc(S.ground)}</td><td>${S.mins[0]}–${S.mins[1]}</td><td>${fights}</td><td>${cps}</td><td>${out ? esc(out.note) : "the documents (I8)"}</td><td>${sightRow(S.id)}</td></tr>`;
}).join("");
const fightRows = FIGHTS.map(F => `<tr><td>${F.id}</td><td>${F.sec} · ${esc(F.room)}</td><td>${F.start}${F.wave ? ` + ${F.wave} (${F.max} at once)` : ""}${F.foes.some(e => e[2] === "c") ? `<br><span class="small">${F.foes.filter(e => e[2] === "c").length} crouched</span>` : ""}</td><td>${esc(F.trigger)}</td><td class="small">${esc(F.note)}</td></tr>`).join("");
const inspRows = INSPECTS.map(i => `<tr><td>${i.id}</td><td>${i.sec}</td><td><b>${esc(i.name)}</b>${i.req ? ' <span class="tag">needed</span>' : ""}</td><td class="small">${i.what ? esc(i.what) + (i.src === "scenario" ? ' <span class="src">scenario</span>' : "") : ""}${i.sug ? `${i.what ? "<br>" : ""}<i>${esc(i.sug)}</i> <span class="src sug">suggestion</span>` : ""}</td><td class="small">${esc(i.does) || "—"}</td></tr>`).join("");

const json = {
  name: "Linear slum level (working: the missing patrolman)", drafted: "2026-11-07", revised: "2026-11-08: doors and steps for the drops, borders both ways",
  units: "m, x east, y south, from the NW corner",
  floors: { "0": "ground", "1": "+4 (bodega mezzanine +3)", "2": "+8" }, storey_m: 4,
  sections: SECTIONS.map(({ label, ...S }) => S), connectors: CONNECTORS, streaming: STREAM_NOTE,
  areas: AREAS, openings: OPENINGS, barriers: BARRIERS, stairs: STAIRS, landings: LANDINGS, cover: COVER, roofs: ROOFS,
  arms: ARMS, mass_auto: MASS.map(r => r.map(r2)), fights: FIGHTS, inspects: INSPECTS, checkpoints: CHECKPOINTS, pickups: PICKUPS,
  civilians: CIVILIANS, start: START, flee: FLEE,
  sightlines_measured: Object.fromEntries(Object.entries(SIGHT).map(([s, v]) => [s, { len: r2(v.len), floor: v.f, a: v.a.map(r2), b: v.b.map(r2) }])),
};
fs.writeFileSync(OUT_JSON, JSON.stringify(json, null, 1));

const legend = `<div class="legend">
  <span><svg viewBox="0 0 2 1.4"><rect width="2" height="1.4" class="blk"/></svg>Houses (built-up, not entered)</span>
  <span><svg viewBox="0 0 2 1.4"><rect width="2" height="1.4" class="lane"/></svg>Street, alley, yard</span>
  <span><svg viewBox="0 0 2 1.4"><rect width="2" height="1.4" class="room-f"/><path d="M0 .1H2" class="wallx"/></svg>Room (walls drawn)</span>
  <span><svg viewBox="0 0 2 1.4"><path d="M0 .7H2" class="knockl"/></svg>Knocked-through wall</span>
  <span><svg viewBox="0 0 2 1.4"><path d="M0 .7H2" class="gate"/></svg>Shut gate</span>
  <span><svg viewBox="0 0 2 1.4"><rect width="2" height="1.4" class="cover"/></svg>Low cover (dive past)</span>
  <span><svg viewBox="0 0 2 1.4"><rect width="2" height="1.4" class="tall"/></svg>Full height (blocks sight)</span>
  <span><svg viewBox="-1 -1 2 2"><circle r=".5" class="spawn-d"/></svg>Gunman</span>
  <span><svg viewBox="-1 -1 2 2"><circle r=".5" class="foe-c"/><circle r=".2" class="spawn-d"/></svg>Gunman, crouched</span>
  <span><svg viewBox="-1 -1 2 2"><circle r=".8" class="spawn"/></svg>Wave door</span>
  <span><svg viewBox="-1 -1 2 2"><circle r=".42" class="civ"/></svg>Civilian (no fights)</span>
  <span><svg viewBox="-1.2 -1.2 2.6 2.6"><circle r=".62" class="insp req"/><line x1=".44" y1=".44" x2=".95" y2=".95" class="insp-h"/></svg>Inspect (filled = needed)</span>
  <span><svg viewBox="-1 -1 2.4 2"><path d="M0 .7V-.85l1 .35l-1 .35" class="cp"/></svg>Checkpoint</span>
  <span><svg viewBox="-1 -1 2 2"><rect x="-.42" y="-.42" width=".84" height=".84" class="pick" transform="rotate(45)"/></svg>Pickup</span>
  <span><svg viewBox="0 0 3.2 1.4"><path d="M0 .7H3.2" class="conn"/></svg>Section border (a door, both ways)</span>
  <span><svg viewBox="0 0 2 1.4"><rect width="2" height="1.4" class="stair"/><path d="M.67 0V1.4M1.33 0V1.4" class="tread"/></svg>Stair or steps (arrow points up)</span>
  <span><svg viewBox="0 0 3.2 1.4"><path d="M0 .7H3.2" class="sight"/></svg>Longest sightline, measured</span>
  <span><svg viewBox="0 0 2 1.4"><rect width="2" height="1.4" class="lane"/><rect width="2" height="1.4" fill="url(#roofL)" class="roofo"/></svg>Roofed over</span>
</div>`;

const html = `<title>Slum Linear Layout</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Text:wght@500;700;800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap">
<!-- Generated by Tools/LevelGen/layout_linear_slums.mjs. Edit the script, not this file. -->
<style>
:root {
  --bg: #e8ebe6; --sheet: #f4f5f1; --floor: #fbfbf8; --ink: #1d2729; --muted: #5e6b6b; --line: #c3cbc6;
  --grid: #dfe4df; --grid2: #cdd5cf; --wall: #263235; --mass: #c9d0cc; --cover: #aab4b0; --tall: #7d8985;
  --accent: #c97a12; --foe: #b3332b; --pick: #23786a; --trig: #6a52a8; --insp: #1f6fb2; --cp: #3a8a2e; --lane: #f1f2ec;
  --display: "Big Shoulders Text", "Arial Narrow", sans-serif; --body: "IBM Plex Sans", system-ui, sans-serif; --mono: "IBM Plex Mono", ui-monospace, Consolas, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #111719; --sheet: #172023; --floor: #1d282b; --ink: #dfe6e3; --muted: #8e9c9a; --line: #2f3b3d; --grid: #1a2427; --grid2: #243134;
  --wall: #c8d2cf; --mass: #2c383b; --cover: #4a5856; --tall: #6d7a77; --accent: #f0a53a; --foe: #e2594d; --pick: #4fb7a2; --trig: #a28be0;
  --insp: #5aa7e6; --cp: #6cc35e; --lane: #1a2427; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #111719; --sheet: #172023; --floor: #1d282b; --ink: #dfe6e3; --muted: #8e9c9a; --line: #2f3b3d; --grid: #1a2427; --grid2: #243134;
  --wall: #c8d2cf; --mass: #2c383b; --cover: #4a5856; --tall: #6d7a77; --accent: #f0a53a; --foe: #e2594d; --pick: #4fb7a2; --trig: #a28be0;
  --insp: #5aa7e6; --cp: #6cc35e; --lane: #1a2427; color-scheme: dark }
body { background: var(--bg); color: var(--ink); font-family: var(--body); font-size: 15px; line-height: 1.5; margin: 0; }
.wrap { max-width: 1240px; margin: 0 auto; padding-block: 28px 56px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); display: grid; gap: 28px; }
header { display: grid; gap: 6px; }
.eyebrow { font: 600 12px/1.3 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
h1 { font: 800 clamp(34px, 6vw, 56px)/1 var(--display); letter-spacing: .01em; text-transform: uppercase; margin: 0; text-wrap: balance; }
h2 { font: 700 22px/1.1 var(--display); text-transform: uppercase; letter-spacing: .03em; margin: 0; }
h3 { font: 700 16px/1.1 var(--display); text-transform: uppercase; letter-spacing: .03em; margin: 0; }
.lede { max-width: 78ch; margin: 4px 0 0; color: var(--muted); }
.lede b { color: var(--ink); font-weight: 600; }
.stats { display: flex; flex-wrap: wrap; gap: 10px 28px; margin-top: 8px; }
.stats div { display: grid; }
.stats b { font: 700 28px/1 var(--display); }
.stats span { font: 500 11px var(--mono); text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
.sheet { background: var(--sheet); border: 1px solid var(--line); min-width: 0; }
.sheet-head { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px 20px; align-items: baseline; padding: 12px 16px; border-bottom: 1px solid var(--line); }
.sheet-head .meta { font: 500 12px var(--mono); color: var(--muted); }
.scroll { overflow-x: auto; }
.plan { display: block; width: 100%; min-width: 1500px; height: auto; }
.plan-s { display: block; width: 100%; height: auto; }
.pad { padding: 12px 16px 16px; display: grid; gap: 10px; }
.note { font-size: 13px; color: var(--muted); margin: 0; }
.grid3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.grid3 figure, .grid2 figure, .gridE figure { margin: 0; display: grid; gap: 4px; }
.gridE { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px 20px; align-items: start; }
.sbox { fill: var(--floor); stroke: var(--wall); stroke-width: .25; } .sbox.end { fill: var(--insp); } .sbox.opt { stroke-dasharray: .6 .4; } .sbox.fl { stroke: var(--foe); stroke-dasharray: .6 .4; }
.t-sb { font: 600 2px var(--mono); fill: var(--ink); } .t-sbs { font: 400 1.5px var(--body); fill: var(--muted); } .sbox.end + .t-sb, .sbox.end + .t-sb + .t-sbs { fill: var(--sheet); }
.t-fl { font: 700 2.6px var(--display); fill: var(--muted); } .band { stroke: var(--line); stroke-width: .2; } .ahd { fill: var(--trig); } .route { stroke-width: .5; }
figcaption { font: 600 12px var(--mono); color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }
.grid2 { display: grid; grid-template-columns: 1.6fr 1fr; gap: 12px; align-items: start; }
.legend { display: flex; flex-wrap: wrap; gap: 6px 16px; padding: 10px 16px; border-bottom: 1px solid var(--line); font-size: 12.5px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.legend svg { width: 22px; height: 16px; overflow: visible; }
table { border-collapse: collapse; width: 100%; font-size: 13.5px; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { font: 600 11px var(--mono); text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
td:first-child { font: 500 12.5px var(--mono); white-space: nowrap; }
.small { font-size: 12.5px; color: var(--muted); }
.tag { font: 600 10.5px var(--mono); text-transform: uppercase; color: var(--sheet); background: var(--insp); padding: 1px 5px; border-radius: 3px; }
.src { font: 600 10px var(--mono); text-transform: uppercase; color: var(--insp); }
.src.sug { color: var(--accent); }
.lists { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 28px; }
.lists section { display: grid; gap: 8px; align-content: start; min-width: 0; }
.lists ul, .lists ol { margin: 0; padding-left: 18px; display: grid; gap: 6px; font-size: 14px; }
.lists .owned { border-left: 3px solid var(--trig); padding-left: 14px; }
code { font: 500 .9em var(--mono); }
.tw { overflow-x: auto; }
/* drawing (user units are metres) */
.g1 { stroke: var(--grid); stroke-width: .05; } .g5 { stroke: var(--grid2); stroke-width: .09; }
.blk { fill: var(--mass); }
.below { fill: var(--mass); opacity: .45; }
.lane { fill: var(--lane); } .room-f { fill: var(--floor); }
.void { stroke: none; } .hl { stroke: var(--cover); stroke-width: .12; }
.rail { fill: none; stroke: var(--muted); stroke-width: .12; stroke-dasharray: .3 .2; }
.offl { fill: var(--lane); opacity: .55; }
.roofo { stroke: var(--muted); stroke-width: .08; stroke-dasharray: .4 .3; } .rl { stroke: var(--grid2); stroke-width: .14; }
.wallx { stroke: var(--wall); stroke-width: .3; stroke-linecap: square; }
.knockl { stroke: var(--accent); stroke-width: .22; stroke-dasharray: .25 .2; }
.gate { stroke: var(--wall); stroke-width: .7; }
.stair { fill: var(--floor); stroke: var(--wall); stroke-width: .1; } .tread { stroke: var(--muted); stroke-width: .07; }
.arrowhead { fill: var(--accent); }
.cover { fill: var(--cover); } .tall { fill: var(--tall); }
.spawn { fill: none; stroke: var(--foe); stroke-width: .22; stroke-dasharray: .35 .25; } .spawn-d { fill: var(--foe); }
.foe-c { fill: var(--sheet); stroke: var(--foe); stroke-width: .2; }
.civ { fill: none; stroke: var(--muted); stroke-width: .16; }
.pick { fill: var(--pick); } .start { fill: var(--accent); }
.insp { fill: var(--sheet); stroke: var(--insp); stroke-width: .2; } .insp.req { fill: var(--insp); } .insp-h { stroke: var(--insp); stroke-width: .25; stroke-linecap: round; }
.cp { fill: var(--cp); stroke: var(--cp); stroke-width: .14; stroke-linejoin: round; }
.conn { stroke: var(--trig); stroke-width: .5; stroke-dasharray: .5 .3; } .connb { fill: var(--trig); } .t-conn { font-family: var(--mono); font-weight: 600; fill: var(--sheet); }
.sight { fill: none; stroke: var(--accent); stroke-width: .24; stroke-dasharray: .9 .5; stroke-linecap: round; }
.flee { fill: none; stroke: var(--foe); stroke-width: .18; stroke-dasharray: .5 .3; }
.route { fill: none; stroke: var(--trig); stroke-width: .6; stroke-linecap: round; }
.vh { fill: none; stroke: var(--muted); stroke-width: .15; stroke-dasharray: .5 .4; }
.slab { fill: var(--wall); } .ground { stroke: var(--wall); stroke-width: .35; }
.stack { width: 100%; height: auto; display: block; }
.t-sub { font-family: var(--body); fill: var(--muted); }
.t-w { font-family: var(--mono); font-weight: 600; fill: var(--foe); }
.t-p { font-family: var(--body); font-weight: 500; fill: var(--pick); }
.t-a { font-family: var(--mono); font-weight: 600; fill: var(--accent); }
.t-r { font-family: var(--mono); font-weight: 600; fill: var(--trig); }
.t-i { font-family: var(--mono); font-weight: 600; fill: var(--insp); }
.t-cp { font-family: var(--mono); font-weight: 600; fill: var(--cp); }
.t-dim { font-family: var(--mono); font-weight: 500; fill: var(--muted); }
.t-sec { font: 800 1.9px var(--display); fill: var(--trig); letter-spacing: .06px; opacity: .85; }
@media (max-width: 900px) { .lists, .grid3, .grid2, .gridE { grid-template-columns: 1fr; } }
</style>
<svg width="0" height="0" style="position:absolute"><defs><pattern id="roofL" width=".6" height=".6" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><line x1="0" y1="0" x2="0" y2=".6" class="rl"/></pattern></defs></svg>

<div class="wrap">
  <header>
    <div class="eyebrow">ProjectBopis · level layout · linear story level · slum compound · night · draft 2026-11-07 · revised 2026-11-08: doors, no drops</div>
    <h1>Slum Linear Layout</h1>
    <p class="lede">The missing patrolman, laid out from your scenario as <b>seven streamed sections</b>: a night street with people still out, an eskinita, the yard where the patrol car is hidden, then the compound. That's knocked-through row houses, a covered alley, a bodega, the holding house and a <b>three-level trap house</b> at the end. Every street and alley bends, or has something standing in it, within about 25 m, and no room or yard is deeper than 18 m. <b>The longest sightline in any fight space is ${fightMax.toFixed(1)} m</b>, and the walk-around street's is ${streetLen.toFixed(1)} m. Both were measured on this plan with a 1.2 m-wide line. Fights follow the room-encounter rules: 2–5 waiting, waves topping up to 4, never more than 6 in one fight. Arms are <b>${ARMS}</b>. Story beats are <b>inspects</b>: the car one starts the first big fight, and the documents one ends the level. <b>There are no drops:</b> every section border is a swinging door (the eskinita's mouth is a bend), every way through goes both ways, and the height changes are steps.</p>
    <div class="stats">
      <div><b>${mins[0]}–${mins[1]} min</b><span>estimated, first play</span></div>
      <div><b>7</b><span>sections</span></div>
      <div><b>${FIGHTS.length}</b><span>fights</span></div>
      <div><b>${totalFoes}</b><span>gunmen</span></div>
      <div><b>${INSPECTS.length}</b><span>inspects, 2 needed</span></div>
      <div><b>${CHECKPOINTS.length}</b><span>checkpoints</span></div>
      <div><b>${fightMax.toFixed(1)} m</b><span>longest fight sightline</span></div>
    </div>
  </header>

  <div class="sheet">
    <div class="sheet-head"><h2>Plan · ground</h2><span class="meta">metres from the NW corner (x east, y south) · grid 1.5 m, heavy line every 6 m · north up · scrolls sideways</span></div>
    ${legend}
    <div class="scroll">${overview}</div>
    <div class="pad"><p class="note">Upper-floor gunmen (F4, F6's mezzanine, F9's gallery, F10–F12) are drawn on the floor sheets below. Houses along the route are drawn as one built-up mass, 7.5 m deep: the generator already splits blocks into houses 4.5–7.5 m wide. Only houses that are entered get interiors.</p></div>
  </div>

  <div class="sheet">
    <div class="sheet-head"><h2>Upper floors · row houses + bodega</h2><span class="meta">S4 at +4 m · S5's mezzanine at +3 m · grey = the floor below</span></div>
    <div class="pad grid2">
      <figure><figcaption>Row houses, +4 (F4)</figcaption>${rowUp}</figure>
      <figure><figcaption>Bodega mezzanine, +3 (one of F6)</figcaption>${mezz}
        <p class="note">You come up H2's stair facing south. Then it's a knock-through into H3, a door to its front room, a knock-through into H4, and its back room. A gunman holds the head of H4's back stair, which turns at a half landing (+2) and comes down facing the back door. The section's way out is that door (CP4 is just outside it). The stair fits inside H4's back room, so no building changes size.</p>
        <p class="note">The mezzanine runs the bodega's full 18 m along the north wall, with one gunman on it. Its stair starts by the door.</p></figure>
    </div>
  </div>

  <div class="sheet">
    <div class="sheet-head"><h2>Trap house · three levels</h2><span class="meta">15 × 18 m · storeys 4 m (3.8 m clear) · the wooden storey 3.6 m clear · grey = the floor below</span></div>
    <div class="pad">
      <div class="gridE">
        <figure><figcaption>Ground (F8 courtyard, F9 hall, F10)</figcaption>${thGs}</figure>
        <figure><figcaption>+4 (F10 landing, F11)</figcaption>${th1s}</figure>
        <figure><figcaption>+8 (F12, I7, I8, the escape)</figcaption>${th2s}</figure>
        <div class="pad" style="padding:0;align-content:start">
          <figure><figcaption>The route up (schematic, not to scale)</figcaption>${stack}</figure>
          <p class="note"><b>Built like a trap house:</b> a hollow-block ground storey, a plastered and painted +4, and a plywood-and-tin storey on top with its own wooden stair. Doors are knocked out to 2.25 m, there's a gallery round the double-height hall, and a terrace on the +4 roof.</p>
          <p class="note"><b>You see the hall twice.</b> You fight in it from below (F9), then walk the gallery above it on the way to the bunks (F11). The kitchen's wooden stair comes up into the staging room, where F12 is the last fight. The two small rooms off it hold the photo corner and the documents.</p>
          <p class="note"><b>“Kills or drives off”:</b> F12's survivors break for the terrace and cross a plank to the neighbour's roof, then the plank falls. That's optional new tech (a scripted flee). Without it, F12 is simply a fight to the last man.</p>
        </div>
      </div>
    </div>
  </div>

  <div class="sheet">
    <div class="sheet-head"><h2>Sections + streaming</h2><span class="meta">one small persistent map · each section an <code>_Art</code> and a <code>_Gameplay</code> sublevel</span></div>
    <div class="pad">
      <p class="note"><b>Loaded: the section you're in and the ones either side.</b> ${esc(STREAM_NOTE)} A death reloads only the current section's <code>_Gameplay</code> from its last checkpoint, never the map. Every border is a door or a bend, so no two sections that aren't neighbours can see each other.</p>
      <p class="note"><b>In place of the drops (2026-11-08), with no building resized:</b> 2→3 is a door in the yard wall at the eskinita's level, then a railed landing and steps down into the yard, with the car in view from the landing (the garage roof's back edge has to clear it: about 4.2 m at the wall). In section 4, H4's floor hole is now a stair with a half landing, inside the back room. 5→6 is the bodega's back door, then steps down 1.8 m through the passage, their foot coming through a doorway into the guard room. The ground heights stay as they were: the eskinita at +1.8, the holding house at −1.8.</p>
      <div class="tw"><table><tr><th>#</th><th>Section</th><th>Ground</th><th>Min</th><th>Fights</th><th>Checkpoints</th><th>Way out</th><th>Longest sightline</th></tr>${sectionRows}</table></div>
    </div>
  </div>

  <div class="sheet">
    <div class="sheet-head"><h2>Fights</h2><span class="meta">${totalFoes} gunmen · never more than 6 in one fight · ${ARMS}</span></div>
    <div class="pad tw"><table><tr><th>#</th><th>Where</th><th>Gunmen</th><th>Starts on</th><th>Notes</th></tr>${fightRows}</table>
    <p class="note"><b>Level 1 arms: ${ARMS}</b>, for Navarro and the gunmen alike. No ammo, weapons or grenades are placed: what you carry on comes from what they drop. First aid is the only pickup.</p></div>
  </div>

  <div class="sheet">
    <div class="sheet-head"><h2>Inspects · story beats</h2><span class="meta">the new interactable · <span class="src">scenario</span> = your text · <span class="src sug">suggestion</span> = mine, yours to replace</span></div>
    <div class="pad tw"><table><tr><th>#</th><th>Sec</th><th>Inspect</th><th>What's there</th><th>Does</th></tr>${inspRows}</table></div>
  </div>

  <div class="lists">
    <section>
      <h2>The generator has to learn</h2>
      <ol>
        <li><b>Levels as data.</b> The split I put off earlier: a shared building library, and level files like this JSON. The arena must still come out identical.</li>
        <li><b>Rooms inside houses</b>, storey by storey: partition walls (hollow block, plywood, tarp), plastered or painted inside faces, and a paint per room.</li>
        <li><b>Openings:</b> 1 m doors, 2.25 m doors, 3 m knock-throughs with broken block edges, a garage opening, open-fronted plywood rooms. The shell's windows also have to read from inside: check that the AsiaSlum wall pieces have inside faces.</li>
        <li><b>Floors:</b> slabs with stairwells, a double-height hall with a railed gallery, and a wooden top storey.</li>
        <li><b>Stairs indoors:</b> concrete flights at least 1.8 m wide, a stair that turns at a half landing (H4), and a steep wooden one.</li>
        <li><b>Ground heights:</b> the eskinita at +1.8 and the holding house at −1.8, with steps between (a stair's foot can sit off the floor's datum: <code>z0</code>), railed landings, and a doorway with no door (<code>open</code>).</li>
        <li><b>3 m eskinitas.</b> The arena is all 4.5 m alleys, so wires, laundry, pipes and AC units need spacing rules that fit.</li>
        <li><b>One sublevel per section</b> for the art, plus the gameplay actors written into each section's <code>_Gameplay</code>.</li>
        <li><b>Night:</b> the lamps, bulbs and tubes lit (<code>STREET_LIGHTS_ON</code>), and bulbs and tubes in the rooms. That's the Deck cost to measure first.</li>
      </ol>
    </section>
    <section>
      <h2>New gameplay it needs</h2>
      <ul>
        <li><b>Inspects</b> (yours, coming): a prompt, a look, a line or subtitle, and events. I3 saves CP2 and then starts F1; I8 ends the level through <code>ALevelExitTrigger::Fire()</code>, which already exists.</li>
        <li><b>Section streaming both ways, and checkpoints:</b> a border door that holds until the section behind it is loaded, and sections that remember what's done.</li>
        <li><b>A fight started by an event</b> rather than a volume (F1 on I3; F8 as you leave the cells).</li>
        <li><b>Civilians</b> on the street, up to 12, no fighting. What you can do with them is still undecided.</li>
        <li>Optional: <b>a scripted flee</b> for F12's survivors.</li>
      </ul>
      <h3 style="margin-top:12px">Layout calls I made</h3>
      <ul>
        <li>The car's lane is gated at both ends. It's the car's route, never yours, and it's why you go round.</li>
        <li>Section borders are swinging doors you can go back through, not drops (your call, 2026-11-08). Nothing locks behind you.</li>
        <li>No fight in the cells. The reveal stays quiet, with F7 before it and F8 after.</li>
        <li>Pallets inside the bodega door cut what would be a 37 m line from the alley's end.</li>
        <li>CP2 saves after the car inspect, so a death in F1 doesn't replay the reveal.</li>
      </ul>
    </section>
    <section class="owned">
      <h2>Open — yours to call</h2>
      <ul>
        <li>The level's name (a story level, so no <code>_Arena</code>).</li>
        <li>Is the patrolman's body at the car, and where?</li>
        <li>How Navarro arrives, and whether he starts with a .45 or a revolver (the plan assumes a .45).</li>
        <li>What the clues are at I1, I2 and I7 (my suggestions are marked).</li>
        <li>Navarro's lines at each inspect: voice, subtitles, or none.</li>
        <li>Who the civilians are and what you can do with them, and who the gunmen are.</li>
        <li>“Drives off”: a scripted escape, or kill them all.</li>
        <li>Whether any door should lock behind you for a story reason. The plan has none, so you can walk back to the street.</li>
        <li>The exact child's items (your examples are used as given).</li>
      </ul>
    </section>
  </div>
  <p class="note">Build data: <code>Design Document/Linear_Slums_Layout.json</code> (areas, openings, stairs, cover, fights, inspects, checkpoints, the auto mass, measured sightlines). Drawing, JSON and measurements all come from <code>Tools/LevelGen/layout_linear_slums.mjs</code>.</p>
</div>
`;
fs.writeFileSync(OUT_HTML, html);
console.log("sightlines:", Object.entries(SIGHT).map(([s, v]) => `S${s} ${v.len.toFixed(1)}m f${v.f} (${v.a.map(r2)} -> ${v.b.map(r2)})`).join("\n  "));
console.log("S7 per floor:", s7.map(v => v && v.len.toFixed(1)));
console.log("mass rects:", MASS.length, " foes:", totalFoes, " mins:", mins, " html bytes:", html.length);

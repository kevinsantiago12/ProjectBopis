// Paper layout for Mission 2, the restaurant / smuggler compound (user's scenario 2026-11-13).
// One source for the drawing, the measured sightlines and the build data:
//   node Tools/LevelGen/layout_linear_restaurant.mjs
// writes Design Document/Linear_Restaurant_Layout.html and Design Document/Linear_Restaurant_Layout.json.
// Same conventions as layout_linear_slums.mjs (Mission 1): metres from the NW corner, x east, y south; building faces on the
// 1.5 m grid, partitions and openings may sit off it. Floors: 0 ground, 1 = +3.5 m (Lvl_01_Slum's storey, user 2026-11-08:
// "the interiors are too tall").
// The lead is "he" here: no name in the build (user, 2026-11-13: "ignore the Navarro name, To be decided").
// Gunmen and pickups are rough guides (user, 2026-11-12); the geometry is what gets built.
// Loops (Claude-Rules §8, 2026-11-12): the courtyard is the mid room, met twice from different entrances (west, then north).
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const OUT_HTML = path.join(ROOT, "Design Document", "Linear_Restaurant_Layout.html");
const OUT_JSON = path.join(ROOT, "Design Document", "Linear_Restaurant_Layout.json");

// ---------------------------------------------------------------------------------------------------------------
// Sections (streamed). The courtyard (3) is crossed twice, so 3 borders four sections and the loading rule has to be "the one
// you're in and every section it borders", not "either side".
const SECTIONS = [
  { id: 1, name: "The street", ground: "0", kind: "walk-around",
    what: "A street, the restaurant's open front halfway along. The informant waits at an eskinita mouth near the start: the passport maker is inside. No civilians in play (the recognition cutscene gets the customers out).",
    label: [1, 64.6] },
  { id: 2, name: "The restaurant", ground: "0", kind: "wave encounter + fight",
    what: "Dining room, counter, kitchen, dry store. He's recognised a few steps in; a cutscene gets the customers and staff out, then the waves. Kill the count and the kitchen door opens.",
    label: [14, 58.5] },
  { id: 3, name: "The back lanes", ground: "0", kind: "fights · loop 1",
    what: "The covered service lane behind the kitchen, a small courtyard where the lanes meet, and a chained lane north. Crossed twice: west to east first, then from the north, out of the flats.",
    label: [22.5, 50.6] },
  { id: 4, name: "Storage", ground: "0", kind: "fight",
    what: "A storage hall of stacked boxes, a loading room and an office. They're carrying boxes out as he comes in. The stair up is in the far corner.",
    label: [60, 57.4] },
  { id: 5, name: "Upstairs + the roof", ground: "+3.5, then 0", kind: "fights",
    what: "Safe rooms above the storage hall, out onto the workshop's flat roof, a plank across the lane into the next building's upper floor, then down its stair and out its front door into the courtyard again.",
    label: [73, 28.4] },
  { id: 6, name: "Workshop + burn yard", ground: "0", kind: "fights",
    what: "A workshop off the lane, then a narrow yard where they're burning papers in drums. A side gate at its west end lets out into the back alleys.",
    label: [73, 24.6] },
  { id: 7, name: "The back alleys", ground: "0", kind: "fights · loop 2",
    what: "Alleys as the arena's: 4.5 m between houses, bending every 15 m or so, posts, tanks and parked bikes in them. They ring a block of houses, through a half-court where they make a stand, and come back round to the first alley's corner from the north, where the safe house's side door is.",
    label: [-1, 41.5] },
  { id: 8, name: "The safe house", ground: "0 / +3.5", kind: "fights",
    what: "Two storeys of stash and safe rooms: the front room and stash room, up the stair, round the floor, down the back stair into the back room, which they've knocked through into the print shop's front.",
    label: [31, 4.4] },
  { id: 9, name: "Print shop", ground: "0 / +3.5", kind: "fights + the turn",
    what: "A print shop with its shutters down, presses half pulled apart. Upstairs, the document lab, the photo room and the passport maker's office. Out by the side stair to the next street.",
    label: [50, 4.4] },
];

// Walkable areas. kind: open (outside), cov (outside, roofed), room (walled), void (no floor: seen through, not stood on),
// off (walkable but out of bounds).
const A = (id, sec, f, kind, x0, y0, x1, y1, label = "", o = {}) => ({ id, sec, f, kind, x0, y0, x1, y1, label, ...o });
const AREAS = [
  // 1 The street (the stall and the jeepney break its 51 m into two halves)
  A("ST", 1, 0, "open", 0, 66, 51, 73.5, "street"),
  // 2 The restaurant (15 x 15, one storey entered; the family's rooms above are not)
  A("DIN", 2, 0, "room", 30, 57, 45, 66, "dining room"),
  A("KIT", 2, 0, "room", 34.5, 51, 45, 57, "kitchen"),
  A("DRY", 2, 0, "room", 30, 51, 34.5, 57, "dry store"),
  // 3 The back lanes: the service lane (roofed), the courtyard, the chained lane north
  A("LA", 3, 0, "cov", 39, 48, 48, 51, "service lane"),
  A("CY", 3, 0, "open", 48, 39, 57, 51, "courtyard"),
  A("LC", 3, 0, "open", 54, 27, 57, 39, ""),
  // 4 Storage (15 x 15, 2 storeys; the upper floor is section 5)
  A("SH", 4, 0, "room", 57, 39, 72, 48, "storage hall"),
  A("LR", 4, 0, "room", 57, 48, 64.5, 54, "loading room"),
  A("SO", 4, 0, "room", 64.5, 48, 72, 54, "office"),
  // 5 Upstairs over the storage hall, the workshop's roof, the plank, and the flats (12 x 12, 2 storeys)
  A("UA", 5, 1, "room", 57, 39, 64.5, 46.5, "safe room"),
  A("UB", 5, 1, "room", 64.5, 39, 72, 46.5, "stash room"),
  A("UC", 5, 1, "room", 57, 46.5, 64.5, 54, "bunks"),
  A("UD", 5, 1, "room", 64.5, 46.5, 72, 54, "kitchen"),
  A("SW1", 5, 1, "void", 70.2, 41.25, 72, 46.05, ""),
  A("ROOF", 5, 1, "open", 57, 27, 72, 39, "workshop roof"),
  A("PLANK", 5, 1, "open", 54, 31.5, 57, 33, ""),
  A("AU1", 5, 1, "room", 48, 27, 54, 33, ""),
  A("AU2", 5, 1, "room", 42, 27, 48, 33, ""),
  A("AU3", 5, 1, "room", 42, 33, 54, 39, "flat"),
  A("SW2", 5, 1, "void", 48.6, 33.6, 53.4, 35.4, ""),
  A("AG1", 5, 0, "room", 42, 33, 54, 39, "front room"),
  A("AG2", 5, 0, "room", 42, 27, 54, 33, "back room"),
  // 6 Workshop (one storey: its roof is section 5's) and the burn yard
  A("WS", 6, 0, "room", 57, 27, 72, 39, "workshop"),
  A("BC", 6, 0, "open", 48, 21, 72, 27, "burn yard"),
  // 7 The back alleys: 4.5 m wide as the arena's (user, 2026-11-13: "add more backalleys, somilar to what we have in the arena",
  // "except linear", "linear or looping"). A ring round a block of houses, every leg 15 m or less.
  A("AL1", 7, 0, "open", 33, 21, 48, 25.5, "alley"),
  A("AL2", 7, 0, "open", 28.5, 21, 33, 37.5, ""),
  A("AL3", 7, 0, "open", 15, 33, 28.5, 37.5, "alley"),
  A("AL4", 7, 0, "open", 10.5, 22.5, 15, 37.5, ""),
  A("PK", 7, 0, "open", 7.5, 12, 19.5, 22.5, "half-court"),
  A("AL5", 7, 0, "open", 19.5, 12, 33, 16.5, "alley"),
  A("PSG", 7, 0, "open", 28.5, 16.5, 33, 21, ""),
  // 8 The safe house (15 x 15, 2 storeys), its back room knocked through into the print shop
  A("SG1", 8, 0, "room", 33, 13.5, 42, 21, "front room"),
  A("SG2", 8, 0, "room", 42, 13.5, 48, 21, "stash room"),
  A("SG3", 8, 0, "room", 33, 6, 48, 13.5, "back room"),
  A("SU1", 8, 1, "room", 33, 13.5, 42, 21, ""),
  A("SW4", 8, 1, "void", 34.8, 19.2, 39.6, 21, ""),
  A("SU2", 8, 1, "room", 42, 13.5, 48, 21, "safe room"),
  A("SU3", 8, 1, "room", 33, 6, 48, 13.5, "bunk room"),
  A("SW5", 8, 1, "void", 34.2, 7.5, 36, 12.3, ""),
  // 9 The print shop (18 x 15, 2 storeys) and the side lane out
  A("PS", 9, 0, "room", 48, 12, 60, 21, "print shop"),
  A("PP", 9, 0, "room", 60, 12, 66, 21, "paper store"),
  A("PF", 9, 0, "room", 48, 6, 66, 12, "shop front (shutters down)"),
  A("EX", 9, 0, "open", 66, 6, 70.5, 21, "side lane"),
  A("UL", 9, 1, "room", 48, 6, 66, 10.5, "upper hall"),
  A("SW3", 9, 1, "void", 58.5, 7, 63.3, 8.8, ""),
  A("DL", 9, 1, "room", 48, 10.5, 60, 21, "document lab"),
  A("PH", 9, 1, "room", 60, 10.5, 66, 15, "photos"),
  A("FO", 9, 1, "room", 60, 15, 66, 21, "his office"),
  A("EXL", 9, 1, "open", 66, 18, 69, 21, ""),
];

// Openings (segments on a wall). k: door1 (1 m; 1.1 m at a swinging door's jamb), door (2.25 m), knock (knocked-through or a
// window knocked out), front (open shop front), open (a doorway with no door).
const O = (f, ax, ay, bx, by, k) => ({ f, a: [ax, ay], b: [bx, by], k });
const OPENINGS = [
  O(0, 33, 66, 42, 66, "front"),            // the street -> dining room: the shutters are up
  O(0, 35.25, 57, 37.5, 57, "door"),        // dining -> kitchen (a swinging door), west of the back door: no line street-to-lane.
                                            // Barred until F1's kill count (the wave encounter's event opens it).
  O(0, 30, 59.25, 30, 60.35, "door1"),      // dining -> the stair up to the family's rooms (not entered): F1's last wave comes down it
  O(0, 34.5, 52.5, 34.5, 54.75, "door"),    // kitchen -> dry store
  O(0, 42, 51, 44.25, 51, "door"),          // kitchen -> service lane (2|3)
  O(0, 57, 42.75, 57, 45, "door"),          // courtyard -> storage hall (3|4)
  O(0, 58.5, 48, 60.75, 48, "door"),        // storage hall -> loading room
  O(0, 64.5, 49.5, 64.5, 51.75, "door"),    // loading room -> office
  O(0, 49.5, 39, 51.75, 39, "door"),        // flats' front room -> courtyard (5|3)
  O(0, 43.5, 33, 45.75, 33, "door"),        // front room -> back room
  O(0, 57, 33, 57, 35.25, "door"),          // the lane -> workshop (3|6)
  O(0, 64.5, 27, 66.75, 27, "door"),        // workshop -> burn yard
  O(0, 33, 14, 33, 16.25, "door"),          // the alleys -> the safe house's side door (7|8)
  O(0, 42, 14.25, 42, 16.5, "door"),        // front room -> stash room
  O(0, 48, 6.5, 48, 8.75, "knock"),         // the safe house's back room -> the print shop's front, knocked through (8|9)
  O(0, 60, 15, 60, 17.25, "door"),          // print shop -> paper store
  O(0, 49.5, 12, 51.75, 12, "door"),        // print shop -> shop front (the stair)
  O(1, 66, 46.5, 68.25, 46.5, "door"),      // stash room -> kitchen
  O(1, 64.5, 49.5, 64.5, 51.75, "door"),    // kitchen -> bunks
  O(1, 57.75, 46.5, 60, 46.5, "door"),      // bunks -> safe room (west; the roof door is east, so no line through both)
  O(1, 62, 39, 64.25, 39, "door"),          // safe room -> the roof
  O(1, 54, 31.5, 54, 33, "knock"),          // the plank -> the flats: a window knocked out
  O(1, 48, 28.5, 48, 30.75, "door"),
  O(1, 43.5, 33, 45.75, 33, "door"),
  O(1, 42, 15, 42, 17.25, "door"),          // safe house: landing room -> safe room
  O(1, 44.25, 13.5, 46.5, 13.5, "door"),    // safe room -> bunk room (the back stair)
  O(1, 50.25, 10.5, 52.5, 10.5, "door"),    // upper hall -> document lab
  O(1, 60, 12, 60, 14.25, "door"),          // lab -> photos
  O(1, 60, 17.25, 60, 19.5, "door"),        // lab -> his office (barred until the lab is clear)
  O(1, 66, 18.75, 66, 19.85, "door1"),      // his office -> the side stair's landing
];
// Closed barriers between open areas (block movement and sight)
const BARRIERS = [
  { f: 0, a: [54, 39], b: [57, 39], k: "gate", label: "chained gate (F8's wave opens it)" },
  { f: 0, a: [54, 27], b: [57, 27], k: "wall", label: "" },     // the lane's end: a wall, not into the burn yard
  { f: 0, a: [66, 21], b: [72, 21], k: "wall", label: "" },     // burn yard | side lane
  { f: 0, a: [48, 22.5], b: [48, 27], k: "wall", label: "" },   // burn yard | the alleys: a wall, the side gate at its north end (6|7)
  { f: 0, a: [28.5, 21], b: [33, 21], k: "gate", label: "chained gate (F14's wave opens it)" },
  { f: 0, a: [66, 6], b: [70.5, 6], k: "gate", label: "side gate to the next street (I10)" },
];
// Stairs: r on base floor f, up = direction you face going up. The kit's 36 degrees: about 4.8 m of run for 3.5 m.
const STAIRS = [
  { f: 0, r: [70.2, 41.25, 72, 46.05], up: "N", rise: 3.5 },                  // storage hall -> stash room
  { f: 0, r: [48.6, 33.6, 53.4, 35.4], up: "W", rise: 3.5 },                  // the flats: down to the front room, foot by the door
  { f: 0, r: [58.5, 7, 63.3, 8.8], up: "E", rise: 3.5 },                      // print shop front -> upper hall
  { f: 0, r: [66.6, 13.2, 68.4, 18], up: "S", rise: 3.5, label: "steel" },   // the side stair, from his office's landing down to the lane
  { f: 0, r: [34.8, 19.2, 39.6, 21], up: "W", rise: 3.5 },                    // safe house: front room -> landing room
  { f: 0, r: [34.2, 7.5, 36, 12.3], up: "N", rise: 3.5, label: "wooden" },   // safe house: bunk room -> back room
];
const LANDINGS = [];
// Cover: low = dive past, tall = blocks sight
const C = (f, x0, y0, x1, y1, tall, label = "") => ({ f, r: [x0, y0, x1, y1], tall, label });
const COVER = [
  // street
  C(0, 23, 66, 26, 68.75, true, "stall"),
  C(0, 24, 69.75, 28.5, 72.5, true, "jeepney"),
  C(0, 8.5, 71, 10.3, 72.6, false, "tricycle"),
  C(0, 45.5, 67, 50, 69.2, true, "van"),
  C(0, 31, 70.6, 32.6, 72, false, "tables"),
  // restaurant
  C(0, 39, 57.75, 44.5, 58.75, false, "counter"),
  C(0, 32, 61, 33.5, 62.5, false, "table"),
  C(0, 35.5, 61, 37, 62.5, false, "table"),
  C(0, 39, 61, 40.5, 62.5, false, "table"),
  C(0, 42.5, 61, 44, 62.5, false, "table"),
  C(0, 32.5, 63.8, 34, 65, false, "table"),
  C(0, 42.5, 63.8, 44, 65, false, "table"),
  C(0, 37.4, 63.6, 38.6, 64.8, true, "pillar"),
  C(0, 37, 53, 41.5, 54.2, false, "prep table"),
  C(0, 43.6, 51.6, 44.9, 54.2, false, "stoves"),
  C(0, 30.6, 51.6, 31.8, 56.2, true, "shelves"),
  // back lanes
  C(0, 45.4, 48.3, 46.7, 49.6, false, "drums"),
  C(0, 49.5, 43.5, 51.5, 45.5, true, "tank stand"),
  C(0, 53.4, 47.6, 55.4, 48.8, false, "bench"),
  C(0, 54.3, 29.6, 55.7, 31, false, "crates"),
  // storage
  C(0, 59.5, 40.5, 62, 42.5, true, "boxes"),
  C(0, 63.5, 43.5, 66.5, 45.5, true, "boxes"),
  C(0, 60, 45.2, 61.8, 46.8, false, "boxes"),
  C(0, 66.8, 40, 68.6, 41.5, false, "sacks"),
  C(0, 60, 50.4, 62.5, 51.8, false, "pallet"),
  C(0, 67.5, 51.5, 70.5, 52.7, false, "desk"),
  // upstairs + roof + flats
  C(1, 65.5, 40, 67.5, 41.5, false, "boxes"),
  C(1, 58, 49.5, 59.2, 53.4, false, "bunks"),
  C(1, 66.5, 29, 68.5, 31, true, "water tanks"),
  C(1, 61.5, 34.5, 63, 36, true, "tank"),
  C(1, 69.4, 35.4, 71.2, 37, false, "drums"),
  C(1, 43, 35.4, 45.4, 36.6, false, "sofa"),
  // workshop + burn yard
  C(0, 59, 29.4, 63, 30.6, false, "workbench"),
  C(0, 66, 33.5, 70, 34.7, false, "workbench"),
  C(0, 68.5, 36, 70.5, 38, true, "crates"),
  C(0, 58.5, 22, 62, 24.6, true, "multicab"),
  C(0, 51, 23, 52.4, 24.4, false, "burn drum"),
  C(0, 64, 24.6, 65.2, 25.8, false, "burn drum"),
  // the back alleys
  C(0, 36, 21, 39.5, 22.8, true, "owner-type jeep"),
  C(0, 44, 24, 45.2, 25.2, false, "drums"),
  C(0, 29.4, 28, 31.2, 28.8, false, "motorbike"),
  C(0, 31.2, 32, 33, 34, true, "tank stand"),
  C(0, 20, 33.2, 22, 34, false, "bench"),
  C(0, 24, 35.4, 25.5, 37.5, true, "crates"),
  C(0, 16, 36, 17.2, 37.2, false, "drums"),
  C(0, 10.5, 24, 12.5, 26, true, "tank stand"),
  C(0, 13.2, 29, 14.8, 30.6, false, "tricycle"),
  C(0, 11.5, 12, 15.5, 14.5, true, "sari-sari stall"),
  C(0, 10, 17, 11.5, 18.5, false, "tables"),
  C(0, 16.4, 19.6, 18, 20.6, false, "bench"),
  C(0, 8, 20.2, 9.6, 21.2, false, "motorbike"),
  C(0, 22, 15.2, 23.2, 16.4, false, "drums"),
  C(0, 27, 14.4, 31, 16.4, true, "multicab"),
  // safe house
  C(0, 36, 16.6, 38.4, 17.6, false, "table"),
  C(0, 43, 18.8, 46.6, 20.2, false, "rice sacks"),
  C(1, 43.4, 15.4, 44.6, 19, false, "mattresses"),
  C(1, 39.6, 7.2, 46.6, 8.4, false, "bunks"),
  // print shop
  C(0, 50.5, 14.5, 53, 16.5, true, "press"),
  C(0, 55, 17, 57.5, 19, true, "press"),
  C(0, 55.5, 13.2, 57.5, 14.4, false, "cutter"),
  C(0, 61, 13, 63, 15, true, "paper"),
  C(0, 50.5, 6, 51.7, 10, true, "shelves"),       // just inside the knock-through: no line down the shop front
  C(0, 53.5, 7.2, 57, 8.2, false, "counter"),
  C(1, 50, 13, 53, 14.2, false, "laminator"),
  C(1, 54.5, 16, 57.5, 17.2, false, "seal desk"),
  C(1, 50, 18.5, 53, 19.7, false, "light table"),
  C(1, 57.6, 11.2, 59.6, 12.4, true, "shelves"),
  C(1, 62, 18.6, 64.4, 19.8, false, "desk"),
];
const ROOFS = [
  { f: 0, r: [39, 48, 48, 51], label: "" },   // the service lane's lean-to
  { f: 0, r: [15, 33, 22.5, 37.5], label: "" },   // a lean-to over part of the long alley
];

// Fights: enemies [x, y, "c" crouched, floor if not the fight's], wave doors, label position
const FIGHTS = [
  // A wave encounter (user, 2026-11-13: "for this level, we can start using wave stlye encounters, in the restaurant is a good spot
  // to put it, where you have to kill x amount of enemies for the next event that would open the door start"). No civilians in play:
  // "remove the civilians in real time,we will evacuate them via cutscene".
  { id: "F1", sec: 2, room: "Dining room", kind: "waves", start: 4, wave: 7, max: 5, killTo: 11, trigger: "the recognition cutscene (it gets the customers and staff out)", f: 0,
    waves: [{ n: 4, from: "at the tables, once the room is cleared" }, { n: 4, from: "in at the front, off the street" }, { n: 3, from: "down the stair from the rooms above" }],
    opens: "the kitchen door: the last of them kick it open and fall back through the kitchen",
    foes: [[33.6, 63.2], [41.2, 60.2], [44, 60], [41.6, 59.3, "c"]], waveDoors: [[37.5, 66.4], [30, 59.8]], lab: [37.6, 60.2],
    note: "A wave encounter: kill 11 and the kitchen door opens. It's barred from the kitchen side until then. A cutscene, not live civilians, shows him recognised and the customers and staff got out. Then four at the tables, four in at the front off the street, three down the stair from the family's rooms above. Never more than 5 up at once. Tables and the counter are low cover, the pillar is the only full cover." },
  { id: "F2", sec: 2, room: "Kitchen", start: 4, wave: 0, max: 4, trigger: "the kitchen door", f: 0,
    foes: [[39.5, 52.2, "c"], [44, 55.6], [33.2, 54.4], [41.6, 55.4, "c"]], lab: [39.6, 56.2],
    note: "Close quarters round the prep table, one in the dry store. They're going out the back door, not holding." },
  { id: "F3", sec: 3, room: "Service lane + courtyard", start: 4, wave: 2, max: 4, trigger: "the kitchen's back door", f: 0,
    foes: [[46.2, 49.4, "c"], [50.4, 47.4], [53.6, 41.6], [55.8, 46.4, "c"]], waveDoors: [[57, 43.9]], lab: [52.4, 50.2],
    note: "Out of the kitchen into a 3 m lane under a lean-to roof, then the courtyard where the lanes meet. The wave comes out of the storage side door, the way on." },
  { id: "F4", sec: 4, room: "Storage hall", start: 5, wave: 1, max: 5, trigger: "the side door: they're carrying boxes out", f: 0,
    foes: [[60.6, 44], [64.6, 41.4, "c"], [68.2, 44.2], [69.2, 47, "c"], [70.6, 40.2, "", 1]], waveDoors: [[59.6, 48]], lab: [64.6, 47.2],
    note: "Stacks of boxes break the hall into short lanes. One holds the head of the stair in the far corner; one comes in from the loading room." },
  { id: "F5", sec: 5, room: "Rooms over the hall", start: 4, wave: 0, max: 4, trigger: "the top of the stair", f: 1,
    foes: [[68.2, 49.8], [61.6, 51.6, "c"], [62.6, 43.4], [58.6, 41.6, "c"]], lab: [64.5, 55.4],
    note: "Room to room, a loop round the floor: stash room, kitchen, bunks, the safe room. The safe room's door is the way out onto the roof." },
  { id: "F6", sec: 5, room: "The workshop roof", start: 3, wave: 1, max: 3, trigger: "the roof door", f: 1,
    foes: [[64.6, 31.8, "c"], [69.8, 32.6], [59, 28.6]], waveDoors: [[54, 32.25]], lab: [64.5, 26.2],
    note: "In the open, among water tanks, with the lane below. The last one comes across the plank from the flats." },
  { id: "F7", sec: 5, room: "The flats", start: 4, wave: 0, max: 4, trigger: "the knocked-out window", f: 1,
    foes: [[45, 30.2], [44.4, 37.4, "c"], [52.4, 29.6], [52.4, 37.4, "", 0]], lab: [45, 40.4],
    note: "Two small rooms and the front room upstairs, then one waiting at the foot of the stair, by the front door." },
  { id: "F8", sec: 3, room: "Courtyard, from the north", start: 3, wave: 3, max: 4, trigger: "the flats' front door", f: 0,
    foes: [[50.4, 47.4, "c"], [55.2, 49.6], [46.4, 49.6]], waveDoors: [[55.5, 39.4], [43.1, 50.6]], lab: [52.4, 52.2],
    note: "Loop 1: the courtyard again, from the other side. They've moved across the block: men in the service lane where he came from, and a wave that comes down the chained lane (opening its gate, which is the way on) and out of the kitchen." },
  { id: "F9", sec: 6, room: "Lane + workshop", start: 5, wave: 0, max: 5, trigger: "through the lane gate", f: 0,
    foes: [[55.5, 29.4, "c"], [60.6, 33.8], [64, 36.8, "c"], [69.8, 31.2], [61.5, 37.4]], lab: [64.5, 40.8],
    note: "One at the lane's dead end, four in the workshop among the benches. The plank you crossed is over your head." },
  { id: "F10", sec: 6, room: "Burn yard", start: 4, wave: 2, max: 4, trigger: "the workshop's back door", f: 0,
    foes: [[51.8, 25.4], [57.6, 23.2, "c"], [66.4, 22.6], [70, 25.6]], waveDoors: [[48.4, 21.75]], lab: [60.2, 28.2],
    note: "They're feeding papers into drums as he comes out. A parked multicab splits the yard. The wave comes in through the side gate from the alleys, the way on." },
  { id: "F11", sec: 7, room: "The first alley", start: 4, wave: 0, max: 4, trigger: "the side gate", f: 0,
    foes: [[42.6, 23.6, "c"], [34.4, 24.2], [30.2, 30.6], [32, 36.2, "c"]], lab: [40.5, 27.4],
    note: "Out of the gate, an owner-type jeep parked across half the alley, then the turn south. The chained gate north of the corner stays shut: that's where you'll come back to." },
  { id: "F12", sec: 7, room: "The long alley", start: 4, wave: 1, max: 4, trigger: "the turn west", f: 0,
    foes: [[26.2, 34, "c"], [18.6, 35], [12.6, 31.4], [13.8, 27.4, "c"]], waveDoors: [[22, 33]], lab: [21.6, 39.6],
    note: "West under a lean-to, then the turn north. One comes out of a house door behind the bench." },
  { id: "F13", sec: 7, room: "The half-court", start: 5, wave: 2, max: 5, trigger: "the mouth of the half-court", f: 0,
    foes: [[9.4, 19.4, "c"], [13.4, 17.6], [17.6, 21.6], [16.8, 15.6, "c"], [9, 15.4]], waveDoors: [[19.5, 14.25], [7.5, 16.5]], lab: [13.5, 24.6],
    note: "The widest place in the alleys, 12 × 10.5 m, a sari-sari stall in one corner. They make a stand here; the wave comes in from the alley east and a house on the west side." },
  { id: "F14", sec: 7, room: "Back at the corner, from the north", start: 3, wave: 3, max: 4, trigger: "the end of the alley east", f: 0,
    foes: [[25.4, 13.4, "c"], [30.4, 13], [31.6, 18.6]], waveDoors: [[30.75, 21.4]], lab: [26, 19.2],
    note: "Loop 2: the alleys come round to the first alley's corner from the north. The safe house's side door is here; men are waiting at it, and the wave opens the chained gate from the first alley, so you're shooting back down the way you came in." },
  { id: "F15", sec: 8, room: "Safe house, ground", start: 4, wave: 0, max: 4, trigger: "the side door", f: 0,
    foes: [[37.6, 14.6], [40.6, 18, "c"], [45.6, 15.4], [46.6, 17.6, "c"]], lab: [40.5, 23.6],
    note: "The front room and the stash room. The stair up is along the front room's south wall." },
  { id: "F16", sec: 8, room: "Safe house, upstairs", start: 5, wave: 0, max: 5, trigger: "the top of the stair", f: 1,
    foes: [[38.6, 16.4], [45, 20.2, "c"], [46.6, 15.4], [38.4, 10.4], [44.6, 10, "c"]], lab: [40.5, 23.6],
    note: "Round the floor: the landing room, the safe room, the bunk room. Down the wooden back stair into the back room, knocked through into the print shop." },
  { id: "F17", sec: 9, room: "Print shop", start: 6, wave: 0, max: 5, trigger: "through the knocked-out wall", f: 0,
    foes: [[56, 10.2], [53.6, 13.4, "c"], [58.6, 19.8], [62.6, 18.8], [49.6, 19.4, "c"], [57.6, 15.6]], lab: [54, 22.6],
    note: "In through the shop front, shutters down. Behind it the presses are half pulled apart, one in the paper store." },
  { id: "F18", sec: 9, room: "Document lab (+3.5)", start: 5, wave: 2, max: 5, trigger: "the top of the stair", f: 1,
    foes: [[49.8, 12.4, "c"], [53.8, 18.2], [57.8, 15, "c"], [58.6, 19.8], [55.6, 11.6]], waveDoors: [[60, 13.1]], lab: [54, 22.4],
    note: "The last fight, in the room the case is about. The wave comes out of the photo room. The office door stays barred until the lab is clear." },
];
// Inspects: req = the route waits on it. src: scenario = the user's text, suggestion = mine.
const INSPECTS = [
  { id: "I1", f: 0, x: 7.6, y: 67.2, sec: 1, name: "The informant (Jun-Jun)", req: true,
    src: "scenario", what: "A teenage street informant confirms the passport maker is inside the restaurant right now. He's paid a few hundred pesos and jokes that he's too cheap.", sug: "", does: "Saves CP2 by the restaurant's front." },
  { id: "I2", f: 0, x: 61.6, y: 52.8, sec: 4, name: "Storage", req: false,
    src: "scenario", what: "Rooms used for storage: the smuggling side of the ring.", sug: "Cartons of cigarettes and boxed appliances with no duty stamps, and a ledger of deliveries by date.", does: "" },
  { id: "I3", f: 1, x: 58.4, y: 40.6, sec: 5, name: "Safe room", req: false,
    src: "scenario", what: "A temporary safe room.", sug: "Mattresses, a bag packed to run, a cash box left open.", does: "" },
  { id: "I4", f: 0, x: 53, y: 24.8, sec: 6, name: "The burn drums", req: false,
    src: "scenario", what: "Papers being burned to cover their tracks.", sug: "Half-burnt sheets of passport-page print and photo strips in the ash.", does: "" },
  { id: "I5", f: 0, x: 45, y: 17.6, sec: 8, name: "Stash room", req: false,
    src: "scenario", what: "A stash room.", sug: "Rice sacks with bundles of cash inside, and a carton of blank passport booklets.", does: "" },
  { id: "I6", f: 0, x: 56.6, y: 15.2, sec: 9, name: "A press pulled apart", req: false,
    src: "scenario", what: "Equipment pulled apart in a rush.", sug: "", does: "" },
  { id: "I7", f: 1, x: 55, y: 15.2, sec: 9, name: "The document lab", req: true,
    src: "scenario", what: "Printers, fake seals, blank papers, passport photos and incomplete identity documents, matching the ones from Mission 1: the passports were made here.", sug: "", does: "Saves CP14 and unbars his office." },
  { id: "I8", f: 1, x: 62.8, y: 12.4, sec: 9, name: "Passport photos", req: false,
    src: "scenario", what: "Passport photos.", sug: "A backdrop sheet and a camera on a stand, the photos cut and sorted into envelopes.", does: "" },
  { id: "I9", f: 1, x: 62.6, y: 17.2, sec: 9, name: "The passport maker", req: true,
    src: "scenario", what: "Cornered, he says he's only a forger and smuggler. Threatened with the trafficking case, he breaks: a big batch, no questions, through intermediaries. He gives the address he delivered to: an active construction site.", sug: "", does: "Saves CP15; the way out." },
  { id: "I10", f: 0, x: 68.2, y: 7, sec: 9, name: "The way out", req: true,
    src: "suggestion", what: "", sug: "Down the side stair and out through the side gate to the next street, leaving the block with the address.", does: "Ends the level (ALevelExitTrigger::Fire)." },
];
const CHECKPOINTS = [
  { id: "CP1", f: 0, x: 3, y: 69.75, sec: 1, at: "level start" },
  { id: "CP2", f: 0, x: 36.4, y: 67.4, sec: 1, at: "the informant done: the restaurant's front" },
  { id: "CP3", f: 0, x: 41.6, y: 49.6, sec: 3, at: "the kitchen's back door" },
  { id: "CP4", f: 0, x: 58.4, y: 43.9, sec: 4, at: "inside the storage side door" },
  { id: "CP5", f: 1, x: 69.2, y: 42.2, sec: 5, at: "the top of the stair" },
  { id: "CP6", f: 1, x: 63.1, y: 37.6, sec: 5, at: "out on the roof" },
  { id: "CP7", f: 0, x: 50.4, y: 36.8, sec: 5, at: "the flats' front room, at the foot of the stair" },
  { id: "CP8", f: 0, x: 55.5, y: 37.2, sec: 3, at: "through the lane gate" },
  { id: "CP9", f: 0, x: 66.8, y: 25.6, sec: 6, at: "the workshop's back door" },
  { id: "CP10", f: 0, x: 46.4, y: 22.4, sec: 7, at: "through the side gate into the alleys" },
  { id: "CP11", f: 0, x: 13.6, y: 23.4, sec: 7, at: "the mouth of the half-court" },
  { id: "CP12", f: 0, x: 34.6, y: 15.2, sec: 8, at: "inside the safe house's side door" },
  { id: "CP13", f: 1, x: 64.6, y: 9.6, sec: 9, at: "the top of the print shop's stair" },
  { id: "CP14", f: 1, x: 57, y: 19.6, sec: 9, at: "the lab inspected (I7)" },
  { id: "CP15", f: 1, x: 64.4, y: 16.4, sec: 9, at: "after the passport maker: the way out" },
];
// First aid only, as in Mission 1 (an assumption: the arms and pickups for this level are open). Rough guides.
const PICKUPS = [
  { f: 0, x: 32.2, y: 52.6, label: "first aid" },
  { f: 0, x: 70.4, y: 49.6, label: "first aid" },
  { f: 0, x: 44, y: 28.8, label: "first aid" },
  { f: 0, x: 18.4, y: 13.2, label: "first aid" },
  { f: 0, x: 64.6, y: 19.8, label: "first aid" },
];
const ARMS = "not set yet: Mission 1's .45 pistols, revolvers and shotguns assumed";
// No civilians in play (user, 2026-11-13: "remove the civilians in real time,we will evacuate them via cutscene").
const CIVILIANS = [];
// Section borders. Every one is a door or gate except the restaurant's open front, the stair and the knock-through.
const CONNECTORS = [
  { from: 1, to: 2, a: [33, 66], b: [42, 66], door: false, note: "the restaurant's open front" },
  { from: 2, to: 3, a: [42, 51], b: [44.25, 51], door: true, note: "the kitchen's back door" },
  { from: 3, to: 4, a: [57, 42.75], b: [57, 45], door: true, note: "the storage hall's side door" },
  { from: 4, to: 5, a: [70.2, 41.25], b: [72, 41.25], door: false, note: "the stair up (a stairwell, not a door)" },
  { from: 5, to: 3, a: [49.5, 39], b: [51.75, 39], door: true, note: "the flats' front door, back into the courtyard" },
  { from: 3, to: 6, a: [57, 33], b: [57, 35.25], door: true, note: "the workshop's side door, off the chained lane" },
  { from: 6, to: 7, a: [48, 21], b: [48, 22.5], door: true, note: "a side gate at the burn yard's west end" },
  { from: 7, to: 8, a: [33, 14], b: [33, 16.25], door: true, note: "the safe house's side door" },
  { from: 8, to: 9, a: [48, 6.5], b: [48, 8.75], door: false, note: "a wall knocked through into the print shop's front" },
];
const STREAM_NOTE = "As Mission 1, but the loops make the sections a graph, not a line: the courtyard (3) borders the restaurant, storage, the flats and the workshop. "
  + "Loaded is the section you're in and every section it borders. The workshop's roof is walked in 5 but belongs to the workshop's building, so 6 loads with 5 as well. "
  + "The alleys (7) are one section: their ring comes back to its own start. "
  + "A border door holds until the section behind it is loaded, unloading waits until you're a few metres past a door, and a section remembers what's done. "
  + "That memory matters more here: the courtyard and the alleys' first corner are each fought twice, and the second fight must not bring back the first one's dead.";
const START = [3, 69.75];

// The route walked, leg by leg in the order played (the courtyard twice). A stair counts by its run.
const ROUTE = [
  { sec: 1, pts: [[3, 69.75], [7.6, 68.4], [22, 69.25], [29.5, 69.25], [37.5, 67], [37.5, 66]] },
  { sec: 2, pts: [[37.5, 66], [37.5, 60], [36.4, 58.2], [36.4, 57], [36.4, 55.2], [33.2, 54], [36.4, 55.2], [42, 55.2], [43.1, 51]] },
  { sec: 3, pts: [[43.1, 51], [43.1, 49.5], [52.4, 49.2], [54, 46], [57, 43.9]] },
  { sec: 4, pts: [[57, 43.9], [59, 47], [59.6, 48], [61.4, 51.4], [59.6, 48], [68, 47.2], [71.1, 46.05], [71.1, 41.25]] },
  { sec: 5, pts: [[71.1, 41.25], [69, 44], [67.1, 46.5], [66, 50.6], [61, 50.6], [58.9, 46.5], [59.6, 42], [63.1, 39], [62, 34], [57, 32.25],
      [54, 32.25], [50.4, 30], [48, 29.6], [45, 29.6], [44.6, 33], [46, 34.5], [48.6, 34.5], [53.4, 34.5], [52.6, 37], [50.6, 39]] },
  { sec: 3, pts: [[50.6, 39], [53, 42], [55.5, 40], [55.5, 34.1], [57, 34.1]] },
  { sec: 6, pts: [[57, 34.1], [62, 32], [65.6, 28], [65.6, 27], [62, 25.8], [53, 25.6], [50, 22], [48, 21.75]] },
  { sec: 7, pts: [[48, 21.75], [40, 24.2], [30.75, 24.2], [30.75, 35.25], [12.75, 35.25], [12.75, 22.5], [13.5, 18], [19.5, 13.4], [32, 13.4], [33, 15.1]] },
  { sec: 8, pts: [[33, 15.1], [38, 15.4], [42, 15.4], [45, 17.6], [42, 15.4], [40.4, 18], [39.6, 20.1], [34.8, 20.1],
      [34, 18], [38, 16.1], [42, 16.1], [45.4, 16.1], [45.4, 13.5], [40, 9.6], [35.1, 6.8], [35.1, 7.5], [35.1, 12.3], [40, 10.6], [48, 7.6]] },
  { sec: 9, pts: [[48, 7.6], [49.6, 8], [49.6, 10.8], [50.6, 12], [54, 13], [56.6, 15.2], [58, 18.4], [60, 16.1], [62, 17], [60, 16.1], [54, 13], [50.6, 12],
      [52, 10.8], [58, 9.6], [58.5, 7.9], [63.3, 7.9], [64.5, 9.6], [51.4, 9.6], [51.4, 10.5], [55, 15.2], [59, 13.1], [62.8, 12.4], [59, 13.1],
      [59, 18.4], [62.6, 17.6], [66, 19.3], [67.5, 19.3], [67.5, 18], [67.5, 13.2], [69.4, 12], [68.2, 7]] },
];
const pathLen = p => p.slice(1).reduce((n, q, k) => n + Math.hypot(q[0] - p[k][0], q[1] - p[k][1]), 0);
// Time, first play with no deaths (Mission 1's model): 2.5 m/s walking, 12-20 s a gunman, 15-45 s an inspect.
const WALK_MS = 2.5, GUN_S = [12, 20], INSP_S = [15, 45];
const half = (v, up) => (up ? Math.ceil(v * 2) : Math.floor(v * 2)) / 2;
for (const S of SECTIONS) {
  const len = ROUTE.filter(L => L.sec === S.id).reduce((n, L) => n + pathLen(L.pts), 0);
  const foes = FIGHTS.filter(F => F.sec === S.id).reduce((n, F) => n + F.start + F.wave, 0);
  const insp = INSPECTS.filter(i => i.sec === S.id).length;
  S.route_m = Math.round(len);
  S.secs = [0, 1].map(k => len / WALK_MS + foes * GUN_S[k] + insp * INSP_S[k]);
  S.mins = S.secs.map((v, k) => half(v / 60, k === 1));
}
const secsAll = SECTIONS.reduce((m, S) => [m[0] + S.secs[0], m[1] + S.secs[1]], [0, 0]);
const routeAll = SECTIONS.reduce((n, S) => n + S.route_m, 0);

// ---------------------------------------------------------------------------------------------------------------
// Raster for sightlines (0.25 m cells). 0 solid, 1 open (stand + see), 2 see-through only (void, out of bounds)
const CELL = 0.25, GX0 = -6, GY0 = 0, GX1 = 82, GY1 = 80;
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
for (const f of [0, 1]) { const b = longestSightlines(f); for (const s in b) if (!SIGHT[s] || b[s].len > SIGHT[s].len) SIGHT[s] = b[s]; }
// longest in a fight space: every floor, the street excluded
const fightMax = Math.max(...Object.entries(SIGHT).filter(([s]) => +s >= 2).map(([, v]) => v.len));

// Auto mass: built-up ground (0.75 m cells) within 7.5 m of any ground-floor walkable area, merged into rectangles
function autoMass() {
  const C2 = 0.75, mx0 = -6, my0 = -1.5, mnx = Math.round(88 / C2), mny = Math.round(83.25 / C2);
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
// Drawing (as Mission 1's)
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
  if (f === 0) for (const [x0, y0, x1, y1] of MASS) s += `<rect x="${r2(x0)}" y="${r2(y0)}" width="${r2(x1 - x0)}" height="${r2(y1 - y0)}" class="blk"/>`;
  else for (const a of AREAS.filter(a => a.f === 0 && a.kind === "room")) s += `<rect x="${a.x0}" y="${a.y0}" width="${r2(a.x1 - a.x0)}" height="${r2(a.y1 - a.y0)}" class="below"/>`;
  const areas = AREAS.filter(a => a.f === f);
  for (const a of areas) {
    const cls = { open: "lane", cov: "lane", room: "room-f", void: "void", off: "offl" }[a.kind];
    s += `<rect x="${a.x0}" y="${a.y0}" width="${r2(a.x1 - a.x0)}" height="${r2(a.y1 - a.y0)}" class="${cls}"${a.kind === "void" ? ` fill="url(#hatch${opt.id})"` : ""}/>`;
  }
  for (const rf of ROOFS.filter(r => r.f === f)) { const [x0, y0, x1, y1] = rf.r; s += `<rect x="${x0}" y="${y0}" width="${r2(x1 - x0)}" height="${r2(y1 - y0)}" fill="url(#roof${opt.id})" class="roofo"/>`; }
  for (const a of areas.filter(a => a.kind === "void")) s += `<rect x="${a.x0}" y="${a.y0}" width="${r2(a.x1 - a.x0)}" height="${r2(a.y1 - a.y0)}" class="rail"/>`;
  // the roof's parapet and the plank's edges (upper floor, open areas)
  if (f === 1) for (const a of areas.filter(a => a.kind === "open")) s += `<rect x="${a.x0}" y="${a.y0}" width="${r2(a.x1 - a.x0)}" height="${r2(a.y1 - a.y0)}" class="parapet"/>`;
  for (const st of STAIRS.filter(st => st.f === f)) s += stairSvg(st, t);
  for (const c of COVER.filter(c => c.f === f)) { const [x0, y0, x1, y1] = c.r; s += `<rect x="${x0}" y="${y0}" width="${r2(x1 - x0)}" height="${r2(y1 - y0)}" class="${c.tall ? "tall" : "cover"}"/>`; }
  for (const a of areas.filter(a => a.kind === "room")) for (const [x0, y0, x1, y1] of wallSegments(a, f)) s += `<line x1="${x0}" y1="${y0}" x2="${x1}" y2="${y1}" class="wallx"/>`;
  for (const o of OPENINGS.filter(o => o.f === f)) if (o.k === "knock") s += `<line x1="${o.a[0]}" y1="${o.a[1]}" x2="${o.b[0]}" y2="${o.b[1]}" class="knockl"/>`;
  for (const b of BARRIERS.filter(b => b.f === f)) s += `<line x1="${b.a[0]}" y1="${b.a[1]}" x2="${b.b[0]}" y2="${b.b[1]}" class="${b.k === "wall" ? "wallx" : "gate"}"/>`;
  if (opt.connectors) for (const c of CONNECTORS) {
    const mx = (c.a[0] + c.b[0]) / 2, my = (c.a[1] + c.b[1]) / 2;
    s += `<line x1="${c.a[0]}" y1="${c.a[1]}" x2="${c.b[0]}" y2="${c.b[1]}" class="conn"/>`;
    s += `<g transform="translate(${mx} ${my})"><rect x="${fs(-1.55)}" y="${fs(-0.62)}" width="${fs(3.1)}" height="${fs(1.24)}" rx="${fs(0.62)}" class="connb"/><text y="${fs(0.27)}" class="t-conn" text-anchor="middle" style="font-size:${fs(0.78)}px">${c.from}↔${c.to}</text></g>`;
  }
  const drawn = [], near = (p, q) => Math.hypot(p[0] - q[0], p[1] - q[1]) < 3;
  if (opt.sight) for (const [sid, v] of Object.entries(SIGHT)) {
    if (v.f !== f || !opt.sight.includes(+sid)) continue;
    if (drawn.some(d => (near(d.a, v.a) && near(d.b, v.b)) || (near(d.a, v.b) && near(d.b, v.a)))) continue;
    drawn.push(v);
    s += `<line x1="${r2(v.a[0])}" y1="${r2(v.a[1])}" x2="${r2(v.b[0])}" y2="${r2(v.b[1])}" class="sight"/>`;
    const mx = (v.a[0] + v.b[0]) / 2, my = (v.a[1] + v.b[1]) / 2;
    s += `<text x="${r2(mx)}" y="${r2(my - 0.5 * t)}" class="t-a" text-anchor="middle" style="font-size:${fs(0.8)}px">${v.len.toFixed(1)} m</text>`;
  }
  for (const a of areas) if (a.label && a.kind !== "void") {
    const cx = (a.x0 + a.x1) / 2, cy = (a.y0 + a.y1) / 2, w = a.x1 - a.x0;
    const size = Math.min(0.78 * t, w / Math.max(4, a.label.length) * 1.9);
    s += `<text x="${r2(cx)}" y="${r2(a.kind === "room" ? a.y0 + 1.15 * t : cy)}" class="t-sub" text-anchor="middle" style="font-size:${r2(size)}px">${esc(a.label)}</text>`;
  }
  for (const c of (f === 0 ? CIVILIANS : [])) if (inView(...c)) s += `<circle cx="${c[0]}" cy="${c[1]}" r="${fs(0.42)}" class="civ"/>`;
  for (const p of PICKUPS.filter(p => p.f === f)) s += `<rect x="${r2(p.x - 0.42 * t)}" y="${r2(p.y - 0.42 * t)}" width="${fs(0.84)}" height="${fs(0.84)}" class="pick" transform="rotate(45 ${p.x} ${p.y})"/><text x="${p.x}" y="${r2(p.y + 1.45 * t)}" class="t-p" text-anchor="middle" style="font-size:${fs(0.66)}px">${esc(p.label)}</text>`;
  for (const F of FIGHTS) {
    let any = false;
    for (const e of F.foes) { const ef = e[3] !== undefined ? e[3] : F.f; if (ef !== f) continue; any = true;
      s += e[2] === "c" ? `<circle cx="${e[0]}" cy="${e[1]}" r="${fs(0.5)}" class="foe-c"/><circle cx="${e[0]}" cy="${e[1]}" r="${fs(0.2)}" class="spawn-d"/>` : `<circle cx="${e[0]}" cy="${e[1]}" r="${fs(0.5)}" class="spawn-d"/>`; }
    if (F.f === f) for (const w of F.waveDoors || []) { s += `<circle cx="${w[0]}" cy="${w[1]}" r="${fs(0.8)}" class="spawn"/>`; any = true; }
    if (any && (F.f === f)) s += `<text x="${F.lab[0]}" y="${F.lab[1]}" class="t-w" text-anchor="middle" style="font-size:${fs(0.82)}px">${F.id} · ${F.start}${F.wave ? "+" + F.wave : ""}</text>`;
    else if (any) { const e = F.foes.find(e => (e[3] ?? F.f) === f); s += `<text x="${r2(e[0] + 0.75 * t)}" y="${r2(e[1] + 1.25 * t)}" class="t-w" style="font-size:${fs(0.62)}px">${F.id}</text>`; }
  }
  for (const i of INSPECTS.filter(i => i.f === f)) s += `<g transform="translate(${i.x} ${i.y})"><circle r="${fs(0.62)}" class="insp${i.req ? " req" : ""}"/><line x1="${fs(0.44)}" y1="${fs(0.44)}" x2="${fs(0.95)}" y2="${fs(0.95)}" class="insp-h"/><text x="${fs(1.15)}" y="${fs(-0.5)}" class="t-i" style="font-size:${fs(0.72)}px">${i.id}</text></g>`;
  for (const c of CHECKPOINTS.filter(c => c.f === f)) s += `<g transform="translate(${c.x} ${c.y})"><path d="M0 ${fs(0.7)}V${fs(-0.85)}l${fs(1)} ${fs(0.35)}l${fs(-1)} ${fs(0.35)}" class="cp"/><text x="${fs(-0.3)}" y="${fs(1.55)}" class="t-cp" text-anchor="middle" style="font-size:${fs(0.6)}px">${c.id}</text></g>`;
  if (f === 0 && inView(...START)) s += `<circle cx="${START[0]}" cy="${START[1]}" r="${fs(0.6)}" class="start"/><text x="${START[0] + 1.2 * t}" y="${START[1] + 2.4 * t}" class="t-a" style="font-size:${fs(0.74)}px">START</text>`;
  if (opt.sections) for (const S of SECTIONS) if (opt.sections.includes(S.id)) s += `<text x="${S.label[0]}" y="${S.label[1]}" class="t-sec" style="font-size:${fs(1.5)}px">${S.id} ${esc(S.name.toUpperCase())}</text>`;
  if (opt.extra) s += opt.extra;
  return s + "</svg>";
}

// ---------------------------------------------------------------------------------------------------------------
// Page
const totalFoes = FIGHTS.reduce((n, F) => n + F.start + F.wave, 0);
const mins = [Math.floor(secsAll[0] / 60), Math.ceil(secsAll[1] / 60)];
const needed = INSPECTS.filter(i => i.req).length;
const sightRow = s => SIGHT[s] ? `${SIGHT[s].len.toFixed(1)} m${SIGHT[s].f ? " (+3.5)" : ""}` : "—";
const streetLen = SIGHT[1] ? SIGHT[1].len : 0;

// The order played, written into the plan's empty west margin
const ORDER = [[1, ""], [2, ""], [3, "west to east"], [4, ""], [5, ""], [3, "again, from the north"], [6, ""], [7, "round the ring"], [8, ""], [9, ""]];
const routeBox = (() => {
  const X = -29;
  let y = 4, s = `<text x="${X}" y="${y}" class="t-sec" style="font-size:1.5px">THE ORDER PLAYED</text>`;
  for (const [id, how] of ORDER) {
    const S = SECTIONS.find(S => S.id === id);
    const fights = FIGHTS.filter(F => F.sec === id && (id !== 3 || (how.startsWith("again") ? F.id === "F8" : F.id === "F3")));
    const foes = fights.reduce((n, F) => n + F.start + F.wave, 0);
    y += 2.2;
    s += `<text x="${X}" y="${y}" class="t-dim" style="font-size:1px"><tspan class="t-r">${id}</tspan>  ${esc(S.name)}${how ? " · " + how : ""}${fights.length ? ` · ${fights.map(F => F.id).join(" ")} (${foes})` : ""}</text>`;
  }
  y += 2.6;
  s += `<text x="${X}" y="${y}" class="t-dim" style="font-size:1px">${mins[0]}–${mins[1]} min · ${routeAll} m walked</text>`;
  s += `<text x="${X}" y="${y + 1.5}" class="t-dim" style="font-size:1px">${FIGHTS.length} fights · ${totalFoes} gunmen</text>`;
  return s;
})();
const overview = plan(0, [-31, 0, 128, 76], { id: "o", connectors: true, sections: [1, 2, 3, 4, 6, 7, 8, 9], extra: routeBox + `<text x="31.5" y="41" class="t-sec" style="font-size:1.5px">5 FLATS</text>`, sight: SECTIONS.map(S => S.id), aria: "Top-down ground plan of the whole level, nine sections from the street to the print shop" });
const upper = plan(1, [31.5, 4.5, 42, 51], { id: "u", t: 0.8, cls: "plan-s", sight: [5, 8, 9], aria: "The upper floor at +3.5 m: rooms over the storage hall, the workshop roof, the plank, the flats, the safe house and the print shop's upper floor" });

// The loops (schematic): the order played, the courtyard twice, the alleys a ring
const loopSvg = (() => {
  const box = (x, y, w, label, sub, cls = "") => `<rect x="${x}" y="${y}" width="${w}" height="6.4" rx=".6" class="sbox ${cls}"/><text x="${x + w / 2}" y="${y + 2.9}" class="t-sb" text-anchor="middle">${label}</text><text x="${x + w / 2}" y="${y + 5.1}" class="t-sbs" text-anchor="middle">${sub}</text>`;
  const arr = (x1, y1, x2, y2, cls = "route") => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="${cls}" marker-end="url(#ah)"/>`;
  let g = `<svg viewBox="0 0 100 50" class="stack" role="img" aria-label="Schematic of the order played: the courtyard is met twice, and the back alleys ring a block back to their start"><defs><marker id="ah" viewBox="0 0 4 4" refX="3" refY="2" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0L4 2L0 4z" class="ahd"/></marker></defs>`;
  g += box(1, 42, 14, "1 street", "I1 informant") + arr(15.4, 45.2, 18.6, 45.2) + box(19, 42, 18, "2 restaurant", "F1 waves · F2");
  g += arr(28, 41.6, 28, 34.8) + box(19, 28, 22, "3 courtyard", "F3 west · F8 north", "end");
  g += arr(41.4, 31.2, 47.6, 31.2) + box(48, 28, 15, "4 storage", "F4 · stair up");
  g += arr(55.5, 27.6, 55.5, 20.8) + box(44, 14, 26, "5 upstairs · roof · plank", "F5 · F6 · F7");
  g += arr(43.6, 17.4, 35, 27.6);
  g += arr(21, 27.6, 12, 20.8) + box(1, 14, 20, "6 workshop", "F9 · F10 burn yard");
  g += arr(9, 13.6, 9, 7.8) + box(1, 1, 21, "7 back alleys", "F11–F14 · a ring", "end");
  g += arr(22.4, 4.2, 25.6, 4.2) + box(26, 1, 17, "8 safe house", "F15 · F16");
  g += arr(43.4, 4.2, 46.6, 4.2) + box(47, 1, 30, "9 print shop", "F17 · F18 · I7 · I9 · out", "fl");
  g += `<text x="74" y="30" class="t-sbs">filled = met twice</text><text x="74" y="32.2" class="t-sbs">gates chained the first time:</text><text x="74" y="34.4" class="t-sbs">F8's and F14's waves open them</text>`;
  return g + "</svg>";
})();

const sectionRows = SECTIONS.map(S => {
  const ids = list => list.filter(x => x.sec === S.id).map(x => x.id).join(", ") || "—";
  const outs = CONNECTORS.filter(c => c.from === S.id);
  return `<tr><td>${S.id}</td><td><b>${esc(S.name)}</b><br><span class="small">${esc(S.what)}</span></td><td>${esc(S.ground)}</td><td class="nw">${S.mins[0]}–${S.mins[1]}</td><td class="nw">${S.route_m}</td><td>${ids(FIGHTS)}</td><td>${ids(CHECKPOINTS)}</td><td>${outs.length ? outs.map(o => esc(o.note)).join("<br>") : "the side gate (I9)"}</td><td>${sightRow(S.id)}</td></tr>`;
}).join("");
const fightRows = FIGHTS.map(F => `<tr><td>${F.id}</td><td>${F.sec} · ${esc(F.room)}${F.id === "F8" ? ' <span class="tag back">the loop</span>' : ""}${F.kind === "waves" ? ' <span class="tag">waves</span>' : ""}</td><td>${F.kind === "waves" ? `kill ${F.killTo}: ${F.waves.map(w => w.n).join(" + ")} (${F.max} at once)<br><span class="small">${F.waves.map((w, k) => `${k + 1}: ${esc(w.from)}`).join("<br>")}<br>opens ${esc(F.opens)}</span>` : `${F.start}${F.wave ? ` + ${F.wave} (${F.max} at once)` : ""}`}${F.foes.some(e => e[2] === "c") ? `<br><span class="small">${F.foes.filter(e => e[2] === "c").length} crouched</span>` : ""}</td><td>${esc(F.trigger)}</td><td class="small">${esc(F.note)}</td></tr>`).join("");
const inspRows = INSPECTS.map(i => `<tr><td>${i.id}</td><td>${i.sec}</td><td><b>${esc(i.name)}</b>${i.req ? ' <span class="tag">needed</span>' : ""}</td><td class="small">${i.what ? esc(i.what) + (i.src === "scenario" ? ' <span class="src">scenario</span>' : "") : ""}${i.sug ? `${i.what ? "<br>" : ""}<i>${esc(i.sug)}</i> <span class="src sug">suggestion</span>` : ""}</td><td class="small">${esc(i.does) || "—"}</td></tr>`).join("");

const json = {
  name: "Mission 2: the restaurant / smuggler compound", drafted: "2026-11-13",
  guides: "Gunmen and pickups are rough guides (user, 2026-11-12); the geometry is followed.",
  time_model: { walk_m_s: WALK_MS, s_per_gunman: GUN_S, s_per_inspect: INSP_S, route_m: routeAll, minutes: mins },
  route: ROUTE, order_played: ORDER.map(([id, how]) => (how ? `${id} (${how})` : String(id))),
  units: "m, x east, y south, from the NW corner",
  floors: { "0": "ground", "1": "+3.5" }, storey_m: 3.5,
  sections: SECTIONS.map(({ label, secs, ...S }) => S), connectors: CONNECTORS, streaming: STREAM_NOTE,
  areas: AREAS, openings: OPENINGS, barriers: BARRIERS, stairs: STAIRS, landings: LANDINGS, cover: COVER, roofs: ROOFS,
  arms: ARMS, mass_auto: MASS.map(r => r.map(r2)), fights: FIGHTS, inspects: INSPECTS, checkpoints: CHECKPOINTS, pickups: PICKUPS,
  civilians: CIVILIANS, start: START,
  sightlines_measured: Object.fromEntries(Object.entries(SIGHT).map(([s, v]) => [s, { len: r2(v.len), floor: v.f, a: v.a.map(r2), b: v.b.map(r2) }])),
};
fs.writeFileSync(OUT_JSON, JSON.stringify(json, null, 1));

const legend = `<div class="legend">
  <span><svg viewBox="0 0 2 1.4"><rect width="2" height="1.4" class="blk"/></svg>Buildings (built-up, not entered)</span>
  <span><svg viewBox="0 0 2 1.4"><rect width="2" height="1.4" class="lane"/></svg>Street, lane, yard</span>
  <span><svg viewBox="0 0 2 1.4"><rect width="2" height="1.4" class="room-f"/><path d="M0 .1H2" class="wallx"/></svg>Room (walls drawn)</span>
  <span><svg viewBox="0 0 2 1.4"><path d="M0 .7H2" class="knockl"/></svg>Knocked through</span>
  <span><svg viewBox="0 0 2 1.4"><path d="M0 .7H2" class="gate"/></svg>Gate</span>
  <span><svg viewBox="0 0 2 1.4"><rect width="2" height="1.4" class="cover"/></svg>Low cover (dive past)</span>
  <span><svg viewBox="0 0 2 1.4"><rect width="2" height="1.4" class="tall"/></svg>Full height (blocks sight)</span>
  <span><svg viewBox="-1 -1 2 2"><circle r=".5" class="spawn-d"/></svg>Gunman</span>
  <span><svg viewBox="-1 -1 2 2"><circle r=".5" class="foe-c"/><circle r=".2" class="spawn-d"/></svg>Gunman, crouched</span>
  <span><svg viewBox="-1 -1 2 2"><circle r=".8" class="spawn"/></svg>Wave door</span>
  <span><svg viewBox="-1.2 -1.2 2.6 2.6"><circle r=".62" class="insp req"/><line x1=".44" y1=".44" x2=".95" y2=".95" class="insp-h"/></svg>Inspect (filled = needed)</span>
  <span><svg viewBox="-1 -1 2.4 2"><path d="M0 .7V-.85l1 .35l-1 .35" class="cp"/></svg>Checkpoint</span>
  <span><svg viewBox="-1 -1 2 2"><rect x="-.42" y="-.42" width=".84" height=".84" class="pick" transform="rotate(45)"/></svg>Pickup</span>
  <span><svg viewBox="0 0 3.2 1.4"><path d="M0 .7H3.2" class="conn"/></svg>Section border</span>
  <span><svg viewBox="0 0 2 1.4"><rect width="2" height="1.4" class="stair"/><path d="M.67 0V1.4M1.33 0V1.4" class="tread"/></svg>Stair (arrow points up)</span>
  <span><svg viewBox="0 0 3.2 1.4"><path d="M0 .7H3.2" class="sight"/></svg>Longest sightline, measured</span>
  <span><svg viewBox="0 0 2 1.4"><rect width="2" height="1.4" class="lane"/><rect width="2" height="1.4" fill="url(#roofL)" class="roofo"/></svg>Roofed over</span>
</div>`;

const html = `<title>Restaurant Linear Layout</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Text:wght@500;700;800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap">
<!-- Generated by Tools/LevelGen/layout_linear_restaurant.mjs. Edit the script, not this file. -->
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
.plan { display: block; width: 100%; min-width: 1300px; height: auto; }
.plan-s { display: block; width: 100%; height: auto; }
.pad { padding: 12px 16px 16px; display: grid; gap: 10px; }
.note { font-size: 13px; color: var(--muted); margin: 0; }
.note b { color: var(--ink); font-weight: 600; }
.grid2 { display: grid; grid-template-columns: 1.15fr 1fr; gap: 16px 20px; align-items: start; }
.grid2 figure { margin: 0; display: grid; gap: 4px; }
.sbox { fill: var(--floor); stroke: var(--wall); stroke-width: .25; } .sbox.end { fill: var(--insp); } .sbox.fl { stroke: var(--insp); stroke-width: .45; }
.t-sb { font: 600 1.9px var(--mono); fill: var(--ink); } .t-sbs { font: 400 1.4px var(--body); fill: var(--muted); } .sbox.end + .t-sb, .sbox.end + .t-sb + .t-sbs { fill: var(--sheet); }
.ahd { fill: var(--trig); }
figcaption { font: 600 12px var(--mono); color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }
.legend { display: flex; flex-wrap: wrap; gap: 6px 16px; padding: 10px 16px; border-bottom: 1px solid var(--line); font-size: 12.5px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.legend svg { width: 22px; height: 16px; overflow: visible; }
table { border-collapse: collapse; width: 100%; font-size: 13.5px; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { font: 600 11px var(--mono); text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
td:first-child { font: 500 12.5px var(--mono); white-space: nowrap; }
.small { font-size: 12.5px; color: var(--muted); }
.tag { font: 600 10.5px var(--mono); text-transform: uppercase; color: var(--sheet); background: var(--insp); padding: 1px 5px; border-radius: 3px; }
.tag.back { background: var(--trig); }
td.nw { white-space: nowrap; }
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
.parapet { fill: none; stroke: var(--wall); stroke-width: .14; }
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
.route { fill: none; stroke: var(--trig); stroke-width: .5; stroke-linecap: round; }
.stack { width: 100%; height: auto; display: block; }
.t-sub { font-family: var(--body); fill: var(--muted); }
.t-w { font-family: var(--mono); font-weight: 600; fill: var(--foe); }
.t-p { font-family: var(--body); font-weight: 500; fill: var(--pick); }
.t-a { font-family: var(--mono); font-weight: 600; fill: var(--accent); }
.t-r { font-family: var(--mono); font-weight: 600; fill: var(--trig); }
.t-i { font-family: var(--mono); font-weight: 600; fill: var(--insp); }
.t-cp { font-family: var(--mono); font-weight: 600; fill: var(--cp); }
.t-dim { font-family: var(--mono); font-weight: 500; fill: var(--muted); }
.t-sec { font: 800 1.5px var(--display); fill: var(--trig); letter-spacing: .06px; opacity: .85; }
@media (max-width: 900px) { .lists, .grid2 { grid-template-columns: 1fr; } }
</style>
<svg width="0" height="0" style="position:absolute"><defs><pattern id="roofL" width=".6" height=".6" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><line x1="0" y1="0" x2="0" y2=".6" class="rl"/></pattern></defs></svg>

<div class="wrap">
  <header>
    <div class="eyebrow">ProjectBopis · level layout · linear story level · mission 2 · the restaurant block · draft 2026-11-13 · lengthened the same day: the back alleys and the safe house</div>
    <h1>Restaurant Linear Layout</h1>
    <p class="lede">Mission 2, laid out from your scenario as <b>${SECTIONS.length} streamed sections</b>: a street where the informant gives up the passport maker, the restaurant where he's recognised, then the block behind it. That's <b>storage, safe rooms, a workshop, a safe house and a print shop, stitched together by back lanes and alleys</b> rather than hallways. <b>Two loops.</b> The courtyard where the lanes meet is crossed west to east, then met again from the north after the roofs and the flats (F8). <b>The back alleys</b>, 4.5 m between houses as the arena's, ring a block and come back round to their first corner from the north (F14). <b>The restaurant is a wave encounter:</b> a cutscene gets the customers out, then kill 11 across three waves and the barred kitchen door opens. <b>No civilians in play.</b> <b>The longest sightline in any fight space is ${fightMax.toFixed(1)} m</b>, and the street's is ${streetLen.toFixed(1)} m (both measured with a 1.2 m-wide line). Story beats are <b>inspects</b>: the informant, the document lab, the passport maker. <b>Gunmen and pickups are rough guides; the layout is what gets built.</b></p>
    <div class="stats">
      <div><b>${mins[0]}–${mins[1]} min</b><span>estimated, first play</span></div>
      <div><b>${routeAll} m</b><span>walked</span></div>
      <div><b>${SECTIONS.length}</b><span>sections</span></div>
      <div><b>${FIGHTS.length}</b><span>fights</span></div>
      <div><b>${totalFoes}</b><span>gunmen</span></div>
      <div><b>${INSPECTS.length}</b><span>inspects, ${needed} needed</span></div>
      <div><b>${CHECKPOINTS.length}</b><span>checkpoints</span></div>
      <div><b>${fightMax.toFixed(1)} m</b><span>longest fight sightline</span></div>
    </div>
  </header>

  <div class="sheet">
    <div class="sheet-head"><h2>Plan · ground</h2><span class="meta">metres from the NW corner (x east, y south) · grid 1.5 m, heavy line every 6 m · north up · scrolls sideways</span></div>
    ${legend}
    <div class="scroll">${overview}</div>
    <div class="pad"><p class="note">Upper-floor gunmen (F4's one at the stair head, F5–F7, F16, F18) are drawn on the upper-floor sheet below. Section 5 is mostly upstairs: on this sheet it's only the flats' two ground rooms (north of the courtyard). Buildings along the route are drawn as one built-up mass, 7.5 m deep; only the buildings that are entered get interiors.</p></div>
  </div>

  <div class="sheet">
    <div class="sheet-head"><h2>Upper floor · +3.5 m</h2><span class="meta">storeys 3.5 m (Lvl_01_Slum's) · grey = the floor below · the roof and the plank are open, with a parapet</span></div>
    <div class="pad grid2">
      <figure><figcaption>Over storage, the roof, the plank, the flats (S5) · the safe house (S8) · the print shop's upper floor (S9)</figcaption>${upper}</figure>
      <div class="pad" style="padding:0;align-content:start">
        <figure><figcaption>The order played (schematic)</figcaption>${loopSvg}</figure>
        <p class="note"><b>Section 5 goes over the lane and back down.</b> Up the storage hall's stair into rooms they hold (F5), round the floor and out of the safe room onto the workshop's flat roof (F6). A plank crosses the 3 m lane to a knocked-out window in the flats next door (F7), and their stair comes down by the front door. The lane you'll walk next is under the plank.</p>
        <p class="note"><b>Loop 1, the courtyard:</b> the first time, it's ahead of you as you come out of a roofed lane. The second time you come out of a front door on its north side, they're waiting in the lane you came in by, and the wave comes from the chained gate and the kitchen.</p>
        <p class="note"><b>Loop 2, the back alleys:</b> out of the burn yard's side gate, west along the first alley, south, west under a lean-to, north into a half-court where they make a stand (F13), then east to the safe house's side door. That's the first alley's corner again, seen from the north through a chained gate. Their wave opens it from the side you came in by (F14). Both loops follow your rule of 2026-11-12: back to a place from another entrance, for a new fight.</p>
        <p class="note"><b>The safe house and the print shop:</b> the safe house goes up its front stair, round the floor, and down a wooden back stair into a back room they've knocked through into the print shop's front, with shelving right inside the hole. The presses behind the shut shop front are being pulled apart (F17); upstairs is the document lab (F18, I7). The office door is barred until the lab is clear, and the passport maker is in there (I9). His office opens onto a steel side stair down to a lane and a gate onto the next street: the way out (I10).</p>
      </div>
    </div>
  </div>

  <div class="sheet">
    <div class="sheet-head"><h2>Sections + streaming</h2><span class="meta">one persistent map, sections as tags until streaming is built (as Lvl_01_Slum)</span></div>
    <div class="pad">
      <p class="note"><b>Streaming:</b> ${esc(STREAM_NOTE)} A death reloads only the current section's gameplay from its last checkpoint.</p>
      <div class="tw"><table><tr><th>#</th><th>Section</th><th>Ground</th><th>Min</th><th>Route m</th><th>Fights</th><th>Checkpoints</th><th>Ways out</th><th>Longest sightline</th></tr>${sectionRows}</table></div>
      <p class="note"><b>The minutes are Mission 1's rough model:</b> the route walked at ${WALK_MS} m/s through the doors and up the stairs (${routeAll} m, the courtyard twice), ${GUN_S[0]}–${GUN_S[1]} s a gunman, ${INSP_S[0]}–${INSP_S[1]} s an inspect, first play, no deaths. Your target is 30–45.</p>
    </div>
  </div>

  <div class="sheet">
    <div class="sheet-head"><h2>Fights</h2><span class="meta">${totalFoes} gunmen · never more than 6 in a room fight · F1 a wave encounter · arms ${ARMS}</span></div>
    <div class="pad tw"><table><tr><th>#</th><th>Where</th><th>Gunmen</th><th>Starts on</th><th>Notes</th></tr>${fightRows}</table>
    <p class="note"><b>Rough guides (your call, 2026-11-12):</b> where the gunmen stand, how many and the pickups are starting points. The rooms, doors, stairs, the plank and the lanes are what gets built. <b>Arms are not set for this level:</b> the plan assumes Mission 1's (.45 pistols, revolvers, shotguns, nothing placed, first aid the only pickup).</p></div>
  </div>

  <div class="sheet">
    <div class="sheet-head"><h2>Inspects · story beats</h2><span class="meta"><span class="src">scenario</span> = your text · <span class="src sug">suggestion</span> = mine, yours to replace</span></div>
    <div class="pad tw"><table><tr><th>#</th><th>Sec</th><th>Inspect</th><th>What's there</th><th>Does</th></tr>${inspRows}</table></div>
  </div>

  <div class="lists">
    <section>
      <h2>The generator has to learn</h2>
      <ol>
        <li><b>A restaurant:</b> a dining room with an open shop front, a counter, a kitchen. Check the packs (Philippines_Markets first) for tables, monobloc chairs, a counter, stoves and steel prep tables.</li>
        <li><b>The arena's alleys, laid as a chain:</b> 4.5 m lanes with their dressing rules (wires, laundry, pipes, AC units, meters, posters), a lean-to over part of one, and a half-court pocket with a sari-sari stall.</li>
        <li><b>A walkable flat roof</b> with a parapet and water tanks, over a one-storey building.</li>
        <li><b>A plank bridge</b> across a 3 m lane into a knocked-out window.</li>
        <li><b>An outside steel stair</b> down a building's side (the way out).</li>
        <li><b>A print shop and a document lab:</b> presses, a guillotine, paper stacks, a light table, a laminator. Probably no pack has these, so they may need sourcing.</li>
        <li><b>Shut shop fronts</b> on the far street (shutters down), as the slum's.</li>
        <li>Everything else is Mission 1's: rooms per storey, openings, stairs, lanes, compound walls, sections as tags.</li>
      </ol>
    </section>
    <section>
      <h2>New gameplay it needs</h2>
      <ul>
        <li><b>A talk inspect:</b> the informant is a person, not an object, and money changes hands.</li>
        <li><b>The recognition cutscene</b> (yours, 2026-11-13): he's recognised and the customers and staff are got out in the cutscene. No live civilians, so F1 starts on its end.</li>
        <li><b>Wave encounters</b> (yours, 2026-11-13): waves from set doors, a cap on how many are up at once, and a kill count that fires an event. F1's opens the barred kitchen door. Mission 1's fights have a single top-up wave; this is the general version.</li>
        <li><b>Gunmen busy with something:</b> carrying boxes (F4), burning papers (F10), pulling a press apart (F17), until they see him.</li>
        <li><b>Gates opened by the enemy</b> (F8's and F14's waves unchain them), and <b>a door unbarred by an event</b> (his office, after I7).</li>
        <li><b>Graph streaming:</b> a section that borders four others (the courtyard), and the roof's building loading with the section above it.</li>
        <li><b>A non-hostile NPC</b> for the passport maker, cornered: the interrogation is a mini cutscene (I9).</li>
      </ul>
      <h3 style="margin-top:12px">Layout calls I made</h3>
      <ul>
        <li>F1's waves: 4 at the tables, 4 in at the front off the street, 3 down a stair from the family's rooms; kill 11, at most 5 up.</li>
        <li>The courtyard is the first loop's mid room; the back alleys' first corner is the second's.</li>
        <li>Both loops' ways on are chained gates their wave opens, so the order holds without locking anything behind you.</li>
        <li>The alleys are one section: a ring, every leg 15 m or less, the half-court the widest place.</li>
        <li>The burn yard's side gate is in a wall, with an owner-type jeep just inside: no line from the yard down the first alley.</li>
        <li>The safe house's back room is knocked through into the print shop: the "improvised connection between properties", with the plank.</li>
        <li>The print shop's shop front faces the far street, shut: the business is a front on both sides of the block.</li>
        <li>His office is barred until the lab is clear, so the interrogation comes after the last fight.</li>
        <li>The way out is a side stair and a gate to the next street, not back through the block.</li>
      </ul>
    </section>
    <section class="owned">
      <h2>Open — yours to call</h2>
      <ul>
        <li>The level's name (a story level, so no <code>_Arena</code>). <code>Lvl_02_Restaurant</code> would follow <code>Lvl_01_Slum</code>.</li>
        <li>Time of day. There are customers, so it's open: lunch, or evening?</li>
        <li>What kind of restaurant (a carinderia, a panciteria, something bigger), and who owns it.</li>
        <li>Arms for this level, and whether anything is placed.</li>
        <li>Where the informant is met, and whether he's seen again.</li>
        <li>Who recognises him in the dining room.</li>
        <li>The street before the fight: empty (as now, no live civilians), or ambient people the cutscene clears too?</li>
        <li>Is the evidence burning on a clock (lost if you're slow), or set dressing?</li>
        <li>The passport maker: does he try to run or fight first, or is he simply cornered?</li>
        <li>The end: walk out by the side gate (my suggestion), or end on the interrogation.</li>
        <li>What I2, I3, I4 and I5 show (my suggestions are marked).</li>
        <li>The lead's name (to be decided: none in the build).</li>
      </ul>
    </section>
  </div>
  <p class="note">Build data: <code>Design Document/Linear_Restaurant_Layout.json</code> (areas, openings, stairs, cover, fights, inspects, checkpoints, the route, the auto mass, measured sightlines). Drawing, JSON and measurements all come from <code>Tools/LevelGen/layout_linear_restaurant.mjs</code>.</p>
</div>
`;
fs.writeFileSync(OUT_HTML, html);
console.log("sightlines:", Object.entries(SIGHT).map(([s, v]) => `S${s} ${v.len.toFixed(1)}m f${v.f} (${v.a.map(r2)} -> ${v.b.map(r2)})`).join("\n  "));
console.log("sections:", SECTIONS.map(S => `S${S.id} ${S.route_m}m ${S.mins[0]}-${S.mins[1]}min`).join(", "));
console.log("mass rects:", MASS.length, " foes:", totalFoes, " mins:", mins, " route m:", routeAll, " html bytes:", html.length);

/**
 * Original placeholder art: each species is drawn from a few simple parts (wings, head,
 * tail, legs), seen from below in flight. They hint at a species' build, not its film
 * design (Plan.md §16: no film assets, no copies of official designs).
 *
 * Coordinates are in a 100 x 100 box, symmetric around x = 50. `left` paths are drawn on
 * the left and mirrored to the right; `center` paths are drawn once.
 */

type Part = { left?: string[]; center?: string[] };

export function ellipse(cx: number, cy: number, rx: number, ry: number): string {
  return `M${cx - rx} ${cy}a${rx} ${ry} 0 1 0 ${2 * rx} 0a${rx} ${ry} 0 1 0 ${-2 * rx} 0Z`;
}

const NECK = "M47 34L48 20h4l1 14Z";

const WINGS = {
  bat: { left: ["M46 34C36 16 18 8 2 14c6 6 8 12 8 18 6-2 12 0 16 6 4-2 10 0 14 6 2-2 4-2 6 0Z"] },
  broad: { left: ["M46 32C34 14 14 12 4 22c4 8 10 18 18 24 8-2 16 0 24 2Z"] },
  stubby: { left: ["M42 36c-6-8-16-8-22-2 2 8 10 14 22 14Z"] },
  swept: { left: ["M46 34C34 26 16 26 2 34c12 4 22 8 30 16 6-4 10-6 14-4Z"] },
  double: {
    left: [
      "M46 30C36 14 18 8 4 12c6 6 10 12 12 18 10 0 20 2 30 8Z",
      "M46 44c-10-2-26 2-38 12 10 2 20 2 26 6 4-6 8-10 12-10Z",
    ],
  },
} satisfies Record<string, Part>;

const HEADS = {
  round: { center: [NECK, ellipse(50, 18, 5, 6)] },
  fury: {
    center: ["M47 34l1-12h4l1 12Z", ellipse(50, 20, 7, 6)],
    left: ["M44 18l-8-8 9 13Z", "M44 22l-6-2 7 5Z"],
  },
  furyLight: {
    center: ["M47 34l1-12h4l1 12Z", ellipse(50, 20, 6, 6)],
    left: ["M45 19l-6-6 7 9Z"],
  },
  horned: {
    center: [NECK, ellipse(50, 18, 6, 6)],
    left: ["M45 16c-5-4-7-10-5-14 2 6 5 9 8 12Z"],
  },
  crown: {
    center: [NECK, ellipse(50, 18, 5, 6), "M48 13l2-9 2 9Z"],
    left: ["M46 15l-8-7 9 10Z", "M45 19l-8-2 9 5Z"],
  },
  hornNose: {
    center: [NECK, ellipse(50, 19, 6, 7), "M48 13l2-11 2 11Z"],
    left: ["M45 20l-5-2 5 5Z"],
  },
  pincers: {
    center: [NECK, ellipse(50, 20, 6, 6)],
    left: ["M46 16c-6-4-6-11-1-14-1 5 0 9 4 13Z"],
  },
  bigJaw: { center: [ellipse(50, 26, 9, 8)] },
  tusks: { center: [NECK, ellipse(50, 19, 6, 6)], left: ["M46 14l-2-8 4 7Z"] },
  twin: { left: ["M45 36c-2-8-5-16-9-24l6-2c2 8 5 15 8 22Z", ellipse(38, 10, 5.5, 6)] },
} satisfies Record<string, Part>;

const THIN_TAIL = "M47 58q2 20 3 38 1-18 3-38Z";

const TAILS = {
  thin: { center: [THIN_TAIL] },
  fins: { center: [THIN_TAIL], left: ["M50 84l-10 6 10 2Z", "M50 70l-6 2 6 3Z"] },
  finsLight: { center: [THIN_TAIL], left: ["M50 84l-9 7 9 1Z"] },
  club: { center: ["M46 58q2 12 2 20h4q0-8 2-20Z", ellipse(50, 82, 7, 6)] },
  spiked: {
    center: [THIN_TAIL],
    left: ["M49 68l-8-2 8 7Z", "M49 78h-7l7 5Z", "M50 88l-6 2 6 3Z"],
  },
  barb: { center: [THIN_TAIL, "M44 86l6 13 6-13-6 4Z"] },
  twin: { left: ["M47 58q-3 18-9 36 8-18 12-34Z"] },
  short: { center: ["M47 58q3 14 3 22 0-8 3-22Z"] },
} satisfies Record<string, Part>;

const LEGS = {
  0: {},
  4: { left: ["M44 42l-10 4 2 3 9-3Z", "M45 56l-9 6 2 3 8-5Z"] },
  6: { left: ["M44 42l-10 4 2 3 9-3Z", "M44 49l-11 4 2 3 10-4Z", "M45 56l-9 6 2 3 8-5Z"] },
} satisfies Record<number, Part>;

type Build = {
  wings: keyof typeof WINGS;
  head: keyof typeof HEADS;
  tail: keyof typeof TAILS;
  legs: keyof typeof LEGS;
  body: [rx: number, ry: number];
};

const GENERIC: Build = { wings: "bat", head: "round", tail: "thin", legs: 0, body: [7, 15] };

/** The matchable species (data/game/species_profiles.yaml). Others use the generic build. */
export const BUILDS: Record<string, Build> = {
  night_fury: { wings: "swept", head: "fury", tail: "fins", legs: 0, body: [6, 15] },
  light_fury: { wings: "swept", head: "furyLight", tail: "finsLight", legs: 0, body: [5.5, 15] },
  stormcutter: { wings: "double", head: "horned", tail: "thin", legs: 0, body: [7, 16] },
  deathgripper: { wings: "bat", head: "pincers", tail: "barb", legs: 6, body: [7, 14] },
  rumblehorn: { wings: "broad", head: "hornNose", tail: "thin", legs: 4, body: [10, 16] },
  crimson_goregutter: { wings: "broad", head: "horned", tail: "thin", legs: 4, body: [9, 17] },
  snafflefang: { wings: "stubby", head: "tusks", tail: "short", legs: 4, body: [8, 14] },
  hobgobbler: { wings: "stubby", head: "bigJaw", tail: "short", legs: 4, body: [11, 13] },
  deadly_nadder: { wings: "bat", head: "crown", tail: "spiked", legs: 0, body: [7, 15] },
  gronckle: { wings: "stubby", head: "bigJaw", tail: "club", legs: 4, body: [12, 15] },
  hideous_zippleback: { wings: "bat", head: "twin", tail: "twin", legs: 0, body: [8, 14] },
  monstrous_nightmare: { wings: "bat", head: "horned", tail: "thin", legs: 0, body: [7, 17] },
  terrible_terror: { wings: "bat", head: "round", tail: "thin", legs: 0, body: [6, 13] },
  hotburple: { wings: "stubby", head: "bigJaw", tail: "short", legs: 4, body: [14, 16] },
  scuttleclaw: { wings: "bat", head: "horned", tail: "spiked", legs: 4, body: [7, 14] },
};

/** All the paths for a species, split into mirrored (`left`) and single (`center`) ones. */
export function shapeOf(speciesId: string | null): { left: string[]; center: string[] } {
  const build = (speciesId && BUILDS[speciesId]) || GENERIC;
  const parts: Part[] = [
    WINGS[build.wings],
    LEGS[build.legs],
    { center: [ellipse(50, 46, ...build.body)] },
    HEADS[build.head],
    TAILS[build.tail],
  ];
  return {
    left: parts.flatMap((p) => p.left ?? []),
    center: parts.flatMap((p) => p.center ?? []),
  };
}

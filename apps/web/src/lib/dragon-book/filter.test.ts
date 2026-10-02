import { describe, expect, it } from "vitest";

import { classesOf, createSearch, DEFAULT_FILTERS, type Filters, visibleCards } from "./filter";
import type { DragonCard } from "./types";

function card(overrides: Partial<DragonCard> & Pick<DragonCard, "id" | "name">): DragonCard {
  return {
    kind: "species",
    speciesName: null,
    speciesId: overrides.id,
    dragonClass: null,
    size: null,
    appearances: [],
    confidence: "high",
    ...overrides,
  };
}

const CARDS: DragonCard[] = [
  card({
    id: "night_fury",
    name: "Night Fury",
    dragonClass: "Strike",
    appearances: [
      { movie: "httyd1", type: "on_screen" },
      { movie: "httyd2", type: "on_screen" },
    ],
  }),
  card({
    id: "deadly_nadder",
    name: "Deadly Nadder",
    dragonClass: "Tracker",
    appearances: [{ movie: "httyd1", type: "on_screen" }],
  }),
  card({
    id: "thunderdrum",
    name: "Thunderdrum",
    dragonClass: "Tidal",
    appearances: [
      { movie: "httyd1", type: "mentioned" },
      { movie: "httyd2", type: "background" },
    ],
  }),
  card({
    id: "toothless",
    name: "Toothless",
    kind: "individual",
    speciesName: "Night Fury",
    speciesId: "night_fury",
    dragonClass: "Strike",
    appearances: [{ movie: "httyd1", type: "featured" }],
  }),
];

const search = createSearch(CARDS);
const ids = (filters: Partial<Filters>) =>
  visibleCards(CARDS, { ...DEFAULT_FILTERS, ...filters }, search).map((c) => c.id);

describe("visibleCards", () => {
  it("lists everything by name with no filters", () => {
    expect(ids({})).toEqual(["deadly_nadder", "night_fury", "thunderdrum", "toothless"]);
  });

  it("filters by film and kind", () => {
    expect(ids({ movie: "httyd2" })).toEqual(["night_fury", "thunderdrum"]);
    expect(ids({ kind: "individual" })).toEqual(["toothless"]);
  });

  it("applies film and appearance type to the same appearance", () => {
    // Thunderdrum is mentioned in HTTYD 1 and in the background of HTTYD 2.
    expect(ids({ movie: "httyd2", appearanceType: "background" })).toEqual(["thunderdrum"]);
    expect(ids({ movie: "httyd1", appearanceType: "background" })).toEqual([]);
    expect(ids({ appearanceType: "mentioned" })).toEqual(["thunderdrum"]);
  });

  it("combines every filter", () => {
    expect(ids({ movie: "httyd1", kind: "species", dragonClass: "Strike" })).toEqual([
      "night_fury",
    ]);
  });

  it("ignores the class filter when franchise facts are hidden", () => {
    expect(ids({ dragonClass: "Tidal", includeFranchise: false })).toHaveLength(CARDS.length);
  });

  it("searches names with typos, best match first, then filters", () => {
    // Letter-wise, "nader" is as close to Thu-nder-drum; the word-aware ranking fixes that.
    expect(ids({ query: "nader" })[0]).toBe("deadly_nadder");
    expect(ids({ query: "nadder" })).toEqual(["deadly_nadder"]);
    expect(ids({ query: "night fury" })[0]).toBe("night_fury");
    // A named dragon is found by its species name too.
    expect(ids({ query: "night fury", kind: "individual" })).toEqual(["toothless"]);
    expect(ids({ query: "zzzz" })).toEqual([]);
  });
});

describe("classesOf", () => {
  it("lists each class once, sorted", () => {
    expect(classesOf(CARDS)).toEqual(["Strike", "Tidal", "Tracker"]);
  });
});

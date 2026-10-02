import { describe, expect, it } from "vitest";

import { type Academy, isDiscovered, isNew, progress } from "./academy";
import type { DragonCard } from "./types";

const card = (id: string, kind: DragonCard["kind"], speciesId = id): DragonCard => ({
  id,
  kind,
  name: id,
  speciesName: null,
  speciesId,
  dragonClass: null,
  size: null,
  appearances: [],
  confidence: "high",
});

const NOW = Date.parse("2026-10-04T12:00:00Z");
const academy: Academy = {
  discovered: new Map([
    ["night_fury", "2026-10-04T08:00:00Z"],
    ["gronckle", "2026-10-01T08:00:00Z"],
  ]),
};

describe("Academy mode", () => {
  it("unlocks named dragons with their species", () => {
    expect(isDiscovered(card("toothless", "individual", "night_fury"), academy)).toBe(true);
    expect(isDiscovered(card("cloudjumper", "individual", "stormcutter"), academy)).toBe(false);
  });

  it("marks discoveries from the last day as new", () => {
    expect(isNew(card("night_fury", "species"), academy, NOW)).toBe(true);
    expect(isNew(card("gronckle", "species"), academy, NOW)).toBe(false);
    expect(isNew(card("stormcutter", "species"), academy, NOW)).toBe(false);
  });

  it("counts species only", () => {
    const cards = [
      card("night_fury", "species"),
      card("toothless", "individual", "night_fury"),
      card("stormcutter", "species"),
    ];
    expect(progress(cards, academy)).toEqual({ found: 1, total: 2 });
  });
});

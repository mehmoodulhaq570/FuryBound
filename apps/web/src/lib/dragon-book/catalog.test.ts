// Checks the real catalog build against what the Dragon Book pages rely on.
import { describe, expect, it } from "vitest";

import { dragons, movies, sources, toCard } from "./catalog";
import { APPEARANCE_TYPES } from "./labels";

describe("catalog build", () => {
  it("has entries for all three films", () => {
    expect(dragons.length).toBeGreaterThan(0);
    expect(movies.map((m) => m.ordinal)).toEqual([1, 2, 3]);
  });

  it("gives every entry its own id, so each gets its own page", () => {
    const ids = dragons.map((d) => d.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const id of ids) expect(id).toMatch(/^[a-z0-9_]+$/);
  });

  it("links every named dragon to a species in the catalog", () => {
    const species = new Set(dragons.filter((d) => d.kind === "species").map((d) => d.id));
    for (const d of dragons) {
      if (d.kind === "individual") expect(species, d.id).toContain(d.species.id);
      else for (const id of d.known_individuals) expect(dragons.map((x) => x.id)).toContain(id);
    }
  });

  it("only refers to known films, sources and appearance types", () => {
    const movieIds = new Set(movies.map((m) => m.movie_id));
    for (const d of dragons) {
      expect(d.appearances.length, `${d.id} has no film`).toBeGreaterThan(0);
      for (const a of d.appearances) {
        expect(movieIds).toContain(a.movie);
        expect(APPEARANCE_TYPES).toContain(a.type);
      }
      for (const id of d.sources) expect(sources.has(id), `${d.id}: source ${id}`).toBe(true);
    }
  });

  it("flags every class as franchise", () => {
    for (const d of dragons) {
      if (d.kind === "species" && d.class) expect(d.class.scope).toBe("franchise");
    }
  });

  it("gives named dragons their species' class on cards", () => {
    const toothless = dragons.find((d) => d.id === "toothless");
    expect(toothless && toCard(toothless).dragonClass).toBe("Strike");
  });
});

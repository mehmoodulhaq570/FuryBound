// Server-side access to the catalog build. Only server components import this, so the full
// catalog never ships to the browser; the list page sends slim `DragonCard`s instead.
import dragonsJson from "@data/dragons.json";
import referencesJson from "@data/references.json";

import type { DragonCard, DragonEntry, Movie, Source, SpeciesEntry } from "./types";

export const dragons = dragonsJson as DragonEntry[];
export const movies = (referencesJson.movies as Movie[]).toSorted((a, b) => a.ordinal - b.ordinal);
export const sources = new Map(
  (referencesJson.sources as Source[]).map((source) => [source.source_id, source]),
);

const byId = new Map(dragons.map((entry) => [entry.id, entry]));

export function getDragon(id: string): DragonEntry | undefined {
  return byId.get(id);
}

export function speciesOf(id: string): SpeciesEntry | undefined {
  const entry = byId.get(id);
  return entry?.kind === "species" ? entry : undefined;
}

export function toCard(entry: DragonEntry): DragonCard {
  // Named dragons take their species' class and size.
  const species = entry.kind === "species" ? entry : speciesOf(entry.species.id);
  return {
    id: entry.id,
    kind: entry.kind,
    name: entry.name,
    speciesName: entry.kind === "individual" ? entry.species.name : null,
    speciesId: entry.kind === "individual" ? entry.species.id : entry.id,
    dragonClass: species?.class?.value ?? null,
    size: species?.size ?? null,
    appearances: entry.appearances.map(({ movie, type }) => ({ movie, type })),
    confidence: entry.confidence,
  };
}

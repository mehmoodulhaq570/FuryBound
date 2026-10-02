import type { DragonCard } from "./types";

/**
 * Academy mode (Plan §9.1): a signed-in player's view of the Dragon Book, where dragons they
 * haven't met are hidden. Discoveries are per species; a named dragon follows its species.
 */
export type Academy = {
  /** Species id → when it was discovered (ISO date). */
  discovered: ReadonlyMap<string, string>;
};

const NEW_FOR_MS = 24 * 60 * 60 * 1000;

export function isDiscovered(card: DragonCard, academy: Academy): boolean {
  return academy.discovered.has(card.speciesId);
}

/** Discovered in the last day: shows a "new" badge. */
export function isNew(card: DragonCard, academy: Academy, now: number = Date.now()): boolean {
  const at = academy.discovered.get(card.speciesId);
  return at !== undefined && now - Date.parse(at) < NEW_FOR_MS;
}

/** How many of the book's species the player has met. */
export function progress(cards: DragonCard[], academy: Academy): { found: number; total: number } {
  const species = cards.filter((c) => c.kind === "species");
  return { found: species.filter((c) => isDiscovered(c, academy)).length, total: species.length };
}

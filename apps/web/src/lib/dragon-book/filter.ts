import Fuse from "fuse.js";

import type { AppearanceType, DragonCard } from "./types";

export type Filters = {
  query: string;
  movie: string | null;
  kind: "all" | DragonCard["kind"];
  appearanceType: AppearanceType | null;
  dragonClass: string | null;
  /** Off hides franchise-only facts (dragon classes) and ignores the class filter. */
  includeFranchise: boolean;
};

export const DEFAULT_FILTERS: Filters = {
  query: "",
  movie: null,
  kind: "all",
  appearanceType: null,
  dragonClass: null,
  includeFranchise: true,
};

export function matchesFilters(card: DragonCard, filters: Filters): boolean {
  if (filters.kind !== "all" && card.kind !== filters.kind) return false;
  if (filters.includeFranchise && filters.dragonClass && card.dragonClass !== filters.dragonClass) {
    return false;
  }
  if (filters.movie || filters.appearanceType) {
    // Film and appearance type apply to the same appearance: "background in HTTYD 2".
    return card.appearances.some(
      (a) =>
        (!filters.movie || a.movie === filters.movie) &&
        (!filters.appearanceType || a.type === filters.appearanceType),
    );
  }
  return true;
}

export type Search = (query: string) => DragonCard[];

/**
 * Typo-tolerant name search ("nader" finds Deadly Nadder), best matches first.
 *
 * Fuse scores letters, not words, so on its own "nader" ranks Thu-nder-drum above Nadder.
 * Results are therefore re-ranked: names starting with the query, then names containing it,
 * then names with a word that starts like it, then other fuzzy matches (each group keeps
 * Fuse's order).
 */
export function createSearch(cards: DragonCard[]): Search {
  const fuse = new Fuse(cards, {
    keys: [
      { name: "name", weight: 2 },
      { name: "speciesName", weight: 1 },
    ],
    threshold: 0.3,
    ignoreLocation: true,
  });
  return (query) => {
    const q = query.toLowerCase();
    const tier = (card: DragonCard) => {
      const name = card.name.toLowerCase();
      const names = [name, (card.speciesName ?? "").toLowerCase()];
      if (name.startsWith(q)) return 0;
      if (names.some((n) => n.includes(q))) return 1;
      const words = names.flatMap((n) => n.split(/[\s'&-]+/));
      return words.some((w) => w.startsWith(q.slice(0, 2))) ? 2 : 3;
    };
    return fuse
      .search(query)
      .map((result) => result.item)
      .toSorted((a, b) => tier(a) - tier(b));
  };
}

export function visibleCards(cards: DragonCard[], filters: Filters, search: Search): DragonCard[] {
  const query = filters.query.trim();
  const candidates = query ? search(query) : cards.toSorted((a, b) => a.name.localeCompare(b.name));
  return candidates.filter((card) => matchesFilters(card, filters));
}

export function classesOf(cards: DragonCard[]): string[] {
  return [...new Set(cards.flatMap((card) => (card.dragonClass ? [card.dragonClass] : [])))].sort();
}

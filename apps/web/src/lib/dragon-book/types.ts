// Shapes of data/build/dragons.json and references.json (written by scripts/build_catalog.py).
// catalog.test.ts checks the real files against these.

export type AppearanceType = "featured" | "on_screen" | "background" | "mentioned" | "pictured";
export type Confidence = "high" | "medium" | "low";
export type Scope = "film" | "franchise";
export type Size = "tiny" | "small" | "medium" | "large" | "titan";

export type Appearance = {
  movie: string;
  type: AppearanceType;
  confidence: Confidence;
  evidence: string;
};

type EntryBase = {
  id: string;
  name: string;
  description: string;
  appearances: Appearance[];
  sources: string[];
  confidence: Confidence;
  notes: string;
};

export type SpeciesEntry = EntryBase & {
  kind: "species";
  class: { value: string; scope: Scope } | null;
  size: Size | null;
  diet: string | null;
  known_individuals: string[];
};

export type Rider = {
  movie: string;
  character_id: string;
  character: string;
  relation: "rider" | "owner" | "controller" | "companion";
  confidence: Confidence;
};

export type IndividualEntry = EntryBase & {
  kind: "individual";
  species: { id: string; name: string };
  riders: Rider[];
};

export type DragonEntry = SpeciesEntry | IndividualEntry;

export type Movie = { movie_id: string; title: string; year: number; ordinal: number };

export type Source = {
  source_id: string;
  title: string;
  type: "film" | "official" | "book" | "wiki" | "other";
  url: string | null;
  accessed_on: string | null;
};

/** What the Dragon Book list needs per card: small enough to send to the browser. */
export type DragonCard = {
  id: string;
  kind: DragonEntry["kind"];
  name: string;
  speciesName: string | null;
  /** The species to draw: its own id, or a named dragon's species. */
  speciesId: string;
  dragonClass: string | null;
  size: Size | null;
  appearances: { movie: string; type: AppearanceType }[];
  confidence: Confidence;
};

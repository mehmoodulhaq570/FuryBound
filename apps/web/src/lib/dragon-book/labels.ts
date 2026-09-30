import type { AppearanceType, Confidence, Movie } from "./types";

// Strongest first (Plan.md §2.3).
export const APPEARANCE_TYPES: AppearanceType[] = [
  "featured",
  "on_screen",
  "background",
  "mentioned",
  "pictured",
];

export const APPEARANCE_LABELS: Record<AppearanceType, string> = {
  featured: "Featured",
  on_screen: "On screen",
  background: "Background",
  mentioned: "Mentioned",
  pictured: "Pictured",
};

export const APPEARANCE_HELP: Record<AppearanceType, string> = {
  featured: "A named dragon with a role in the story",
  on_screen: "Clearly seen and identifiable",
  background: "Visible but incidental",
  mentioned: "Named in dialogue but not seen",
  pictured: "Seen only as a drawing, carving or book page",
};

export const CONFIDENCE_HELP: Record<Confidence, string> = {
  high: "Sure",
  medium: "Fairly sure",
  low: "A guess; still to be checked",
};

export function filmLabel(movie: Pick<Movie, "ordinal">): string {
  return `HTTYD ${movie.ordinal}`;
}

// Which species have artwork, written by `pnpm art:build` (scripts/build_species_images.py).
import ids from "./species-images.json";

const WITH_ART = new Set<string>(ids);

/** The species' artwork in /public/dragons, or null if it only has a silhouette. */
export function speciesImage(speciesId: string | null): string | null {
  return speciesId && WITH_ART.has(speciesId) ? `/dragons/${speciesId}.webp` : null;
}

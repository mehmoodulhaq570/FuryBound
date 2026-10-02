import Link from "next/link";

import type { DragonCard as Card, Movie } from "@/lib/dragon-book/types";

import { ClassBadge, ConfidenceMeter, FilmChips } from "./badges";
import { Silhouette } from "./silhouette";

export function DragonCard({
  card,
  movies,
  showClass,
}: {
  card: Card;
  movies: Movie[];
  showClass: boolean;
}) {
  return (
    <Link
      href={`/dragon-book/${card.id}`}
      className="border-line bg-surface hover:border-accent focus-visible:outline-accent group flex h-full flex-col gap-3 rounded-xl border p-4 transition-colors focus-visible:outline-2"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-muted text-xs">
            {card.kind === "species" ? "Species" : `Named dragon · ${card.speciesName}`}
          </p>
          <h2 className="group-hover:text-accent truncate font-semibold">{card.name}</h2>
        </div>
        <Silhouette
          speciesId={card.speciesId}
          size={card.size}
          className="text-muted size-12 shrink-0 opacity-50"
        />
      </div>
      <div className="mt-auto flex flex-wrap items-center justify-between gap-2">
        <FilmChips movies={movies} appearances={card.appearances} />
        <ConfidenceMeter level={card.confidence} />
      </div>
      {showClass && card.dragonClass && (
        <div>
          <ClassBadge value={card.dragonClass} />
        </div>
      )}
    </Link>
  );
}

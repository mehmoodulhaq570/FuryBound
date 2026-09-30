import {
  APPEARANCE_HELP,
  APPEARANCE_LABELS,
  CONFIDENCE_HELP,
  filmLabel,
} from "@/lib/dragon-book/labels";
import type { AppearanceType, Confidence, Movie } from "@/lib/dragon-book/types";

export function Badge({ children, title }: { children: React.ReactNode; title?: string }) {
  return (
    <span
      title={title}
      className="border-line text-muted inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs"
    >
      {children}
    </span>
  );
}

/** A dragon class. Classes come from outside the films, so they always carry the flag. */
export function ClassBadge({ value }: { value: string }) {
  return (
    <Badge title="Dragon classes come from the TV series and games, not the films">
      {value}
      <span className="text-accent font-medium">franchise</span>
    </Badge>
  );
}

const CONFIDENCE_DOTS: Record<Confidence, number> = { high: 3, medium: 2, low: 1 };

export function ConfidenceMeter({ level }: { level: Confidence }) {
  const filled = CONFIDENCE_DOTS[level];
  return (
    <span
      className="text-muted inline-flex items-center gap-1.5 text-xs"
      title={`Confidence: ${level}. ${CONFIDENCE_HELP[level]}`}
    >
      <span className="flex gap-0.5" aria-hidden>
        {[1, 2, 3].map((dot) => (
          <span
            key={dot}
            className={`size-1.5 rounded-full ${dot <= filled ? "bg-accent" : "bg-line"}`}
          />
        ))}
      </span>
      <span>
        <span className="sr-only">Confidence: </span>
        {level}
      </span>
    </span>
  );
}

/** One chip per film: filled when the dragon appears, with the appearance type on hover. */
export function FilmChips({
  movies,
  appearances,
}: {
  movies: Movie[];
  appearances: { movie: string; type: AppearanceType }[];
}) {
  return (
    <ul className="flex gap-1" aria-label="Films">
      {movies.map((movie) => {
        const appearance = appearances.find((a) => a.movie === movie.movie_id);
        return (
          <li
            key={movie.movie_id}
            title={
              appearance
                ? `${movie.title}: ${APPEARANCE_LABELS[appearance.type]} (${APPEARANCE_HELP[appearance.type].toLowerCase()})`
                : `${movie.title}: not in this film`
            }
            className={`rounded px-1.5 py-0.5 font-mono text-[11px] ${
              appearance ? "bg-accent/15 text-foreground" : "text-muted/60 line-through"
            }`}
          >
            <span aria-hidden>{movie.ordinal}</span>
            <span className="sr-only">
              {filmLabel(movie)}
              {appearance ? `: ${APPEARANCE_LABELS[appearance.type]}` : ": not in this film"}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

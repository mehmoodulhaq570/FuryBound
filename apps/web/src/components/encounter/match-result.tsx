import Link from "next/link";

import type { DragonMatch, QuizMatch } from "@/lib/quiz/encounter";

function CompatibilityBar({ dragon }: { dragon: DragonMatch }) {
  return (
    <div
      role="meter"
      aria-label={`Compatibility with ${dragon.name}`}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={dragon.compatibility}
      aria-valuetext={`${dragon.compatibility}%`}
      className="bg-line h-2 overflow-hidden rounded-full"
    >
      <div
        className="bg-accent h-full rounded-full"
        style={{ width: `${dragon.compatibility}%` }}
      />
    </div>
  );
}

/** The plain result: the dragon that chose the player and the two runners-up. */
export function MatchResult({ match }: { match: QuizMatch }) {
  const { top, runners_up } = match;
  return (
    <div className="mx-auto max-w-xl space-y-8">
      <section className="bg-surface border-line space-y-4 rounded-xl border p-6">
        <p className="text-accent text-sm font-medium tracking-widest uppercase">It chose you</p>
        <div className="flex items-baseline justify-between gap-4">
          <h1 className="text-3xl font-semibold tracking-tight">{top.name}</h1>
          <span className="text-2xl font-semibold">{top.compatibility}%</span>
        </div>
        <CompatibilityBar dragon={top} />
        <p className="text-muted text-sm capitalize">{top.rarity}</p>
        <p>{top.summary}</p>
        <p className="text-muted">{top.explanation}</p>
        <Link
          href={`/dragon-book/${top.species_id}`}
          className="text-accent inline-block underline"
        >
          Read about the {top.name} in the Dragon Book
        </Link>
      </section>

      {runners_up.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">Also drawn to you</h2>
          <ul className="space-y-3">
            {runners_up.map((d) => (
              <li key={d.species_id} className="border-line space-y-2 rounded-xl border p-4">
                <div className="flex items-baseline justify-between gap-4">
                  <Link href={`/dragon-book/${d.species_id}`} className="font-medium underline">
                    {d.name}
                  </Link>
                  <span className="text-muted">{d.compatibility}%</span>
                </div>
                <CompatibilityBar dragon={d} />
                <p className="text-muted text-sm">{d.explanation}</p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

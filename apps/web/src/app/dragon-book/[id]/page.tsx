import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ClassBadge, ConfidenceMeter } from "@/components/dragon-book/badges";
import { Silhouette } from "@/components/dragon-book/silhouette";
import { dragons, getDragon, movies, sources, speciesOf } from "@/lib/dragon-book/catalog";
import { APPEARANCE_HELP, APPEARANCE_LABELS, filmLabel } from "@/lib/dragon-book/labels";
import type { DragonEntry } from "@/lib/dragon-book/types";

// Every entry is built ahead of time; anything else is a 404.
export const dynamicParams = false;

export function generateStaticParams() {
  return dragons.map((entry) => ({ id: entry.id }));
}

export async function generateMetadata(props: PageProps<"/dragon-book/[id]">): Promise<Metadata> {
  const entry = getDragon((await props.params).id);
  if (!entry) return {};
  return {
    title: `${entry.name} · Dragon Book · Dragon Academy`,
    description: entry.description || undefined,
  };
}

/**
 * The fan wiki's page for a name. We link instead of showing film images (Plan.md §16).
 * The wiki's "go" search opens the page when the title matches and lists results when not,
 * so a name that differs slightly from the wiki's title still lands somewhere useful.
 */
function wikiUrl(name: string): string {
  const query = new URLSearchParams({ query: name, go: "Go" });
  return `https://howtotrainyourdragon.fandom.com/wiki/Special:Search?${query}`;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function Facts({ entry }: { entry: DragonEntry }) {
  const species = entry.kind === "species" ? entry : speciesOf(entry.species.id);
  const rows: [string, React.ReactNode][] = [];
  if (entry.kind === "individual") {
    rows.push([
      "Species",
      <Link
        key="s"
        href={`/dragon-book/${entry.species.id}`}
        className="text-accent hover:underline"
      >
        {entry.species.name}
      </Link>,
    ]);
  }
  if (species?.class) rows.push(["Class", <ClassBadge key="c" value={species.class.value} />]);
  if (species?.size) rows.push(["Size", species.size]);
  if (entry.kind === "species" && entry.diet) rows.push(["Diet", entry.diet]);
  rows.push(["Confidence", <ConfidenceMeter key="conf" level={entry.confidence} />]);

  return (
    <dl className="border-line bg-surface grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 rounded-xl border p-4 text-sm">
      {rows.map(([label, value]) => (
        <div key={label} className="contents">
          <dt className="text-muted">{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

export default async function DragonPage(props: PageProps<"/dragon-book/[id]">) {
  const entry = getDragon((await props.params).id);
  if (!entry) notFound();

  const species = entry.kind === "species" ? entry : speciesOf(entry.species.id);
  const namedDragons =
    entry.kind === "species" ? entry.known_individuals.flatMap((id) => getDragon(id) ?? []) : [];

  return (
    <article className="space-y-10">
      <div>
        <Link href="/dragon-book" className="text-muted hover:text-foreground text-sm">
          ← Dragon Book
        </Link>
      </div>

      <header className="flex items-start justify-between gap-6">
        <div className="min-w-0 space-y-2">
          <p className="text-accent text-sm font-medium tracking-widest uppercase">
            {entry.kind === "species" ? "Species" : "Named dragon"}
          </p>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">{entry.name}</h1>
          {entry.description ? (
            <p className="max-w-prose text-lg">{entry.description}</p>
          ) : (
            <p className="text-muted max-w-prose">No description yet.</p>
          )}
          <a
            href={wikiUrl(entry.name)}
            target="_blank"
            rel="noreferrer"
            className="text-accent inline-block text-sm underline-offset-2 hover:underline"
          >
            See what it looks like on the fan wiki ↗
          </a>
        </div>
        <Silhouette
          speciesId={entry.kind === "species" ? entry.id : entry.species.id}
          size={species?.size ?? null}
          className="text-muted hidden size-28 shrink-0 opacity-40 sm:block"
        />
      </header>

      <Facts entry={entry} />

      <Section title="In the films">
        <ul className="divide-line border-line divide-y rounded-xl border">
          {movies.map((movie) => {
            const appearance = entry.appearances.find((a) => a.movie === movie.movie_id);
            return (
              <li key={movie.movie_id} className="flex flex-col gap-1 p-4 sm:flex-row sm:gap-6">
                <div className="sm:w-56 sm:shrink-0">
                  <p className="font-medium">{movie.title}</p>
                  <p className="text-muted text-xs">
                    {filmLabel(movie)} · {movie.year}
                  </p>
                </div>
                {appearance ? (
                  <div className="space-y-1 text-sm">
                    <p className="flex flex-wrap items-center gap-3">
                      <span title={APPEARANCE_HELP[appearance.type]} className="font-medium">
                        {APPEARANCE_LABELS[appearance.type]}
                      </span>
                      <ConfidenceMeter level={appearance.confidence} />
                    </p>
                    {appearance.evidence && <p className="text-muted">{appearance.evidence}</p>}
                  </div>
                ) : (
                  <p className="text-muted text-sm">Not in this film</p>
                )}
              </li>
            );
          })}
        </ul>
      </Section>

      {entry.kind === "individual" && entry.riders.length > 0 && (
        <Section title="Riders">
          <ul className="space-y-1 text-sm">
            {entry.riders.map((rider) => {
              const movie = movies.find((m) => m.movie_id === rider.movie);
              return (
                <li key={`${rider.movie}-${rider.character_id}`}>
                  <span className="text-muted font-mono text-xs">
                    {movie ? filmLabel(movie) : rider.movie}
                  </span>{" "}
                  {rider.character} <span className="text-muted">({rider.relation})</span>
                </li>
              );
            })}
          </ul>
        </Section>
      )}

      {namedDragons.length > 0 && (
        <Section title="Named dragons of this species">
          <ul className="flex flex-wrap gap-2">
            {namedDragons.map((dragon) => (
              <li key={dragon.id}>
                <Link
                  href={`/dragon-book/${dragon.id}`}
                  className="border-line hover:border-accent inline-block rounded-full border px-3 py-1 text-sm"
                >
                  {dragon.name}
                </Link>
              </li>
            ))}
          </ul>
        </Section>
      )}

      <Section title="Sources">
        <ol className="text-muted list-decimal space-y-1 pl-5 text-sm">
          {entry.sources.map((id) => {
            const source = sources.get(id);
            if (!source) return <li key={id}>{id}</li>;
            return (
              <li key={id}>
                {source.url ? (
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-foreground hover:text-accent underline-offset-2 hover:underline"
                  >
                    {source.title}
                  </a>
                ) : (
                  <span className="text-foreground">{source.title}</span>
                )}{" "}
                <span className="text-xs">
                  ({source.type}
                  {source.accessed_on ? `, accessed ${source.accessed_on}` : ""})
                </span>
              </li>
            );
          })}
        </ol>
        {entry.notes && <p className="text-muted text-xs">Note: {entry.notes}</p>}
      </Section>
    </article>
  );
}

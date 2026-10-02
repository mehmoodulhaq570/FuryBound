import { DragonSilhouette } from "@/components/art/dragon-silhouette";
import type { Labelled, PlayerDragon } from "@/lib/dragon/my-dragon";

function Bars({ title, items }: { title: string; items: Labelled[] }) {
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">{title}</h2>
      <ul className="space-y-2">
        {items.map((item) => (
          <li key={item.id} className="grid grid-cols-[7rem_1fr_2.5rem] items-center gap-3">
            <span className="text-sm">{item.label}</span>
            <div
              role="meter"
              aria-label={item.label}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={item.value}
              className="bg-line h-2 overflow-hidden rounded-full"
            >
              <div className="bg-accent h-full rounded-full" style={{ width: `${item.value}%` }} />
            </div>
            <span className="text-muted text-right text-sm">{item.value}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function Tags({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div className="space-y-1">
      <h3 className="text-muted text-sm">{title}</h3>
      <ul className="flex flex-wrap gap-2">
        {items.map((item) => (
          <li key={item} className="border-line rounded-full border px-3 py-1 text-sm">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * The dragon card (Plan §9.5): who it is, its mood, needs, trust, stats and personality.
 * `care` is where the care actions go, right under the needs they change.
 */
export function DragonCard({ dragon, care }: { dragon: PlayerDragon; care?: React.ReactNode }) {
  const trust: Labelled = { id: "trust", label: "Trust", value: dragon.trust };
  return (
    <div className="mx-auto max-w-xl space-y-10">
      <section className="bg-surface border-line space-y-4 rounded-xl border p-6">
        <DragonSilhouette
          speciesId={dragon.species_id}
          color={dragon.color_hex ?? undefined}
          outline
          className="text-accent mx-auto w-32"
        />
        <div className="text-center">
          <h1 className="text-3xl font-semibold tracking-tight">{dragon.name}</h1>
          <p className="text-muted">
            {dragon.color_variant ? `${capitalise(dragon.color_variant)} ` : ""}
            {dragon.species_name} · <span className="capitalize">{dragon.rarity}</span>
          </p>
        </div>
        <div className="space-y-1 text-center">
          <p>
            <span className="bg-accent/15 text-accent rounded-full px-3 py-1 text-sm font-medium">
              {dragon.mood.label}
            </span>
          </p>
          <p className="text-muted italic">{dragon.thought}</p>
        </div>
        <dl className="grid grid-cols-3 gap-2 text-center text-sm">
          <div>
            <dt className="text-muted">Compatibility</dt>
            <dd className="font-semibold">
              {dragon.compatibility !== null ? `${dragon.compatibility}%` : "—"}
            </dd>
          </div>
          <div>
            <dt className="text-muted">Level</dt>
            <dd className="font-semibold">{dragon.level}</dd>
          </div>
          <div>
            <dt className="text-muted">Stage</dt>
            <dd className="font-semibold capitalize">{dragon.stage}</dd>
          </div>
        </dl>
        <Tags title="Quirks" items={dragon.quirks.map((q) => q.label)} />
        <Tags title="Likes" items={dragon.likes} />
        <Tags title="Dislikes" items={dragon.dislikes} />
      </section>

      <Bars title="Needs" items={[...dragon.needs, trust]} />
      {care}
      <Bars title="Stats" items={dragon.stats} />
      <Bars title="Personality" items={dragon.personality} />
    </div>
  );
}

function capitalise(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

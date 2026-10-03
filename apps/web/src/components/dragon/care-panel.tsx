"use client";

import type { PlayerDragon } from "@/lib/dragon/my-dragon";

import { useDragonCare } from "./use-dragon-care";

/** Feed, rest or play. The reply (or the dragon's refusal) is shown in the dragon's voice. */
export function CarePanel({
  dragon,
  userId,
  onReaction,
}: {
  dragon: PlayerDragon;
  userId: string;
  onReaction?: (action: "feed" | "rest" | "play") => void;
}) {
  const act = useDragonCare(dragon, userId, onReaction);

  const button =
    "border-line hover:border-accent rounded-lg border px-3 py-2 text-sm transition-colors disabled:opacity-60";

  return (
    <section id="care" className="space-y-4">
      <h2 className="text-lg font-semibold">Look after {dragon.name}</h2>
      <div className="space-y-2">
        <h3 className="text-muted text-sm">Feed</h3>
        <ul className="flex flex-wrap gap-2">
          {dragon.foods.map((food) => (
            <li key={food}>
              <button
                type="button"
                disabled={act.isPending}
                onClick={() => act.mutate({ action: "feed", food })}
                className={`${button} capitalize`}
              >
                {food}
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          disabled={act.isPending}
          onClick={() => act.mutate({ action: "rest" })}
          className={button}
        >
          Rest
        </button>
        <button
          type="button"
          disabled={act.isPending}
          onClick={() => act.mutate({ action: "play" })}
          className={button}
        >
          Play
        </button>
      </div>
      {/* A refusal isn't an error: it's the dragon telling you no. */}
      <p role="status" className="min-h-6 text-sm">
        {act.isSuccess && act.data.message}
        {act.isError && <span className="text-muted">{act.error.message}</span>}
      </p>
    </section>
  );
}

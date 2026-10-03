"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import type { PlayerDragon } from "@/lib/dragon/my-dragon";
import { ProgressPanel } from "@/components/experience/progress-panel";
import { experienceKey, fetchExperience } from "@/lib/experience/api";
import {
  fetchHistory,
  fetchTraining,
  historyKey,
  trainingKey,
  type TrainingOverview,
} from "@/lib/training/api";

import { DragonGate } from "./dragon-gate";
import { StatHistory } from "./stat-history";

export function XpBar({
  level,
  xp,
  xpToNext,
}: {
  level: number;
  xp: number;
  xpToNext: number | null;
}) {
  const share = xpToNext ? Math.min(1, xp / xpToNext) : 1;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="font-medium">Level {level}</span>
        <span className="text-muted">{xpToNext ? `${xp} / ${xpToNext} XP` : "Top level"}</span>
      </div>
      <div
        role="progressbar"
        aria-label="Progress to the next level"
        aria-valuemin={0}
        aria-valuemax={xpToNext ?? 1}
        aria-valuenow={xpToNext ? xp : 1}
        className="bg-line h-2 overflow-hidden rounded-full"
      >
        <div className="bg-accent h-full rounded-full" style={{ width: `${share * 100}%` }} />
      </div>
    </div>
  );
}

export function ActivityList({
  overview,
  dragon,
}: {
  overview: TrainingOverview;
  dragon: PlayerDragon;
}) {
  const energy = dragon.needs.find((n) => n.id === "energy")?.value ?? 0;
  return (
    <ul className="grid gap-3 sm:grid-cols-2">
      {overview.activities.map((a) =>
        a.unlocked ? (
          <li key={a.id}>
            <Link
              href={`/train/${a.id}`}
              className="bg-surface border-line hover:border-accent focus-visible:outline-accent flex h-full flex-col gap-2 rounded-xl border p-4 transition-colors focus-visible:outline-2"
            >
              <span className="flex items-baseline justify-between">
                <span className="font-semibold">{a.label}</span>
                <span className="text-muted text-xs">−{a.energy_cost} energy</span>
              </span>
              <span className="text-muted text-sm">{a.description}</span>
              <span className="text-xs">
                Trains <span className="capitalize">{a.trains.join(" and ")}</span>
                {energy < a.energy_cost && (
                  <span className="text-muted"> · {dragon.name} may be too tired</span>
                )}
              </span>
            </Link>
          </li>
        ) : (
          <li
            key={a.id}
            className="border-line flex h-full flex-col gap-2 rounded-xl border border-dashed p-4"
          >
            <span className="text-muted font-semibold">{a.label} 🔒</span>
            <span className="text-muted text-sm">
              Unlocks at the {a.unlocks_at.label} stage (level {a.unlocks_at_level}).
            </span>
          </li>
        ),
      )}
    </ul>
  );
}

function TrainingPage({ dragon }: { dragon: PlayerDragon }) {
  const experience = useQuery({
    queryKey: experienceKey(dragon.id),
    queryFn: () => fetchExperience(dragon.id),
  });
  const overview = useQuery({
    queryKey: trainingKey(dragon.id),
    queryFn: () => fetchTraining(dragon.id),
  });
  const history = useQuery({
    queryKey: historyKey(dragon.id),
    queryFn: () => fetchHistory(dragon.id),
  });

  return (
    <div className="mx-auto max-w-3xl space-y-10">
      <header className="space-y-4">
        <div>
          <p className="text-accent text-sm font-medium tracking-widest uppercase">Training</p>
          <h1 className="text-3xl font-semibold tracking-tight">Train {dragon.name}</h1>
          <p className="text-muted">
            {dragon.stage_label} · {dragon.mood.label}. Training costs energy and makes{" "}
            {dragon.name} hungry; a happy, rested dragon learns faster.{" "}
            <Link href="/dragon" className="text-accent underline">
              Look after {dragon.name}
            </Link>
          </p>
        </div>
        <XpBar level={dragon.level} xp={dragon.xp} xpToNext={dragon.xp_to_next} />
      </header>

      {experience.data && <ProgressPanel experience={experience.data} />}

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Activities</h2>
        {overview.data ? (
          <ActivityList overview={overview.data} dragon={dragon} />
        ) : (
          <p className="text-muted text-sm">
            {overview.isError ? `Couldn't load activities (${overview.error.message})` : "Loading…"}
          </p>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Progress</h2>
        {history.data ? (
          <StatHistory history={history.data} stats={dragon.stats} />
        ) : (
          <p className="text-muted text-sm">
            {history.isError ? "Couldn't load history" : "Loading…"}
          </p>
        )}
      </section>
    </div>
  );
}

export function TrainHome() {
  return (
    <DragonGate title="Training" path="/train">
      {(dragon) => <TrainingPage dragon={dragon} />}
    </DragonGate>
  );
}

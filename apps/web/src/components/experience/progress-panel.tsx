"use client";

import Link from "next/link";

import type { Experience } from "@/lib/experience/api";

/** Rewards are earned from server-recorded events, including earlier care and training. */
export function ProgressPanel({ experience }: { experience: Experience }) {
  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-xl font-semibold">Your story so far</h2>
        <Link href="/adventure" className="text-accent text-sm underline">
          Explore Misty Cove →
        </Link>
      </div>
      {experience.milestone ? (
        <div className="bg-surface border-line space-y-2 rounded-2xl border p-5">
          <p className="text-accent text-xs font-semibold tracking-widest uppercase">
            Next milestone
          </p>
          <p className="font-semibold">
            Level {experience.milestone.level} · {experience.milestone.label}
          </p>
          <p className="text-muted text-sm">
            {experience.milestone.xp_remaining.toLocaleString()} XP to go. Training and your first
            rescue bring you closer.
          </p>
        </div>
      ) : (
        <p className="text-muted">Master stage reached. Keep exploring together.</p>
      )}
      <div className="grid gap-3 sm:grid-cols-2">
        {experience.achievements.map((badge) => (
          <div
            key={badge.id}
            className={`border-line rounded-2xl border p-4 ${badge.earned ? "bg-accent/10" : "bg-surface"}`}
          >
            <p className="font-semibold">
              {badge.earned ? "✦" : "◇"} {badge.title}
            </p>
            <p className="text-muted mt-1 text-sm">{badge.description}</p>
            <p className="mt-2 text-xs">
              {badge.earned
                ? `Unlocked: ${badge.decoration}`
                : `${badge.progress} / ${badge.target} · unlocks ${badge.decoration}`}
            </p>
            <progress
              className="accent-accent mt-2 h-1.5 w-full"
              aria-label={badge.title}
              value={badge.progress}
              max={badge.target}
            />
          </div>
        ))}
      </div>
      <details className="border-line rounded-2xl border p-5">
        <summary className="cursor-pointer font-semibold">Dragon journal</summary>
        <ol className="mt-4 space-y-3">
          {experience.journal.map((entry) => (
            <li key={entry.id} className="border-line border-l-2 pl-3 text-sm">
              <p>{entry.text}</p>
              <time className="text-muted text-xs" dateTime={entry.at}>
                {new Date(entry.at).toLocaleDateString()}
              </time>
            </li>
          ))}
        </ol>
      </details>
    </section>
  );
}

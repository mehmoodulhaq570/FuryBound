"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { DragonSilhouette } from "@/components/art/dragon-silhouette";
import { TraitBars } from "@/components/quiz/trait-bars";
import type { DragonMatch, QuizAttemptDetail, QuizMatch } from "@/lib/quiz/encounter";

import { RevealStage, type StagePhase } from "./reveal-stage";

type Phase = StagePhase | "landed";

/** How the result appears: moving in, only fading in (reduced motion), or at once (seen). */
type Entrance = "full" | "fade" | "none";

/** How long each part of the sequence lasts (ms). */
export const TIMING = { circling: 2600, peel: 1600 } as const;

function CompatibilityBar({ dragon, entrance }: { dragon: DragonMatch; entrance: Entrance }) {
  const width = `${dragon.compatibility}%`;
  return (
    <div
      role="meter"
      aria-label={`Compatibility with ${dragon.name}`}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={dragon.compatibility}
      aria-valuetext={width}
      className="bg-line h-2 overflow-hidden rounded-full"
    >
      <motion.div
        className="bg-accent h-full rounded-full"
        initial={{ width: entrance === "full" ? "0%" : width }}
        animate={{ width }}
        transition={{ duration: 1.2, ease: "easeOut", delay: 0.3 }}
      />
    </div>
  );
}

function Appear({
  entrance,
  delay,
  className,
  children,
}: {
  entrance: Entrance;
  delay: number;
  className?: string;
  children: React.ReactNode;
}) {
  const initial = entrance === "none" ? false : { opacity: 0, y: entrance === "full" ? 12 : 0 };
  return (
    <motion.div
      className={className}
      initial={initial}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay }}
    >
      {children}
    </motion.div>
  );
}

function Result({
  match,
  traits,
  entrance,
  naming,
}: {
  match: QuizMatch;
  traits: QuizAttemptDetail["traits"];
  entrance: Entrance;
  naming: React.ReactNode;
}) {
  const { top, runners_up } = match;
  return (
    <div className="mx-auto max-w-xl space-y-10">
      <Appear entrance={entrance} delay={0}>
        <section className="bg-surface border-line space-y-4 rounded-xl border p-6">
          <DragonSilhouette speciesId={top.species_id} className="text-accent mx-auto w-28" />
          <p className="text-accent text-center text-sm font-medium tracking-widest uppercase">
            It chose you
          </p>
          <div className="flex items-baseline justify-between gap-4">
            <h1 className="text-3xl font-semibold tracking-tight">{top.name}</h1>
            <span className="text-2xl font-semibold">{top.compatibility}%</span>
          </div>
          <CompatibilityBar dragon={top} entrance={entrance} />
          <p className="text-muted text-sm capitalize">{top.rarity}</p>
          <p>{top.summary}</p>
          <p className="text-muted">{top.explanation}</p>
          <Link
            href={`/dragon-book/${top.species_id}`}
            className="text-accent inline-block underline"
          >
            Read about the {top.name} in the Dragon Book
          </Link>
          {naming}
        </section>
      </Appear>

      <Appear entrance={entrance} delay={1.2} className="space-y-3">
        <h2 className="text-lg font-semibold">How the dragons see you</h2>
        <TraitBars traits={traits} />
      </Appear>

      {runners_up.length > 0 && (
        <Appear entrance={entrance} delay={1.6} className="space-y-3">
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
                <CompatibilityBar dragon={d} entrance={entrance} />
                <p className="text-muted text-sm">{d.explanation}</p>
              </li>
            ))}
          </ul>
        </Appear>
      )}
    </div>
  );
}

/**
 * "The dragon chooses you" (Plan §9.4): three silhouettes circle, two peel away, the chosen
 * one lands. With reduced motion the result just fades in; once seen, it shows at once.
 */
export function Reveal({
  attempt,
  match,
  reduceMotion,
  seen,
  onSeen,
  naming,
}: {
  attempt: QuizAttemptDetail;
  match: QuizMatch;
  reduceMotion: boolean;
  /** The reveal already played for this attempt (e.g. this is a reload). */
  seen: boolean;
  onSeen: () => void;
  /** Where the player names (adopts) the dragon. */
  naming?: React.ReactNode;
}) {
  const [phase, setPhase] = useState<Phase>(reduceMotion || seen ? "landed" : "circling");
  const entrance: Entrance = seen ? "none" : reduceMotion ? "fade" : "full";

  useEffect(() => {
    if (phase === "landed") {
      onSeen();
      return;
    }
    const timer = setTimeout(
      () => setPhase(phase === "circling" ? "peel" : "landed"),
      TIMING[phase],
    );
    return () => clearTimeout(timer);
  }, [phase, onSeen]);

  return (
    <div className="space-y-6">
      <p role="status" className="sr-only">
        {phase === "landed"
          ? `It chose you: ${match.top.name}, ${match.top.compatibility}% compatible.`
          : "Three dragons circle overhead."}
      </p>
      {phase === "landed" ? (
        <Result match={match} traits={attempt.traits} entrance={entrance} naming={naming} />
      ) : (
        <div className="space-y-4 text-center">
          <p className="text-muted">
            {phase === "circling" ? "Three dragons circle overhead…" : "Two of them peel away…"}
          </p>
          <RevealStage
            phase={phase}
            chosen={match.top.species_id}
            others={match.runners_up.map((d) => d.species_id)}
          />
          <button
            type="button"
            onClick={() => setPhase("landed")}
            className="text-muted hover:text-foreground text-sm underline"
          >
            Skip
          </button>
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";

import { accuracyScore } from "@/lib/training/scoring";
import { DragonActor } from "@/components/art/dragon-actor";

import { useTimers, type GameProps } from "./use-timers";

const TARGETS = 10;
const WINDOW_MS = 1200;
const CELLS = 9;

/** Accuracy: a target lights up somewhere on the grid. Hit it before it ducks away. */
export function AccuracyGame({ onFinish, speciesId = "night_fury", color }: GameProps) {
  const [active, setActive] = useState<number | null>(null);
  const [round, setRound] = useState(0);
  const [feedback, setFeedback] = useState("Wait for a target, then tap its centre.");
  const [firing, setFiring] = useState(false);
  const reactions = useRef<(number | null)[]>([]);
  const shownAt = useRef(0);
  const current = useRef(0); // which target is showing, so a late timeout is ignored
  const after = useTimers();

  function record(reaction: number | null) {
    setFeedback(
      reaction === null
        ? "It slipped away. Watch for the next target!"
        : "Bullseye! Your dragon sends a spark across the clearing.",
    );
    if (reaction !== null) {
      setFiring(true);
      after(() => setFiring(false), 350);
    }
    setActive(null);
    reactions.current.push(reaction);
    const next = reactions.current.length;
    setRound(next);
    if (next === TARGETS) {
      onFinish(accuracyScore(reactions.current, WINDOW_MS), {
        hits: reactions.current.filter((r) => r !== null).length,
      });
    } else {
      show(next);
    }
  }

  function show(n: number) {
    after(
      () => {
        current.current = n;
        shownAt.current = performance.now();
        setActive(Math.floor(Math.random() * CELLS));
        after(() => {
          if (current.current === n && reactions.current.length === n) record(null);
        }, WINDOW_MS);
      },
      300 + Math.random() * 500,
    );
  }

  useEffect(() => {
    show(0);
    // Starts the first target once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-6">
      <p className="text-muted text-center text-sm">
        Target {Math.min(round + 1, TARGETS)} of {TARGETS}
      </p>
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-sky-200 to-emerald-900 p-5 pb-24">
        <div className="relative z-10 mx-auto grid max-w-xs grid-cols-3 gap-3">
          {Array.from({ length: CELLS }, (_, i) => (
            <button
              key={i}
              type="button"
              aria-label={active === i ? "Target!" : "Empty"}
              onClick={() => {
                if (active === i) record(performance.now() - shownAt.current);
              }}
              className={`flex aspect-square items-center justify-center rounded-xl border transition-colors ${
                active === i ? "border-accent bg-amber-100" : "bg-surface border-line"
              }`}
            >
              {active === i && (
                <svg viewBox="0 0 100 100" className="size-16" aria-hidden="true">
                  <circle cx="50" cy="50" r="44" fill="#bd643d" />
                  <circle cx="50" cy="50" r="32" fill="#f7e6bb" />
                  <circle cx="50" cy="50" r="20" fill="#bd643d" />
                  <circle cx="50" cy="50" r="8" fill="#f7e6bb" />
                </svg>
              )}
            </button>
          ))}
        </div>
        <div className="absolute bottom-0 left-4 w-36">
          <DragonActor speciesId={speciesId} color={color} pose={firing ? "happy" : "idle"} />
        </div>
        {firing && (
          <div
            className="pointer-events-none absolute right-8 bottom-14 left-28 h-3 -rotate-12 rounded-full bg-gradient-to-r from-amber-100 via-orange-300 to-transparent shadow-lg"
            aria-hidden="true"
          />
        )}
      </div>
      <p role="status" className="text-center text-sm">
        {feedback}
      </p>
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";

import { accuracyScore } from "@/lib/training/scoring";

import { useTimers, type GameProps } from "./use-timers";

const TARGETS = 10;
const WINDOW_MS = 1200;
const CELLS = 9;

/** Accuracy: a target lights up somewhere on the grid. Hit it before it ducks away. */
export function AccuracyGame({ onFinish }: GameProps) {
  const [active, setActive] = useState<number | null>(null);
  const [round, setRound] = useState(0);
  const reactions = useRef<(number | null)[]>([]);
  const shownAt = useRef(0);
  const current = useRef(0); // which target is showing, so a late timeout is ignored
  const after = useTimers();

  function record(reaction: number | null) {
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
      <div className="mx-auto grid max-w-xs grid-cols-3 gap-3">
        {Array.from({ length: CELLS }, (_, i) => (
          <button
            key={i}
            type="button"
            aria-label={active === i ? "Target!" : "Empty"}
            onClick={() => {
              if (active === i) record(performance.now() - shownAt.current);
            }}
            className={`aspect-square rounded-xl border transition-colors ${
              active === i ? "bg-accent border-accent" : "bg-surface border-line"
            }`}
          />
        ))}
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";

import { memoryScore } from "@/lib/training/scoring";

import { gameButton, useTimers, type GameProps } from "./use-timers";

export const SIGNS = [
  { id: "fish", emoji: "🐟" },
  { id: "rock", emoji: "🪨" },
  { id: "fire", emoji: "🔥" },
  { id: "egg", emoji: "🥚" },
  { id: "leaf", emoji: "🌿" },
] as const;

const SHORTEST = 3;
const LONGEST = 8;
const SHOW_MS = 700;
const GAP_MS = 250;

const randomSequence = (length: number) =>
  Array.from({ length }, () => Math.floor(Math.random() * SIGNS.length));

/** Memory: watch the signs, then repeat them in order. Each success adds one more. */
export function MemoryGame({ onFinish }: GameProps) {
  const [sequence, setSequence] = useState(() => randomSequence(SHORTEST));
  const [showing, setShowing] = useState<number | null>(null); // index being shown
  const [watching, setWatching] = useState(true);
  const [entered, setEntered] = useState<number[]>([]);
  const after = useTimers();

  // Play the sequence; `watching` is set to true wherever a new sequence starts.
  useEffect(() => {
    sequence.forEach((_, i) => {
      after(() => setShowing(i), i * (SHOW_MS + GAP_MS) + 400);
      after(() => setShowing(null), i * (SHOW_MS + GAP_MS) + 400 + SHOW_MS);
    });
    after(() => setWatching(false), sequence.length * (SHOW_MS + GAP_MS) + 400);
  }, [sequence, after]);

  function finish(longest: number) {
    onFinish(memoryScore(longest, SHORTEST, LONGEST), { longest });
  }

  function press(sign: number) {
    if (watching) return;
    const next = [...entered, sign];
    if (sequence[next.length - 1] !== sign) return finish(sequence.length - 1);
    if (next.length < sequence.length) return setEntered(next);
    if (sequence.length === LONGEST) return finish(LONGEST);
    setEntered([]);
    setWatching(true);
    setSequence(randomSequence(sequence.length + 1));
  }

  const shown = showing === null ? null : SIGNS[sequence[showing]];
  return (
    <div className="space-y-6 text-center">
      <p className="text-muted text-sm">
        {watching
          ? `Watch: ${sequence.length} signs`
          : `Your turn: ${entered.length} of ${sequence.length}`}
      </p>
      <div className="flex h-28 items-center justify-center text-6xl" role="status">
        {shown ? <span aria-label={shown.id}>{shown.emoji}</span> : watching ? "·" : "?"}
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        {SIGNS.map((sign, i) => (
          <button
            key={sign.id}
            type="button"
            aria-label={sign.id}
            disabled={watching}
            onClick={() => press(i)}
            className={`${gameButton} text-3xl`}
          >
            {sign.emoji}
          </button>
        ))}
      </div>
    </div>
  );
}

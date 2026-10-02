"use client";

import { useEffect, useRef, useState } from "react";

import { obedienceScore } from "@/lib/training/scoring";

import { gameButton, useTimers, type GameProps } from "./use-timers";

export const COMMANDS = ["Fly", "Land", "Turn", "Follow", "Stop"] as const;
const ROUNDS = 8;
const LIMIT_MS = 2000;

/** Obedience: when a command appears, give the matching signal as fast as you can. */
export function ObedienceGame({ onFinish }: GameProps) {
  const [command, setCommand] = useState<number | null>(null);
  const rounds = useRef<{ correct: boolean; ms: number }[]>([]);
  const [round, setRound] = useState(0);
  const shownAt = useRef(0);
  const after = useTimers();

  function answer(correct: boolean, ms: number) {
    setCommand(null);
    rounds.current.push({ correct, ms });
    const n = rounds.current.length;
    setRound(n);
    if (n === ROUNDS) {
      onFinish(obedienceScore(rounds.current, LIMIT_MS), {
        correct: rounds.current.filter((r) => r.correct).length,
      });
    } else {
      next(n);
    }
  }

  function next(n: number) {
    after(
      () => {
        shownAt.current = performance.now();
        setCommand(Math.floor(Math.random() * COMMANDS.length));
        after(() => {
          if (rounds.current.length === n) answer(false, LIMIT_MS);
        }, LIMIT_MS);
      },
      500 + Math.random() * 800,
    );
  }

  useEffect(() => {
    next(0);
    // Starts the first command once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-6 text-center">
      <p className="text-muted text-sm">
        Command {Math.min(round + 1, ROUNDS)} of {ROUNDS}
      </p>
      <p className="h-16 text-4xl font-semibold" role="status">
        {command === null ? (
          <span className="text-muted text-xl">Ready…</span>
        ) : (
          `${COMMANDS[command]}!`
        )}
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        {COMMANDS.map((c, i) => (
          <button
            key={c}
            type="button"
            onClick={() => {
              if (command !== null) answer(i === command, performance.now() - shownAt.current);
            }}
            className={gameButton}
          >
            {c}
          </button>
        ))}
      </div>
    </div>
  );
}

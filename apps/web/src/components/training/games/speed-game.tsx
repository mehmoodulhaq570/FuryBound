"use client";

import { useEffect, useRef, useState } from "react";

import { rhythmScore } from "@/lib/training/scoring";

import { gameButton, useFrames, useTimers, type GameProps } from "./use-timers";

const BEATS = 12;
const INTERVAL_MS = 600;
const LEAD_MS = 1800; // a count-in before the first beat
const BEAT_TIMES = Array.from({ length: BEATS }, (_, i) => LEAD_MS + i * INTERVAL_MS);

/** Speed: tap "Flap" on every wingbeat. The circle swells on the beat. */
export function SpeedGame({ onFinish }: GameProps) {
  const start = useRef(0);
  const taps = useRef<number[]>([]);
  const [pulse, setPulse] = useState(0);
  const [beat, setBeat] = useState(0);
  const after = useTimers();

  useEffect(() => {
    start.current = performance.now();
    after(
      () => {
        const score = rhythmScore(BEAT_TIMES, taps.current);
        onFinish(score, { taps: taps.current.length });
      },
      BEAT_TIMES[BEATS - 1] + INTERVAL_MS,
    );
    // Runs once: the beat schedule is fixed when the game starts.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useFrames((ms) => {
    const nearest = Math.min(...BEAT_TIMES.map((b) => Math.abs(ms - b)));
    setPulse(Math.max(0, 1 - nearest / 200));
    setBeat(BEAT_TIMES.filter((b) => b <= ms).length);
  });

  return (
    <div className="space-y-6 text-center">
      <p className="text-muted text-sm">
        {beat === 0 ? "Get ready…" : `Beat ${Math.min(beat, BEATS)} of ${BEATS}`}
      </p>
      <div className="flex h-40 items-center justify-center" aria-hidden="true">
        <div
          className="bg-accent rounded-full"
          style={{ width: 64 + pulse * 48, height: 64 + pulse * 48, opacity: 0.4 + pulse * 0.6 }}
        />
      </div>
      <button
        type="button"
        onClick={() => taps.current.push(performance.now() - start.current)}
        className={`${gameButton} w-full`}
        autoFocus
      >
        Flap
      </button>
    </div>
  );
}

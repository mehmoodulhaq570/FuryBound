"use client";

import { useRef, useState } from "react";

import { flightScore, markerPosition } from "@/lib/training/scoring";

import { gameButton, useFrames, type GameProps } from "./use-timers";

const ROUNDS = 6;
const PERIOD_MS = 1600;
const ZONE = 0.2; // width of the target zone, as a share of the bar

const newZone = () => 0.2 + Math.random() * 0.6;

/** Flight: press "Bank!" while the marker is inside the glowing zone. */
export function FlightGame({ onFinish }: GameProps) {
  const [position, setPosition] = useState(0);
  const [zone, setZone] = useState(newZone);
  const [offsets, setOffsets] = useState<number[]>([]);
  const elapsed = useRef(0);
  const done = offsets.length >= ROUNDS;

  useFrames((ms) => {
    elapsed.current = ms;
    setPosition(markerPosition(ms, PERIOD_MS));
  }, !done);

  function bank() {
    if (done) return;
    const next = [...offsets, markerPosition(elapsed.current, PERIOD_MS) - zone];
    setOffsets(next);
    setZone(newZone());
    if (next.length === ROUNDS) onFinish(flightScore(next), { offsets: next });
  }

  return (
    <div className="space-y-6">
      <p className="text-muted text-center text-sm">
        Turn {Math.min(offsets.length + 1, ROUNDS)} of {ROUNDS}
      </p>
      <div className="bg-line relative h-10 overflow-hidden rounded-full" aria-hidden="true">
        <div
          className="bg-accent/30 absolute inset-y-0"
          style={{ left: `${(zone - ZONE / 2) * 100}%`, width: `${ZONE * 100}%` }}
        />
        <div
          className="bg-foreground absolute inset-y-0 w-1.5 -translate-x-1/2 rounded-full"
          style={{ left: `${position * 100}%` }}
        />
      </div>
      <button
        type="button"
        onClick={bank}
        disabled={done}
        className={`${gameButton} w-full`}
        autoFocus
      >
        Bank!
      </button>
    </div>
  );
}

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { DragonSilhouette } from "@/components/art/dragon-silhouette";
import {
  courseScore,
  FLIGHT_GATES,
  FLIGHT_LEAD_IN_MS,
  GATE_HALF_GAP,
  GATE_INTERVAL_MS,
  steer,
} from "@/lib/training/flight-course";

import styles from "./flight-game.module.css";
import { gameButton, useFrames, type GameProps } from "./use-timers";

/** A six-gate flight. Missing a gate costs points, never ends the run early. */
export function FlightGame({ onFinish, speciesId = "night_fury", color, agility = 30 }: GameProps) {
  const [frame, setFrame] = useState({ elapsed: 0, height: 0.5, gates: 0 });
  const [paused, setPaused] = useState(false);
  const [feedback, setFeedback] = useState("Follow the glowing openings. First gate ahead!");
  const target = useRef(0.5);
  const actual = useRef(0.5);
  const elapsed = useRef(0);
  const previous = useRef<number | null>(null);
  const offsets = useRef<number[]>([]);
  const finished = useRef(false);
  const pausedRef = useRef(false);
  const latestFinish = useRef(onFinish);
  useEffect(() => {
    latestFinish.current = onFinish;
  }, [onFinish]);

  const move = useCallback((direction: number) => {
    if (!pausedRef.current && !finished.current) target.current = steer(target.current, direction);
  }, []);
  const pause = useCallback((value: boolean) => {
    pausedRef.current = value;
    previous.current = null;
    setPaused(value);
  }, []);

  useEffect(() => {
    const key = (event: KeyboardEvent) => {
      if (event.key === " " && event.target instanceof HTMLButtonElement) return;
      if (["ArrowUp", "ArrowDown", " ", "Escape"].includes(event.key)) {
        event.preventDefault();
        if (event.key === "Escape") pause(!pausedRef.current);
        else move(event.key === "ArrowDown" ? 1 : -1);
      }
    };
    const hidden = () => {
      if (document.hidden) pause(true);
    };
    window.addEventListener("keydown", key);
    document.addEventListener("visibilitychange", hidden);
    return () => {
      window.removeEventListener("keydown", key);
      document.removeEventListener("visibilitychange", hidden);
    };
  }, [move, pause]);

  useFrames((ms) => {
    if (pausedRef.current || finished.current) {
      previous.current = null;
      return;
    }
    const delta = previous.current === null ? 0 : Math.min(50, ms - previous.current);
    previous.current = ms;
    elapsed.current += delta;
    const responsiveness = 3 + Math.max(0, Math.min(100, agility)) / 35;
    actual.current +=
      (target.current - actual.current) * Math.min(1, (delta / 1000) * responsiveness);
    const gateIndex = offsets.current.length;
    const crossing = FLIGHT_LEAD_IN_MS + (gateIndex + 1) * GATE_INTERVAL_MS;
    if (gateIndex < FLIGHT_GATES.length && elapsed.current >= crossing) {
      const offset = actual.current - FLIGHT_GATES[gateIndex];
      offsets.current.push(offset);
      setFeedback(
        Math.abs(offset) <= GATE_HALF_GAP
          ? Math.abs(offset) < 0.06
            ? "Perfect line! Your dragon chirps triumphantly."
            : "Through! Keep those wings steady."
          : "Clipped the sea stack. Shake it off — the next gate is yours.",
      );
      if (offsets.current.length === FLIGHT_GATES.length) {
        finished.current = true;
        latestFinish.current(
          courseScore(offsets.current),
          {
            offsets: offsets.current,
            course: "misty_cove_v1",
            gates: FLIGHT_GATES.length,
          },
          elapsed.current,
        );
      }
    }
    setFrame({ elapsed: elapsed.current, height: actual.current, gates: offsets.current.length });
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between text-sm">
        <span>Gate {Math.min(frame.gates + 1, 6)} of 6 · Misty Cove</span>
        <button type="button" onClick={() => pause(!paused)} className="text-accent underline">
          {paused ? "Resume" : "Pause"}
        </button>
      </div>
      <div
        className={styles.sky}
        role="group"
        aria-label={`Your dragon flies through Misty Cove. ${frame.gates} of 6 gates passed.`}
      >
        <div className={styles.clouds} />
        <div className={styles.horizon} />
        <div className={styles.ocean} />
        {FLIGHT_GATES.map((height, i) => {
          const crossing = FLIGHT_LEAD_IN_MS + (i + 1) * GATE_INTERVAL_MS;
          const x = 22 + ((crossing - frame.elapsed) / GATE_INTERVAL_MS) * 64;
          if (x < -10 || x > 110) return null;
          return (
            <div key={i} className={styles.gate} style={{ left: `${x}%` }}>
              <div
                className={styles.rockTop}
                style={{ height: `${(height - GATE_HALF_GAP) * 100}%` }}
              />
              <div
                className={styles.opening}
                style={{
                  top: `${(height - GATE_HALF_GAP) * 100}%`,
                  height: `${GATE_HALF_GAP * 200}%`,
                }}
              />
              <div
                className={styles.rockBottom}
                style={{ top: `${(height + GATE_HALF_GAP) * 100}%` }}
              />
            </div>
          );
        })}
        <div className={styles.dragon} style={{ top: `${frame.height * 100}%` }}>
          <DragonSilhouette
            speciesId={speciesId}
            color={color ?? "#243649"}
            className="size-20 drop-shadow-lg sm:size-24"
          />
        </div>
        {paused && (
          <div className={styles.pause}>
            <button type="button" onClick={() => pause(false)} className={gameButton}>
              Resume flight
            </button>
          </div>
        )}
      </div>
      <p role="status" className="min-h-12 text-center text-sm">
        {feedback}
      </p>
      <div className="grid grid-cols-2 gap-3">
        <button type="button" className={gameButton} onClick={() => move(-1)} disabled={paused}>
          ↑ Climb
        </button>
        <button type="button" className={gameButton} onClick={() => move(1)} disabled={paused}>
          ↓ Dive
        </button>
      </div>
      <p className="text-muted text-center text-xs">
        Arrow keys to steer · Space to climb · Esc to pause. On touch screens, tap Climb and Dive.
      </p>
    </div>
  );
}

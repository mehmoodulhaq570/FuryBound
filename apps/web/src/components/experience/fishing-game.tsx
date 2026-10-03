"use client";

import { useRef, useState } from "react";

import { DragonActor } from "@/components/art/dragon-actor";
import { useDragonCare } from "@/components/dragon/use-dragon-care";
import { useFrames } from "@/components/training/games/use-timers";
import type { PlayerDragon } from "@/lib/dragon/my-dragon";

/** A free timing game. Sharing a catch uses ordinary feeding rules, never training rewards. */
export function FishingGame({ dragon, userId }: { dragon: PlayerDragon; userId: string }) {
  const [started, setStarted] = useState(false);
  const [finished, setFinished] = useState(false);
  const [fishX, setFishX] = useState(12);
  const [attempts, setAttempts] = useState(0);
  const [catches, setCatches] = useState(0);
  const [message, setMessage] = useState(
    "Cast your line. Reel in when the fish reaches the glowing hook.",
  );
  const x = useRef(12);
  const lastReel = useRef(-1000);
  const previous = useRef<number | null>(null);
  const elapsed = useRef(0);
  const ended = useRef(false);
  const care = useDragonCare(dragon, userId);
  useFrames((ms) => {
    if (document.hidden) {
      previous.current = null;
      return;
    }
    const delta = previous.current === null ? 0 : Math.min(50, ms - previous.current);
    previous.current = ms;
    elapsed.current += delta;
    x.current = 50 + Math.sin(elapsed.current / 720) * 37;
    setFishX(x.current);
  }, started && !finished);

  function reel() {
    if (ended.current || elapsed.current - lastReel.current < 350) return;
    lastReel.current = elapsed.current;
    const caught = Math.abs(x.current - 50) <= 12;
    setAttempts(attempts + 1);
    if (caught) setCatches(catches + 1);
    setMessage(
      caught
        ? "Splash! A fish for your dragon."
        : "The fish slipped past. Watch the hook and try again.",
    );
    if (attempts + 1 === 5) {
      ended.current = true;
      setFinished(true);
    }
  }

  return (
    <section className="space-y-4">
      <div
        className="relative h-64 overflow-hidden rounded-3xl bg-gradient-to-b from-sky-200 via-cyan-600 to-teal-900"
        role="img"
        aria-label="Your dragon fishing beside a moving fish and a glowing hook"
      >
        <div className="absolute top-0 left-3 w-40">
          <DragonActor
            speciesId={dragon.species_id}
            color={dragon.color_hex}
            pose={care.isSuccess ? "eat" : "idle"}
          />
        </div>
        <div className="absolute top-24 left-1/2 h-24 w-px bg-amber-100" />
        <div className="absolute top-44 left-1/2 flex size-14 -translate-x-1/2 items-center justify-center rounded-full border-2 border-dashed border-amber-100 bg-amber-100/20 text-2xl text-white">
          ⌝
        </div>
        <span
          className="absolute top-44 -translate-x-1/2 text-3xl text-amber-100"
          style={{ left: `${fishX}%` }}
        >
          <svg viewBox="0 0 80 40" className="h-8 w-14" aria-hidden="true">
            <path d="M23 20L4 4v32Z" fill="#edbb74" />
            <ellipse cx="45" cy="20" rx="26" ry="15" fill="#f3d797" />
            <path d="M39 7L49 1L54 8M39 32L50 38L55 31" fill="#edbb74" />
            <circle cx="61" cy="16" r="3" fill="#243f46" />
          </svg>
        </span>
      </div>
      <p role="status">
        {care.isSuccess ? care.data.message : care.isError ? care.error.message : message}
      </p>
      <p className="text-muted text-sm">
        {catches} caught · {attempts}/5 reels · Free play
      </p>
      <div className="flex flex-wrap gap-3">
        {!started && (
          <button
            type="button"
            className="bg-accent rounded-xl px-5 py-3 text-white"
            onClick={() => setStarted(true)}
          >
            Cast your line
          </button>
        )}
        {started && !finished && (
          <button
            type="button"
            className="bg-accent rounded-xl px-5 py-3 text-white"
            onClick={reel}
          >
            Reel in
          </button>
        )}
        {finished && catches > 0 && (
          <button
            type="button"
            className="bg-accent rounded-xl px-5 py-3 text-white"
            disabled={care.isPending || care.isSuccess}
            onClick={() => care.mutate({ action: "feed", food: "fish" })}
          >
            Share your catch with {dragon.name}
          </button>
        )}
        {finished && (
          <button
            type="button"
            className="border-line rounded-xl border px-5 py-3"
            disabled={care.isPending}
            onClick={() => {
              setStarted(false);
              setFinished(false);
              setAttempts(0);
              setCatches(0);
              elapsed.current = 0;
              previous.current = null;
              ended.current = false;
              lastReel.current = -1000;
              care.reset();
              setMessage("Ready for another cast.");
            }}
          >
            Fish again
          </button>
        )}
      </div>
    </section>
  );
}

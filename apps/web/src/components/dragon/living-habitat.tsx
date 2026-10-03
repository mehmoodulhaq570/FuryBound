"use client";

import { useReducedMotion } from "motion/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState, type CSSProperties } from "react";

import { DragonActor, type DragonPose } from "@/components/art/dragon-actor";
import { useTimers } from "@/components/training/games/use-timers";
import type { PlayerDragon } from "@/lib/dragon/my-dragon";
import { fetchIsland, islandKey, saveLayout, type HabitatLayout } from "@/lib/experience/island";

import styles from "./living-habitat.module.css";
import { useDragonCare, type Care } from "./use-dragon-care";

type Point = { x: number; y: number };
const bound = (point: Point) => {
  const x = Math.max(17, Math.min(83, point.x));
  return { x, y: Math.max(73 + Math.abs(x - 50) * 0.16, Math.min(88, point.y)) };
};

/** Scene motion is cosmetic; needs, refusals and rewards always come from the care API. */
export function LivingHabitat({
  dragon,
  userId,
  decoration = "camp",
  unlockedDecorations = [],
}: {
  dragon: PlayerDragon;
  userId: string;
  decoration?: string;
  unlockedDecorations?: string[];
}) {
  const [position, setPosition] = useState({ x: 51, y: 75, facing: 1, duration: 0 });
  const [pose, setPose] = useState<DragonPose>("idle");
  const [busy, setBusy] = useState(false);
  const [foodOpen, setFoodOpen] = useState(false);
  const [aiming, setAiming] = useState(false);
  const [ball, setBall] = useState<Point | null>(null);
  const [feedback, setFeedback] = useState(`Tap the meadow to guide ${dragon.name}.`);
  const [effect, setEffect] = useState("");
  const [effectSerial, setEffectSerial] = useState(0);
  const [placing, setPlacing] = useState<keyof HabitatLayout["positions"] | null>(null);
  const [muted, setMuted] = useState(true);
  const audio = useRef<AudioContext | null>(null);
  const serial = useRef(0);
  const working = useRef(false);
  const later = useTimers();
  const reduced = useReducedMotion();
  const care = useDragonCare(dragon, userId);
  const client = useQueryClient();
  const island = useQuery({
    queryKey: islandKey(dragon.id),
    queryFn: () => fetchIsland(dragon.id),
  });
  const arrange = useMutation({
    mutationFn: (layout: HabitatLayout) => saveLayout(dragon.id, layout),
    onSuccess: (data) => {
      client.setQueryData(islandKey(dragon.id), data);
      setPlacing(null);
      setFeedback("Your decoration is in place. Welcome home!");
    },
    onError: (error) => setFeedback(error.message),
  });
  function decorationStyle(key: keyof HabitatLayout["positions"]): CSSProperties | undefined {
    const point = island.data?.layout.positions[key];
    return point
      ? {
          left: `${point.x}%`,
          top: `${point.y}%`,
          right: "auto",
          bottom: "auto",
          transform: "translate(-50%, -50%)",
        }
      : undefined;
  }
  useEffect(
    () => () => {
      serial.current++;
      void audio.current?.close();
    },
    [],
  );

  function sound(kind: "step" | "happy" | "rest") {
    if (muted || typeof AudioContext === "undefined") return;
    try {
      audio.current ??= new AudioContext();
      const ctx = audio.current;
      void ctx.resume().catch(() => {});
      const oscillator = ctx.createOscillator();
      const gain = ctx.createGain();
      oscillator.type = "sine";
      const note = kind === "rest" ? 220 : kind === "step" ? 330 : 660;
      oscillator.frequency.setValueAtTime(note, ctx.currentTime);
      oscillator.frequency.exponentialRampToValueAtTime(note * 1.4, ctx.currentTime + 0.12);
      gain.gain.setValueAtTime(0.035, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
      oscillator.connect(gain);
      gain.connect(ctx.destination);
      oscillator.start();
      oscillator.stop(ctx.currentTime + 0.3);
    } catch {
      /* Sound is optional; the scene still works without an audio device. */
    }
  }

  function travel(point: Point, arrive?: (id: number) => void) {
    const target = bound(point);
    const id = ++serial.current;
    const distance = Math.hypot(target.x - position.x, target.y - position.y);
    const duration = reduced ? 0 : Math.min(1600, Math.max(200, distance * 28));
    setPose("walk");
    setEffect("");
    setPosition({ ...target, facing: target.x < position.x ? -1 : 1, duration });
    sound("step");
    later(() => {
      if (id === serial.current) {
        setPose("idle");
        arrive?.(id);
      }
    }, duration);
  }

  function act(action: Care, target: Point) {
    if (working.current) return;
    working.current = true;
    setBusy(true);
    setFoodOpen(false);
    setAiming(false);
    setFeedback(`${dragon.name} is coming over…`);
    travel(target, (id) => {
      setFeedback(`Checking what ${dragon.name} needs…`);
      care.mutate(action, {
        onSuccess: (result) => {
          if (serial.current !== id) return;
          setPose(action.action === "feed" ? "eat" : action.action === "rest" ? "sleep" : "happy");
          setEffect(action.action === "feed" ? "♥" : action.action === "rest" ? "z z z" : "✦");
          setEffectSerial((value) => value + 1);
          setFeedback(result.message);
          sound(action.action === "rest" ? "rest" : "happy");
          if (action.action !== "rest")
            later(() => {
              if (serial.current === id) {
                setPose("idle");
                setEffect("");
                setBall(null);
              }
            }, 2600);
        },
        onError: (error) => {
          if (serial.current === id) {
            setPose("idle");
            setFeedback(error.message);
            setBall(null);
          }
        },
        onSettled: () => {
          working.current = false;
          setBusy(false);
        },
      });
    });
  }

  function guide(point: Point) {
    if (working.current) return;
    if (arrange.isPending) return;
    if (placing) {
      arrange.mutate({
        positions: {
          ...island.data?.layout.positions,
          [placing]: {
            x: Math.max(7, Math.min(90, point.x)),
            y: Math.max(30, Math.min(90, point.y)),
          },
        },
      });
      return;
    }
    if (aiming) {
      const target = bound(point);
      setBall(target);
      act({ action: "play" }, target);
    } else {
      setFeedback(`${dragon.name} follows your lead.`);
      travel(point);
    }
  }

  function pet() {
    if (working.current) return;
    const id = ++serial.current;
    setPose(dragon.mood.id === "angry" ? "idle" : "happy");
    setEffect(dragon.mood.id === "angry" ? "…" : "♥");
    setEffectSerial((value) => value + 1);
    sound("happy");
    setFeedback(
      dragon.mood.id === "angry"
        ? `${dragon.name} watches your hand cautiously.`
        : `${dragon.name} leans closer and gives a contented little rumble.`,
    );
    later(() => {
      if (serial.current === id) {
        setPose("idle");
        setEffect("");
      }
    }, 1800);
  }

  return (
    <section aria-label={`${dragon.name}'s playable home`} className="space-y-3">
      <div className={styles.scene}>
        <div className={styles.sun} />
        <div className={styles.cloud} />
        <div className={styles.cloudTwo} />
        <div className={styles.mountains} />
        <div className={styles.sea} />
        <div className={styles.shore} />
        <div className={styles.grass} />
        <button
          type="button"
          className={styles.meadow}
          disabled={busy}
          aria-label={
            aiming ? "Throw the ball in the meadow" : "Guide your dragon across the meadow"
          }
          onClick={(event) => {
            const rect = event.currentTarget.parentElement!.getBoundingClientRect();
            guide(
              event.detail === 0
                ? { x: position.x < 50 ? 70 : 30, y: 76 }
                : {
                    x: ((event.clientX - rect.left) / rect.width) * 100,
                    y: ((event.clientY - rect.top) / rect.height) * 100,
                  },
            );
          }}
          onKeyDown={(event) => {
            if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) {
              event.preventDefault();
              guide({
                x:
                  position.x +
                  (event.key === "ArrowLeft" ? -10 : event.key === "ArrowRight" ? 10 : 0),
                y: position.y + (event.key === "ArrowUp" ? -5 : event.key === "ArrowDown" ? 5 : 0),
              });
            }
          }}
        />
        <div className={styles.sceneHeader}>
          <span>HOME · {dragon.mood.label}</span>
          <button type="button" aria-pressed={!muted} onClick={() => setMuted(!muted)}>
            {muted ? "Sound off" : "Sound on"}
          </button>
        </div>
        <div className={styles.decorations} aria-hidden="true">
          {(decoration === "lanterns" || island.data?.layout.positions.lanterns) && (
            <div className={styles.lanterns} style={decorationStyle("lanterns")}>
              ● ── ● ── ● ── ●
            </div>
          )}
          {(decoration === "flowers" || island.data?.layout.positions.flowers) && (
            <div className={styles.flowers} style={decorationStyle("flowers")}>
              ✿　✿　✿
            </div>
          )}
          {(decoration === "pennant" || island.data?.layout.positions.pennant) && (
            <div className={styles.pennant} style={decorationStyle("pennant")}>
              ⚑
            </div>
          )}
          {(decoration === "beacon" || island.data?.layout.positions.beacon) && (
            <div className={styles.beacon} style={decorationStyle("beacon")} />
          )}
        </div>
        <button
          type="button"
          className={styles.nest}
          disabled={busy}
          onClick={() => act({ action: "rest" }, { x: 27, y: 76 })}
          aria-label={`Let ${dragon.name} rest in the nest`}
        >
          <span>☾</span>
          <small>Nest</small>
        </button>
        <button
          type="button"
          className={styles.basket}
          disabled={busy}
          aria-expanded={foodOpen}
          onClick={() => {
            setFoodOpen(!foodOpen);
            setAiming(false);
          }}
          aria-label="Open food basket"
        >
          <span>
            <svg viewBox="0 0 70 50" width="62" height="45" aria-hidden="true">
              <path d="M9 20Q10 1 35 1Q60 1 61 20" fill="none" stroke="#735332" strokeWidth="4" />
              <path d="M6 19h58l-7 28H13Z" fill="#ac834f" stroke="#6b5032" strokeWidth="2" />
              <path
                d="M9 28h52M11 37h48M23 20v27M35 20v27M47 20v27"
                stroke="#d4ac75"
                strokeWidth="2"
              />
              <path d="M26 17l-10-7v12Z" fill="#d8ded0" />
              <ellipse cx="36" cy="16" rx="12" ry="7" fill="#d8ded0" />
              <circle cx="43" cy="14" r="1.5" fill="#273e41" />
            </svg>
          </span>
          <small>Food basket</small>
        </button>
        <button
          type="button"
          className={styles.toy}
          disabled={busy}
          aria-pressed={aiming}
          onClick={() => {
            setAiming(!aiming);
            setFoodOpen(false);
            setFeedback("Choose a spot in the meadow to throw the ball.");
          }}
          aria-label="Throw a ball"
        >
          <span>◉</span>
          <small>Ball</small>
        </button>
        {ball && (
          <div
            className={styles.ball}
            style={{ left: `${ball.x}%`, top: `${ball.y}%` }}
            aria-hidden="true"
          >
            ◉
          </div>
        )}
        <button
          type="button"
          className={styles.dragon}
          data-walking={pose === "walk"}
          aria-label={`Pet ${dragon.name}`}
          disabled={busy}
          onClick={pet}
          style={
            {
              left: `${position.x}%`,
              top: `${position.y}%`,
              "--travel": `${position.duration}ms`,
              "--facing": position.facing,
            } as CSSProperties
          }
        >
          <div className={styles.actor}>
            <DragonActor
              speciesId={dragon.species_id}
              color={dragon.color_hex}
              pose={pose === "idle" && dragon.mood.id === "tired" ? "sleep" : pose}
              mood={dragon.mood.id}
            />
          </div>
          {effect && (
            <span key={effectSerial} className={styles.reaction}>
              {effect}
            </span>
          )}
        </button>
        {foodOpen && (
          <div className={styles.foodMenu} aria-label="Choose a food">
            {dragon.foods.map((food) => (
              <button
                type="button"
                key={food}
                onClick={() => act({ action: "feed", food }, { x: 77, y: 77 })}
              >
                {food}
              </button>
            ))}
          </div>
        )}
      </div>
      <p role="status" className="min-h-10 text-center text-sm">
        {feedback}
      </p>
      <p className="text-muted text-center text-xs">
        Tap the ground to walk · Basket to feed · Nest to rest · Ball to play · Tap your dragon to
        say hello. Keyboard: focus the meadow and use arrow keys.
      </p>
      {unlockedDecorations.length > 0 && island.data && (
        <details className="text-sm">
          <summary className="cursor-pointer">Arrange your earned decorations</summary>
          <div className="mt-3 flex flex-wrap gap-2">
            {unlockedDecorations.map((key) => (
              <button
                type="button"
                key={key}
                disabled={busy || arrange.isPending}
                className="border-line rounded-full border px-3 py-2 capitalize"
                aria-pressed={placing === key}
                onClick={() => {
                  setPlacing(key as keyof HabitatLayout["positions"]);
                  setAiming(false);
                  setFoodOpen(false);
                  setFeedback(`Tap the meadow to place your ${key}.`);
                }}
              >
                {key}
              </button>
            ))}
            {placing && (
              <button type="button" onClick={() => setPlacing(null)} className="underline">
                Cancel placement
              </button>
            )}
          </div>
        </details>
      )}
    </section>
  );
}

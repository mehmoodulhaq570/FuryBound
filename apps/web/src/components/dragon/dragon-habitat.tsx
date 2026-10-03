"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRef, useState } from "react";

import { DragonSilhouette } from "@/components/art/dragon-silhouette";
import { ProgressPanel } from "@/components/experience/progress-panel";
import type { PlayerDragon } from "@/lib/dragon/my-dragon";
import {
  experienceKey,
  fetchExperience,
  setDecoration,
  type Decoration,
} from "@/lib/experience/api";
import { useTimers } from "@/components/training/games/use-timers";

import { CarePanel } from "./care-panel";
import { DragonCard } from "./dragon-card";
import styles from "./habitat.module.css";

export function HabitatScene({
  dragon,
  decoration = "camp",
  reaction = "",
}: {
  dragon: PlayerDragon;
  decoration?: string;
  reaction?: string;
}) {
  const pose = reaction || dragon.mood.id;
  const poseClass = styles[pose] ?? "";
  return (
    <div
      className={styles.habitat}
      role="img"
      aria-label={`${dragon.name} in a coastal habitat, feeling ${dragon.mood.label.toLowerCase()}. Decoration: ${decoration}.`}
    >
      <div className={styles.moon} />
      <div className={styles.ridge} />
      <div className={styles.ground} />
      <div className={styles.nest} />
      <div className={styles.decoration}>
        {decoration === "lanterns" && (
          <div className={styles.lanterns}>
            {[0, 1, 2, 3, 4].map((i) => (
              <span key={i} />
            ))}
          </div>
        )}
        {decoration === "flowers" && (
          <div className={styles.flowers}>
            <span>✿</span>
            <span>✿</span>
            <span>✿</span>
          </div>
        )}
        {decoration === "pennant" && <div className={styles.pennant} />}
        {decoration === "beacon" && <div className={styles.beacon} />}
      </div>
      <div className={`${styles.dragon} ${poseClass}`}>
        <DragonSilhouette
          speciesId={dragon.species_id}
          color={dragon.color_hex ?? "#c2dbe6"}
          outline
        />
      </div>
      {reaction && (
        <span className={styles.reaction}>
          {reaction === "feed" ? "♥" : reaction === "rest" ? "z z" : "✦"}
        </span>
      )}
      <span className={styles.label}>Misty Cove · {dragon.mood.label}</span>
    </div>
  );
}

export function DragonHabitat({ dragon, userId }: { dragon: PlayerDragon; userId: string }) {
  const [reaction, setReaction] = useState({ action: "", count: 0 });
  const reactionCount = useRef(0);
  const later = useTimers();
  const queryClient = useQueryClient();
  const experience = useQuery({
    queryKey: experienceKey(dragon.id),
    queryFn: () => fetchExperience(dragon.id),
  });
  const decorate = useMutation({
    mutationFn: (decoration: Decoration) => setDecoration(dragon.id, decoration),
    onSuccess: (data) => queryClient.setQueryData(experienceKey(dragon.id), data),
  });
  const choices: { id: Decoration; label: string }[] = [
    { id: "camp", label: "Quiet camp" },
    { id: "lanterns", label: "Warm lanterns" },
    { id: "flowers", label: "Wildflowers" },
    { id: "pennant", label: "Flight pennant" },
    { id: "beacon", label: "Rescue beacon" },
  ];
  const hunger = dragon.needs.find((n) => n.id === "hunger")?.value ?? 0;
  const energy = dragon.needs.find((n) => n.id === "energy")?.value ?? 100;
  function react(action: "feed" | "rest" | "play") {
    const count = ++reactionCount.current;
    setReaction({ action, count });
    later(
      () =>
        setReaction((current) => (current.count === count ? { ...current, action: "" } : current)),
      2500,
    );
  }
  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <header className="space-y-2">
        <p className="text-accent text-xs font-semibold tracking-widest uppercase">
          Your home together
        </p>
        <h1 className="text-4xl font-semibold">{dragon.name}</h1>
        <p className="text-muted">
          {dragon.species_name} · Level {dragon.level} · {dragon.stage_label}
        </p>
      </header>
      <HabitatScene
        key={reaction.count}
        dragon={dragon}
        decoration={experience.data?.decoration}
        reaction={reaction.action}
      />
      <p className="text-muted text-center italic">{dragon.thought}</p>
      <section className="bg-surface border-line space-y-5 rounded-2xl border p-5">
        <div className="grid grid-cols-3 gap-3">
          {dragon.needs.map((n) => (
            <div key={n.id}>
              <div className="flex justify-between text-xs">
                <span>{n.label}</span>
                <span>{n.value}</span>
              </div>
              <meter
                className="mt-2 h-3 w-full"
                aria-label={n.label}
                min={0}
                max={100}
                value={n.value}
              />
            </div>
          ))}
        </div>
        <CarePanel dragon={dragon} userId={userId} onReaction={react} />
      </section>
      <div className="grid gap-3 sm:grid-cols-2">
        <Link
          href={hunger > 85 || energy < 15 ? "/dragon#care" : "/train/flight"}
          className="bg-accent rounded-2xl p-5 text-white"
        >
          <p className="font-semibold">
            {hunger > 85
              ? "Share a meal first"
              : energy < 15
                ? "Let your dragon rest"
                : "Take to the skies"}
          </p>
          <p className="mt-1 text-sm opacity-90">
            {hunger > 85 || energy < 15
              ? "A cared-for dragon is ready for the next adventure."
              : "A short flight through the sea stacks. Train agility and speed."}
          </p>
        </Link>
        <Link href="/adventure" className="bg-surface border-line rounded-2xl border p-5">
          <p className="font-semibold">
            {experience.data?.adventure?.node === "complete"
              ? "Your rescue story"
              : "A cry from Misty Cove"}
          </p>
          <p className="text-muted mt-1 text-sm">
            A wild dragon is caught in a net. Choose your approach and fly to its rescue.
          </p>
        </Link>
      </div>
      <div className="flex flex-wrap gap-4 text-sm">
        <Link href="/train" className="text-accent underline">
          All training activities
        </Link>
        <Link href="/chat" className="text-accent underline">
          Talk to {dragon.name}
        </Link>
        <Link href="/dragon-book" className="text-accent underline">
          Your discoveries
        </Link>
      </div>
      {experience.data && (
        <>
          <section className="space-y-3">
            <h2 className="text-xl font-semibold">Make it your home</h2>
            <div className="flex flex-wrap gap-2">
              {choices.map((c) => {
                const unlocked =
                  c.id === "camp" ||
                  experience.data.achievements.some((a) => a.earned && a.decoration === c.id);
                return (
                  <button
                    key={c.id}
                    type="button"
                    aria-pressed={experience.data.decoration === c.id}
                    disabled={!unlocked || decorate.isPending}
                    onClick={() => decorate.mutate(c.id)}
                    className="border-line aria-pressed:border-accent aria-pressed:bg-accent/10 rounded-full border px-4 py-2 text-sm disabled:opacity-50"
                  >
                    {c.label}
                    {!unlocked && " 🔒"}
                  </button>
                );
              })}
            </div>
            {decorate.isError && <p role="alert">{decorate.error.message}</p>}
          </section>
          <ProgressPanel experience={experience.data} />
        </>
      )}
      {experience.isError && (
        <p role="alert" className="text-muted text-sm">
          {experience.error.message}{" "}
          <button
            type="button"
            onClick={() => experience.refetch()}
            className="text-accent underline"
          >
            Try again
          </button>
        </p>
      )}
      <details className="border-line rounded-2xl border p-5">
        <summary className="cursor-pointer font-semibold">Dragon profile, trust and stats</summary>
        <div className="mt-6">
          <DragonCard dragon={dragon} />
        </div>
      </details>
    </div>
  );
}

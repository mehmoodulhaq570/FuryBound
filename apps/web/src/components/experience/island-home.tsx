"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { DragonActor } from "@/components/art/dragon-actor";
import { DragonGate } from "@/components/training/dragon-gate";
import { useTimers } from "@/components/training/games/use-timers";
import { myDragonQueryKey, type PlayerDragon } from "@/lib/dragon/my-dragon";
import { experienceKey } from "@/lib/experience/api";
import { collectTreasure, fetchIsland, islandKey } from "@/lib/experience/island";
import { historyKey, trainingKey } from "@/lib/training/api";

import { FishingGame } from "./fishing-game";
import styles from "./island.module.css";

const places = [
  {
    id: "home",
    label: "Home",
    x: 28,
    y: 70,
    icon: "⌂",
    text: "A warm nest and a familiar face.",
    treasure: null,
  },
  {
    id: "shore",
    label: "Fishing shore",
    x: 19,
    y: 37,
    icon: "≋",
    text: "Something pale glints between the pebbles.",
    treasure: "shell",
  },
  {
    id: "clearing",
    label: "Training clearing",
    x: 52,
    y: 67,
    icon: "◎",
    text: "A bright scrap flutters beside the targets.",
    treasure: "ribbon",
  },
  {
    id: "cove",
    label: "Misty Cove",
    x: 77,
    y: 47,
    icon: "⚑",
    text: "Something iridescent lies beside an old fishing net.",
    treasure: "scale",
  },
  {
    id: "lookout",
    label: "Hilltop lookout",
    x: 54,
    y: 23,
    icon: "△",
    text: "Your island stretches beneath you. Spread your wings!",
    treasure: null,
  },
] as const;

function Island({ dragon, userId }: { dragon: PlayerDragon; userId: string }) {
  const [location, setLocation] = useState<(typeof places)[number]>(places[0]);
  const [moving, setMoving] = useState(false);
  const [fishing, setFishing] = useState(false);
  const [landed, setLanded] = useState(false);
  const later = useTimers();
  const client = useQueryClient();
  const state = useQuery({ queryKey: islandKey(dragon.id), queryFn: () => fetchIsland(dragon.id) });
  const collect = useMutation({
    mutationFn: (treasure: string) => collectTreasure(dragon.id, treasure),
    onSuccess: (data) => {
      client.setQueryData(islandKey(dragon.id), data);
      client.invalidateQueries({ queryKey: myDragonQueryKey(userId) });
      client.invalidateQueries({ queryKey: experienceKey(dragon.id) });
      client.invalidateQueries({ queryKey: trainingKey(dragon.id) });
      client.invalidateQueries({ queryKey: historyKey(dragon.id) });
    },
  });
  const treasure = location.treasure;
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <header>
        <p className="text-accent text-xs tracking-widest uppercase">Explore together</p>
        <h1 className="mt-2 text-3xl font-semibold">Your little island</h1>
        <p className="text-muted mt-2">
          Guide {dragon.name} between places. Follow the clues to find three keepsakes.
        </p>
      </header>
      <div className={styles.map} aria-label="Interactive island map">
        <svg
          viewBox="0 0 700 450"
          preserveAspectRatio="none"
          aria-hidden="true"
          className={styles.land}
        >
          <path
            d="M80 157Q38 70 174 73Q240 14 343 58Q490 17 568 151Q692 178 604 296Q626 418 448 392Q326 448 256 383Q65 399 85 279Q29 231 80 157Z"
            fill="#e2d5a1"
          />
          <path
            d="M102 165Q96 86 202 104Q266 42 348 90Q487 60 532 157Q631 189 574 285Q575 361 431 359Q319 405 267 345Q111 364 121 278Q61 227 102 165Z"
            fill="#8ca56e"
          />
          <path d="M380 79l-48 66h113ZM220 171l-30 49h72ZM480 184l-37 57h88Z" fill="#5f7d65" />
          <path
            d="M196 315Q153 227 131 162M196 315L364 302Q409 178 539 215M364 302L378 104"
            fill="none"
            stroke="#dac89b"
            strokeWidth="9"
            strokeDasharray="6 8"
          />
        </svg>
        {places.map((place) => (
          <button
            key={place.id}
            type="button"
            aria-label={place.label}
            className={styles.place}
            aria-pressed={location.id === place.id}
            disabled={
              moving ||
              collect.isPending ||
              (place.id === "lookout" && !state.data?.lookout_unlocked)
            }
            style={{ left: `${place.x}%`, top: `${place.y}%` }}
            onClick={() => {
              setLocation(place);
              setMoving(true);
              setFishing(false);
              setLanded(false);
              later(() => {
                setMoving(false);
                setLanded(true);
              }, 850);
            }}
          >
            <span>{place.icon}</span>
            <small>
              {place.id === "lookout" && !state.data?.lookout_unlocked ? "Lookout 🔒" : place.label}
            </small>
          </button>
        ))}
        <div
          className={styles.dragon}
          style={{ left: `${location.x}%`, top: `${location.y + 9}%` }}
          aria-hidden="true"
        >
          <DragonActor
            speciesId={dragon.species_id}
            color={dragon.color_hex}
            pose={moving ? "fly" : landed ? "land" : "idle"}
          />
        </div>
      </div>
      {state.isPending && <p role="status">Opening your island journal…</p>}
      {state.isError && (
        <p role="alert">
          {state.error.message}{" "}
          <button type="button" onClick={() => state.refetch()} className="underline">
            Try again
          </button>
        </p>
      )}
      <section className="border-line bg-surface space-y-4 rounded-2xl border p-5">
        <h2 className="text-xl font-semibold">{location.label}</h2>
        <p>{moving ? `${dragon.name} is flying over…` : location.text}</p>
        {!moving && treasure && state.data && (
          <div>
            {state.data.treasures.includes(treasure) ? (
              <p className="text-accent">✦ {treasure} added to your keepsakes</p>
            ) : (
              <button
                type="button"
                className="bg-accent rounded-xl px-4 py-3 text-white"
                disabled={collect.isPending}
                onClick={() => collect.mutate(treasure)}
              >
                Investigate the glint
              </button>
            )}
          </div>
        )}
        {!moving && (
          <div className="flex flex-wrap gap-4">
            {location.id === "home" && (
              <Link href="/dragon" className="text-accent underline">
                Enter your habitat
              </Link>
            )}
            {location.id === "shore" && (
              <button
                type="button"
                onClick={() => setFishing(!fishing)}
                className="text-accent underline"
              >
                {fishing ? "Put away the fishing rod" : "Go fishing"}
              </button>
            )}
            {location.id === "clearing" && (
              <>
                <Link href="/train/flight" className="text-accent underline">
                  Flight course
                </Link>
                <Link href="/train/accuracy" className="text-accent underline">
                  Target practice · Young stage
                </Link>
              </>
            )}
            {location.id === "cove" && (
              <Link href="/adventure" className="text-accent underline">
                Help the trapped dragon
              </Link>
            )}
            {location.id === "lookout" && (
              <Link href="/train/flight" className="text-accent underline">
                Take to the skies
              </Link>
            )}
          </div>
        )}
        {fishing && !moving && <FishingGame key={location.id} dragon={dragon} userId={userId} />}
        {collect.isError && <p role="alert">{collect.error.message}</p>}
      </section>
      <section className="space-y-3">
        <h2 className="text-lg font-semibold">
          Island keepsakes · {state.data?.treasures.length ?? 0}/3
        </h2>
        <div className="flex gap-3">
          {["shell", "ribbon", "scale"].map((item) => (
            <div
              key={item}
              className={`border-line flex-1 rounded-xl border p-3 text-center capitalize ${state.data?.treasures.includes(item) ? "bg-accent/10" : "text-muted"}`}
            >
              {state.data?.treasures.includes(item) ? "✦" : "◇"} {item}
            </div>
          ))}
        </div>
        <p className="text-muted text-sm">
          {state.data?.lookout_unlocked
            ? "Hilltop lookout unlocked · 40 exploration XP earned. Your keepsakes are saved."
            : "Find all three to open the hilltop lookout and earn 40 XP once."}
        </p>
      </section>
      <Link href="/dragon" className="text-accent underline">
        Return to your dragon
      </Link>
    </div>
  );
}

export function IslandHome() {
  return (
    <DragonGate title="Your island" path="/island">
      {(dragon, userId) => <Island key={dragon.id} dragon={dragon} userId={userId} />}
    </DragonGate>
  );
}

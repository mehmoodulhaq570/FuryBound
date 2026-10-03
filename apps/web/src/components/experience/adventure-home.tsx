"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { DragonSilhouette } from "@/components/art/dragon-silhouette";
import { DragonGate } from "@/components/training/dragon-gate";
import { FlightGame } from "@/components/training/games/flight-game";
import { api } from "@/lib/api/client";
import { myDragonQueryKey, type PlayerDragon } from "@/lib/dragon/my-dragon";
import {
  chooseAdventure,
  experienceKey,
  fetchExperience,
  startAdventure,
  type AdventureChoice,
  type AdventureState,
} from "@/lib/experience/api";
import { historyKey, trainingKey } from "@/lib/training/api";

const button =
  "border-line hover:border-accent focus-visible:outline-accent bg-surface rounded-xl border p-4 text-left disabled:opacity-50";

type FlightResult = { score: number; durationMs: number; meta: Record<string, unknown> };

function RescueFlight({
  dragon,
  onFinish,
}: {
  dragon: PlayerDragon;
  onFinish: (result: FlightResult) => void;
}) {
  const start = useRef(0);
  useEffect(() => {
    start.current = performance.now();
  }, []);
  return (
    <FlightGame
      speciesId={dragon.species_id}
      color={dragon.color_hex}
      agility={dragon.stats.find((s) => s.id === "agility")?.value}
      onFinish={(score, meta, activeDurationMs) =>
        onFinish({
          score,
          meta,
          durationMs: Math.round(activeDurationMs ?? performance.now() - start.current),
        })
      }
    />
  );
}

function Mission({ dragon, userId }: { dragon: PlayerDragon; userId: string }) {
  const client = useQueryClient();
  const experience = useQuery({
    queryKey: experienceKey(dragon.id),
    queryFn: () => fetchExperience(dragon.id),
  });
  const [playing, setPlaying] = useState(false);
  const [result, setResult] = useState<FlightResult | null>(null);
  const run = experience.data?.adventure;

  function update(run: AdventureState) {
    client.setQueryData(
      experienceKey(dragon.id),
      (previous: Awaited<ReturnType<typeof fetchExperience>> | undefined) =>
        previous ? { ...previous, adventure: run } : previous,
    );
    client.invalidateQueries({ queryKey: experienceKey(dragon.id) });
    client.invalidateQueries({ queryKey: myDragonQueryKey(userId) });
    client.invalidateQueries({ queryKey: trainingKey(dragon.id) });
    client.invalidateQueries({ queryKey: historyKey(dragon.id) });
    client.invalidateQueries({ queryKey: ["discoveries"] });
    client.invalidateQueries({ queryKey: ["dragon-memory"] });
  }

  const begin = useMutation({ mutationFn: () => startAdventure(dragon.id), onSuccess: update });
  const choose = useMutation({
    mutationFn: (choice: AdventureChoice) => chooseAdventure(dragon.id, run!.id, choice),
    onSuccess: update,
  });
  const prepare = useMutation({
    mutationFn: () => chooseAdventure(dragon.id, run!.id, "continue"),
    onSuccess: (next) => {
      update(next);
      if (next.node === "flight") {
        setResult(null);
        setPlaying(true);
      }
    },
  });
  const saveFlight = useMutation({
    mutationFn: async (flight: FlightResult) => {
      const { data, error, response } = await api.POST(
        "/api/v1/training-sessions/{session_id}/complete",
        {
          params: { path: { session_id: run!.training_session_id! } },
          body: { score: flight.score, duration_ms: flight.durationMs, meta: flight.meta },
        },
      );
      if (error || !data) {
        // A response may have been lost after the server saved it. Confirm before retrying.
        const saved = response.status === 409 ? await fetchExperience(dragon.id) : null;
        if (!saved?.adventure?.flight_finished)
          throw new Error(error?.detail?.toString() ?? "Couldn't save your flight");
      }
      return chooseAdventure(dragon.id, run!.id, "continue");
    },
    onSuccess: (next) => {
      setPlaying(false);
      update(next);
    },
  });
  const error = begin.error ?? choose.error ?? prepare.error ?? saveFlight.error;
  const pending = begin.isPending || choose.isPending || prepare.isPending || saveFlight.isPending;
  const part = !run
    ? 0
    : run.node === "approach"
      ? 1
      : run.node === "flight"
        ? 2
        : run.node === "rescue"
          ? 3
          : 4;
  const choices = [
    {
      id: "gentle" as const,
      title: "Approach gently",
      text: "Keep your wings quiet and reassure the frightened dragon.",
      trait: "patience",
    },
    {
      id: "bold" as const,
      title: "Lead from the front",
      text: "Let your dragon clear a path through the rocky cove.",
      trait: "courage",
    },
    {
      id: "clever" as const,
      title: "Study the tide",
      text: "Find a sheltered route and plan your landing.",
      trait: "intelligence",
    },
  ];
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header className="space-y-2">
        <p className="text-accent text-xs font-semibold tracking-widest uppercase">
          Your first adventure
        </p>
        <h1 className="text-3xl font-semibold">A cry from Misty Cove</h1>
        <p className="text-muted">
          A small wild dragon is tangled in an abandoned fishing net. The tide is rising. You and{" "}
          {dragon.name} can help.
        </p>
      </header>
      <ol className="grid grid-cols-4 gap-2 text-xs" aria-label="Adventure progress">
        {["Set out", "Approach", "Fly", "Rescue"].map((label, i) => (
          <li
            key={label}
            className={`border-t-4 pt-2 ${part > i ? "border-accent" : "border-line text-muted"}`}
          >
            {label}
          </li>
        ))}
      </ol>
      {!playing && (
        <div
          className="relative flex h-52 items-end justify-center gap-6 overflow-hidden rounded-3xl bg-gradient-to-b from-slate-600 via-teal-700 to-teal-950 p-6"
          role="img"
          aria-label="Two dragons on the rocky shore of Misty Cove"
        >
          <div className="absolute top-7 right-12 size-12 rounded-full bg-amber-100/90" />
          <DragonSilhouette
            speciesId={dragon.species_id}
            color={dragon.color_hex ?? "#d3e8ea"}
            className="relative w-36 drop-shadow-xl"
          />
          <div className="relative">
            <DragonSilhouette speciesId="scuttleclaw" color="#bbd396" className="w-20" />
            {run?.node !== "complete" && (
              <div className="absolute inset-0 rounded-xl border-2 border-dashed border-amber-100/60" />
            )}
          </div>
        </div>
      )}
      {experience.isPending && <p role="status">Opening your adventure journal…</p>}
      {experience.isError && (
        <p role="alert">
          {experience.error.message}{" "}
          <button
            onClick={() => experience.refetch()}
            className="text-accent underline"
            type="button"
          >
            Try again
          </button>
        </p>
      )}
      {experience.data && !run && (
        <div className="space-y-4">
          <p>
            Your choices draw on {dragon.name}&apos;s personality and skills. Fly through the sea
            stacks, then decide how to free the wild dragon.
          </p>
          <p className="text-muted text-sm">
            Earn training XP, a rescue bonus of 60–80 XP, trust, a Dragon Book discovery and a
            beacon for your habitat. Your progress saves as you go.
          </p>
          <button
            className="bg-accent rounded-xl px-5 py-3 font-semibold text-white disabled:opacity-50"
            disabled={pending}
            onClick={() => begin.mutate()}
            type="button"
          >
            Set out with {dragon.name}
          </button>
        </div>
      )}
      {run?.node === "approach" && (
        <section className="space-y-4">
          <h2 className="text-xl font-semibold">How will you approach?</h2>
          <div className="grid gap-3">
            {choices.map((c) => (
              <button
                type="button"
                className={button}
                key={c.id}
                disabled={pending}
                onClick={() => choose.mutate(c.id)}
              >
                <span className="block font-semibold">{c.title}</span>
                <span className="text-muted mt-1 block text-sm">{c.text}</span>
                <span className="text-accent mt-2 block text-xs">
                  {c.trait} · {dragon.personality.find((t) => t.id === c.trait)?.value ?? 50}/100
                </span>
              </button>
            ))}
          </div>
        </section>
      )}
      {run?.node === "flight" && !playing && (
        <section className="space-y-4">
          <h2 className="text-xl font-semibold">Through the sea stacks</h2>
          <p>
            {run.approach === "gentle"
              ? `${dragon.name} lowers its head and listens to your calm voice.`
              : run.approach === "bold"
                ? `${dragon.name} spreads its wings, ready to lead.`
                : `${dragon.name} studies the sheltered gaps between the rocks.`}{" "}
            Guide your dragon through six openings using the arrow keys or Climb and Dive.
          </p>
          <button
            type="button"
            disabled={pending}
            className="bg-accent rounded-xl px-5 py-3 font-semibold text-white disabled:opacity-50"
            onClick={() => (run.flight_finished ? choose.mutate("continue") : prepare.mutate())}
          >
            {run.flight_finished
              ? "Your flight is saved — continue to the rescue"
              : "Begin rescue flight"}
          </button>
        </section>
      )}
      {playing && !result && (
        <RescueFlight
          dragon={dragon}
          onFinish={(flight) => {
            setResult(flight);
            saveFlight.mutate(flight);
          }}
        />
      )}
      {playing && result && (
        <div className="space-y-3">
          <p role="status">
            {saveFlight.isPending
              ? "Landing and saving your flight…"
              : `Flight score: ${result.score}/100`}
          </p>
          {saveFlight.isError && (
            <button type="button" className={button} onClick={() => saveFlight.mutate(result)}>
              Retry saving this flight
            </button>
          )}
        </div>
      )}
      {run?.node === "rescue" && (
        <section className="space-y-4">
          <h2 className="text-xl font-semibold">The net is caught on a rock</h2>
          <p>
            You land safely with a flight score of {run.score}/100. The little dragon watches you.
            Your dragon&apos;s skills can help you finish the rescue.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <button
              type="button"
              disabled={pending}
              className={button}
              onClick={() => choose.mutate("untie")}
            >
              <span className="block font-semibold">Untie the knots</span>
              <span className="text-muted text-sm">
                Work patiently · Intelligence{" "}
                {dragon.stats.find((s) => s.id === "intelligence")?.value ?? 30}
              </span>
            </button>
            <button
              type="button"
              disabled={pending}
              className={button}
              onClick={() => choose.mutate("lift")}
            >
              <span className="block font-semibold">Lift the net together</span>
              <span className="text-muted text-sm">
                Work as a team · Strength{" "}
                {dragon.stats.find((s) => s.id === "strength")?.value ?? 30}
              </span>
            </button>
          </div>
        </section>
      )}
      {run?.node === "complete" && (
        <section className="bg-accent/10 space-y-4 rounded-2xl p-6">
          <p className="text-accent text-sm font-semibold tracking-widest uppercase">
            A helping wing ✦
          </p>
          <h2 className="text-2xl font-semibold">Back to open skies</h2>
          <p>{run.outcome}</p>
          <p className="font-semibold">
            +{run.xp_reward} rescue XP · +{run.trust_reward} trust
          </p>
          <p className="text-muted text-sm">
            Scuttleclaw is recorded in your Dragon Book. Your rescue beacon is unlocked and this
            memory is saved in your journal.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link href="/dragon" className="text-accent underline">
              Decorate your habitat
            </Link>
            <Link href="/dragon-book/scuttleclaw" className="text-accent underline">
              Meet the Scuttleclaw
            </Link>
            <Link href="/train/flight" className="text-accent underline">
              Fly again
            </Link>
          </div>
        </section>
      )}
      {pending && !playing && (
        <p role="status" className="text-muted text-sm">
          Saving your progress…
        </p>
      )}
      {error && (
        <p role="alert" className="text-bad text-sm">
          {error.message}{" "}
          <Link href="/dragon#care" className="underline">
            Visit your dragon
          </Link>
        </p>
      )}
      <Link href="/dragon" className="text-muted inline-block text-sm underline">
        Return home · your progress is saved
      </Link>
    </div>
  );
}

export function AdventureHome() {
  return (
    <DragonGate title="Misty Cove" path="/adventure">
      {(dragon, userId) => <Mission dragon={dragon} userId={userId} />}
    </DragonGate>
  );
}

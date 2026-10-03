"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, useReducedMotion } from "motion/react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { Notice } from "@/components/quiz/notice";
import { api } from "@/lib/api/client";
import { myDragonQueryKey, type PlayerDragon } from "@/lib/dragon/my-dragon";
import {
  fetchTraining,
  historyKey,
  trainingKey,
  type TrainingActivity,
  type TrainingResult,
} from "@/lib/training/api";

import { DragonGate } from "./dragon-gate";
import { AccuracyGame } from "./games/accuracy-game";
import { FlightGame } from "./games/flight-game";
import { MemoryGame } from "./games/memory-game";
import { ObedienceGame } from "./games/obedience-game";
import { SpeedGame } from "./games/speed-game";
import type { GameProps } from "./games/use-timers";
import { XpBar } from "./train-home";

const GAMES: Record<string, (props: GameProps) => React.ReactNode> = {
  flight: FlightGame,
  speed: SpeedGame,
  accuracy: AccuracyGame,
  memory: MemoryGame,
  obedience: ObedienceGame,
};

const HOW_TO: Record<string, string> = {
  flight:
    "Fly through six glowing openings between the sea stacks. Arrow keys or Climb/Dive steer; Space climbs. Missing a gate costs points, but you can always finish.",
  speed: "After the count-in, press Flap on every beat as the circle swells. Twelve beats.",
  accuracy: "Click each square the moment it lights up. Ten targets.",
  memory: "Watch the signs, then repeat them in order. Each round adds one more.",
  obedience:
    "When a command appears, click the matching button as fast as you can. Eight commands.",
};

const primary = "bg-accent rounded-lg px-4 py-2 font-medium text-white disabled:opacity-60";

type Finished = { score: number; meta: Record<string, unknown>; durationMs: number };

/** Runs a game and reports how long it took, timed from when it appeared on screen. */
function TimedGame({
  Game,
  onFinish,
  dragon,
}: {
  Game: (props: GameProps) => React.ReactNode;
  onFinish: (result: Finished) => void;
  dragon: PlayerDragon;
}) {
  const shownAt = useRef(0);
  useEffect(() => {
    shownAt.current = performance.now();
  }, []);
  return (
    <Game
      speciesId={dragon.species_id}
      color={dragon.color_hex}
      agility={dragon.stats.find((s) => s.id === "agility")?.value}
      onFinish={(score, meta, activeDurationMs) =>
        onFinish({
          score,
          meta,
          durationMs: Math.round(activeDurationMs ?? performance.now() - shownAt.current),
        })
      }
    />
  );
}

/** The outcome of a session, with a small celebration for a level-up. */
function Result({
  result,
  dragon,
  activities,
  onAgain,
}: {
  result: TrainingResult;
  dragon: PlayerDragon;
  activities: TrainingActivity[];
  onAgain: () => void;
}) {
  const reduce = useReducedMotion();
  const levelled = result.level_ups.length > 0;
  const unlockedNames = result.new_activities.map(
    (id) => activities.find((a) => a.id === id)?.label ?? id,
  );
  return (
    <div className="space-y-6">
      {levelled && (
        <motion.div
          initial={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.6 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: "spring", duration: 0.6 }}
          className="bg-accent rounded-xl p-6 text-center text-white"
          role="status"
        >
          <p className="text-sm tracking-widest uppercase">Level up!</p>
          <p className="text-4xl font-semibold">Level {dragon.level}</p>
          {/* New activities come with a new stage. */}
          {unlockedNames.length > 0 && (
            <p className="mt-2">
              {dragon.name} is now {result.stage.label}. New: {unlockedNames.join(", ")}
            </p>
          )}
        </motion.div>
      )}
      <div className="bg-surface border-line space-y-4 rounded-xl border p-6">
        <p className="text-lg">{result.message}</p>
        <dl className="grid grid-cols-2 gap-3 text-center">
          <div>
            <dt className="text-muted text-sm">Score</dt>
            <dd className="text-2xl font-semibold">{result.score}</dd>
          </div>
          <div>
            <dt className="text-muted text-sm">XP</dt>
            <dd className="text-2xl font-semibold">+{result.xp_gained}</dd>
          </div>
        </dl>
        <ul className="space-y-1 text-sm">
          {result.stat_changes.map((c) => (
            <li key={c.id} className="flex justify-between">
              <span>{c.label}</span>
              <span>
                {c.value}{" "}
                <span className="text-muted">{c.delta > 0 ? `(+${c.delta})` : "(no change)"}</span>
              </span>
            </li>
          ))}
        </ul>
        <XpBar level={dragon.level} xp={dragon.xp} xpToNext={dragon.xp_to_next} />
      </div>
      <div className="flex flex-wrap gap-3">
        <button type="button" onClick={onAgain} className={primary}>
          Train again
        </button>
        <Link href="/train" className="border-line rounded-lg border px-4 py-2 font-medium">
          Back to training
        </Link>
      </div>
    </div>
  );
}

function Session({
  dragon,
  userId,
  activityId,
}: {
  dragon: PlayerDragon;
  userId: string;
  activityId: string;
}) {
  const queryClient = useQueryClient();
  const [phase, setPhase] = useState<"intro" | "playing" | "result">("intro");
  const sessionId = useRef<string | null>(null);

  const overview = useQuery({
    queryKey: trainingKey(dragon.id),
    queryFn: () => fetchTraining(dragon.id),
  });

  const start = useMutation({
    mutationFn: async () => {
      const { data, error } = await api.POST("/api/v1/dragons/{dragon_id}/training-sessions", {
        params: { path: { dragon_id: dragon.id } },
        body: { activity: activityId },
      });
      if (error || !data) throw new Error(error?.detail?.toString() ?? "Couldn't start");
      return data;
    },
    onSuccess: (session) => {
      sessionId.current = session.id;
      finish.reset();
      setPhase("playing");
    },
    // A refusal is logged and can change the mood.
    onError: () => queryClient.invalidateQueries({ queryKey: myDragonQueryKey(userId) }),
  });

  const finish = useMutation({
    mutationFn: async (r: Finished) => {
      const { data, error } = await api.POST("/api/v1/training-sessions/{session_id}/complete", {
        params: { path: { session_id: sessionId.current! } },
        body: {
          score: r.score,
          duration_ms: r.durationMs,
          meta: r.meta,
        },
      });
      if (error || !data) throw new Error(error?.detail?.toString() ?? "Couldn't save");
      return data;
    },
    onSuccess: (result) => {
      queryClient.setQueryData(myDragonQueryKey(userId), result.dragon);
      queryClient.invalidateQueries({ queryKey: trainingKey(dragon.id) });
      queryClient.invalidateQueries({ queryKey: historyKey(dragon.id) });
      queryClient.invalidateQueries({ queryKey: ["experience", dragon.id] });
    },
    onSettled: () => setPhase("result"),
  });

  const activity = overview.data?.activities.find((a) => a.id === activityId);
  const Game = GAMES[activityId];

  if (overview.isPending) return <Notice title="Training">Loading…</Notice>;
  if (!activity || !Game) {
    return (
      <Notice title="No such activity">
        <Link href="/train" className="text-accent underline">
          Back to training
        </Link>
      </Notice>
    );
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <header className="space-y-1">
        <p className="text-accent text-sm font-medium tracking-widest uppercase">
          Training · {activity.label}
        </p>
        <h1 className="text-2xl font-semibold tracking-tight">{activity.description}</h1>
      </header>

      {phase === "intro" && (
        <div className="space-y-4">
          <p className="text-muted">{HOW_TO[activityId]}</p>
          <p className="text-sm">
            Trains <span className="capitalize">{activity.trains.join(" and ")}</span> · costs{" "}
            {activity.energy_cost} energy · {dragon.name} is {dragon.mood.label.toLowerCase()}.
          </p>
          {!activity.unlocked && (
            <p className="text-muted">
              Unlocks at the {activity.unlocks_at.label} stage (level {activity.unlocks_at_level}).
            </p>
          )}
          <button
            type="button"
            onClick={() => start.mutate()}
            disabled={start.isPending || !activity.unlocked}
            className={primary}
          >
            {start.isPending ? "Starting…" : "Start"}
          </button>
          {start.isError && (
            <p role="alert" className="text-sm">
              {start.error.message}{" "}
              <Link href="/dragon" className="text-accent underline">
                Look after {dragon.name}
              </Link>
            </p>
          )}
        </div>
      )}

      {phase === "playing" &&
        (finish.isPending ? (
          <p className="text-muted text-center" role="status">
            Scoring…
          </p>
        ) : (
          <TimedGame Game={Game} dragon={dragon} onFinish={(r) => finish.mutate(r)} />
        ))}

      {phase === "result" &&
        (finish.data ? (
          <Result
            result={finish.data}
            dragon={finish.data.dragon}
            activities={overview.data?.activities ?? []}
            onAgain={() => setPhase("intro")}
          />
        ) : (
          <div className="space-y-3">
            <p role="alert">{finish.error?.message ?? "Something went wrong."}</p>
            <button type="button" onClick={() => setPhase("intro")} className={primary}>
              Try again
            </button>
          </div>
        ))}
    </div>
  );
}

export function TrainActivity({ activityId }: { activityId: string }) {
  return (
    <DragonGate title="Training" path={`/train/${activityId}`}>
      {(dragon, userId) => <Session dragon={dragon} userId={userId} activityId={activityId} />}
    </DragonGate>
  );
}

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";

import { Notice } from "@/components/quiz/notice";
import { QuizRunner, type RunnerWording } from "@/components/quiz/quiz-runner";
import { api } from "@/lib/api/client";
import {
  encounterAsQuiz,
  encounterStorageKey,
  toChoices,
  type QuizAttemptDetail,
} from "@/lib/quiz/encounter";
import { saveProgress } from "@/lib/quiz/progress";
import { useSession } from "@/lib/supabase/use-session";

import { MatchResult } from "./match-result";

const WORDING: RunnerWording = {
  step: "Scene",
  progress: "Encounter progress",
  submitting: "The dragon is deciding…",
};

function TakeTheQuiz({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Notice title={title}>
      <p>{children}</p>
      <Link href="/academy/quiz" className="text-accent underline">
        Take the quiz
      </Link>
    </Notice>
  );
}

/** Signed-in check → load the attempt and scenes → play them → show which dragon chose you. */
export function EncounterFlow({ attemptId }: { attemptId: string | null }) {
  const session = useSession();
  const signedIn = session.status === "signed-in";
  const queryClient = useQueryClient();
  const attemptKey = ["quiz-attempt", attemptId];

  const attempt = useQuery({
    queryKey: attemptKey,
    enabled: signedIn && attemptId !== null,
    queryFn: async (): Promise<QuizAttemptDetail | null> => {
      const { data, error, response } = await api.GET("/api/v1/quiz/attempts/{attempt_id}", {
        params: { path: { attempt_id: attemptId! } },
      });
      // Unknown, malformed or someone else's attempt.
      if (response.status === 404 || response.status === 422) return null;
      if (error || !data) throw new Error(`HTTP ${response.status}`);
      return data;
    },
  });

  const encounter = useQuery({
    queryKey: ["encounter", signedIn ? session.userId : null],
    enabled: signedIn && attempt.data?.match === null,
    // Options are shuffled per player; refetching mid-encounter must not change anything.
    staleTime: Infinity,
    queryFn: async () => {
      const { data, error, response } = await api.GET("/api/v1/encounter");
      if (error || !data) throw new Error(`HTTP ${response.status}`);
      return data;
    },
  });

  const submit = useMutation({
    mutationFn: async (answers: Record<string, string>) => {
      if (!encounter.data) throw new Error("Encounter not loaded");
      const { data, error } = await api.POST("/api/v1/quiz/attempts/{attempt_id}/encounter", {
        params: { path: { attempt_id: attemptId! } },
        body: toChoices(encounter.data, answers),
      });
      if (error || !data) throw new Error(error?.detail?.toString() ?? "Could not save choices");
      return data;
    },
    onSuccess: (detail) => {
      saveProgress(null, encounterStorageKey(attemptId!));
      queryClient.setQueryData(attemptKey, detail);
    },
    // E.g. already finished in another tab: reloading the attempt shows that result.
    onError: () => queryClient.invalidateQueries({ queryKey: attemptKey }),
  });

  if (attemptId === null) {
    return (
      <TakeTheQuiz title="Take the quiz first">
        The dragons need to know you before one steps out of the fog.
      </TakeTheQuiz>
    );
  }

  if (session.status === "loading") return <Notice title="Into the fog">…</Notice>;

  if (session.status === "signed-out") {
    const next = encodeURIComponent(`/academy/encounter?attempt=${attemptId}`);
    return (
      <Notice title="Into the fog">
        <p>Sign in to continue your encounter.</p>
        <Link
          href={`/login?next=${next}`}
          className="bg-accent inline-block rounded-lg px-4 py-2 font-medium text-white"
        >
          Sign in
        </Link>
      </Notice>
    );
  }

  if (attempt.isPending) return <Notice title="Into the fog">Loading…</Notice>;

  if (attempt.isError) {
    return (
      <Notice title="The encounter didn't load">
        <p>Is the API running? ({attempt.error.message})</p>
        <button type="button" onClick={() => attempt.refetch()} className="text-accent underline">
          Try again
        </button>
      </Notice>
    );
  }

  if (attempt.data === null) {
    return (
      <TakeTheQuiz title="We couldn't find that quiz">
        This link doesn&apos;t match one of your quiz attempts.
      </TakeTheQuiz>
    );
  }

  if (attempt.data.match) return <MatchResult match={attempt.data.match} />;

  if (encounter.isPending) return <Notice title="Into the fog">Loading…</Notice>;

  if (encounter.isError) {
    return (
      <Notice title="The encounter didn't load">
        <p>Is the API running? ({encounter.error.message})</p>
        <button type="button" onClick={() => encounter.refetch()} className="text-accent underline">
          Try again
        </button>
      </Notice>
    );
  }

  return (
    <div className="space-y-4">
      <QuizRunner
        quiz={encounterAsQuiz(encounter.data)}
        submitting={submit.isPending}
        onComplete={(answers) => submit.mutate(answers)}
        storageKey={encounterStorageKey(attemptId)}
        wording={WORDING}
      />
      {submit.isError && (
        <p role="alert" className="text-bad mx-auto max-w-xl text-sm">
          {submit.error.message}{" "}
          <button type="button" onClick={() => submit.reset()} className="underline">
            Dismiss
          </button>
        </p>
      )}
    </div>
  );
}

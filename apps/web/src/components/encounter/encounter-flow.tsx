"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { AttemptGate } from "@/components/quiz/attempt-gate";
import { Notice } from "@/components/quiz/notice";
import { QuizRunner, type RunnerWording } from "@/components/quiz/quiz-runner";
import { api } from "@/lib/api/client";
import {
  attemptQueryKey,
  encounterAsQuiz,
  encounterStorageKey,
  revealPath,
  toChoices,
  type QuizAttemptDetail,
} from "@/lib/quiz/encounter";
import { saveProgress } from "@/lib/quiz/progress";

const WORDING: RunnerWording = {
  step: "Scene",
  progress: "Encounter progress",
  submitting: "The dragon is deciding…",
};

/** The three scenes for an unfinished attempt; a finished one goes straight to its reveal. */
function Scenes({ attempt }: { attempt: QuizAttemptDetail }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const done = attempt.match !== null;

  useEffect(() => {
    if (done) router.replace(revealPath(attempt.id));
  }, [done, attempt.id, router]);

  const encounter = useQuery({
    queryKey: ["encounter", attempt.id],
    enabled: !done,
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
        params: { path: { attempt_id: attempt.id } },
        body: toChoices(encounter.data, answers),
      });
      if (error || !data) throw new Error(error?.detail?.toString() ?? "Could not save choices");
      return data;
    },
    // The cached attempt now has its match, so the redirect above takes over.
    onSuccess: (detail) => {
      saveProgress(null, encounterStorageKey(attempt.id));
      queryClient.setQueryData(attemptQueryKey(attempt.id), detail);
    },
    // E.g. already finished in another tab: reloading the attempt shows that result.
    onError: () => queryClient.invalidateQueries({ queryKey: attemptQueryKey(attempt.id) }),
  });

  if (done) return <Notice title="It's decided">…</Notice>;

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
        storageKey={encounterStorageKey(attempt.id)}
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

export function EncounterFlow({ attemptId }: { attemptId: string | null }) {
  return (
    <AttemptGate attemptId={attemptId} title="Into the fog" path="/academy/encounter">
      {(attempt) => <Scenes attempt={attempt} />}
    </AttemptGate>
  );
}

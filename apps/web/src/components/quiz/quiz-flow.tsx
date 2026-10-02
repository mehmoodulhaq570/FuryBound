"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { api } from "@/lib/api/client";
import { saveProgress, type QuizAttempt } from "@/lib/quiz/progress";
import { useSession } from "@/lib/supabase/use-session";

import { Notice } from "./notice";
import { QuizRunner } from "./quiz-runner";
import { TraitBars } from "./trait-bars";

/** Signed-in check → load the quiz → run it → submit the answers → show the trait scores. */
export function QuizFlow() {
  const session = useSession();
  const signedIn = session.status === "signed-in";

  const quiz = useQuery({
    queryKey: ["quiz", signedIn ? session.userId : null],
    enabled: signedIn,
    // Options are shuffled per player; refetching mid-quiz must not change anything.
    staleTime: Infinity,
    queryFn: async () => {
      const { data, error, response } = await api.GET("/api/v1/quiz");
      if (error || !data) throw new Error(`HTTP ${response.status}`);
      return data;
    },
  });

  const submit = useMutation({
    mutationFn: async (answers: Record<string, string>): Promise<QuizAttempt> => {
      if (!quiz.data) throw new Error("Quiz not loaded");
      const { data, error } = await api.POST("/api/v1/quiz/attempts", {
        body: { quiz_version: quiz.data.version, answers },
      });
      if (error || !data) throw new Error(error?.detail?.toString() ?? "Could not save answers");
      return data;
    },
    onSuccess: () => saveProgress(null),
  });

  if (session.status === "loading") return <Notice title="Finding your dragon">…</Notice>;

  if (session.status === "signed-out") {
    return (
      <Notice title="Find your dragon">
        <p>Sign in first, so your dragon can find you again next time.</p>
        <Link
          href="/login?next=/academy/quiz"
          className="bg-accent inline-block rounded-lg px-4 py-2 font-medium text-white"
        >
          Sign in to start
        </Link>
      </Notice>
    );
  }

  if (quiz.isPending) return <Notice title="Finding your dragon">Loading the quiz…</Notice>;

  if (quiz.isError) {
    return (
      <Notice title="The quiz didn't load">
        <p>Is the API running? ({quiz.error.message})</p>
        <button type="button" onClick={() => quiz.refetch()} className="text-accent underline">
          Try again
        </button>
      </Notice>
    );
  }

  if (submit.isSuccess) {
    return (
      <div className="mx-auto max-w-xl space-y-8">
        <div className="space-y-2">
          <p className="text-accent text-sm font-medium tracking-widest uppercase">Quiz done</p>
          <h1 className="text-2xl font-semibold tracking-tight">This is how the dragons see you</h1>
          <p className="text-muted">
            Next, a dragon steps out of the fog. How you meet it decides which one chooses you.
          </p>
        </div>
        <TraitBars traits={submit.data.traits} />
        <Link
          href={`/academy/encounter?attempt=${submit.data.id}`}
          className="bg-accent block w-full rounded-lg px-4 py-2 text-center font-medium text-white"
        >
          Step into the fog
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <QuizRunner
        quiz={quiz.data}
        submitting={submit.isPending}
        onComplete={(answers) => submit.mutate(answers)}
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

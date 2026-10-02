"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { api } from "@/lib/api/client";
import { attemptQueryKey, type QuizAttemptDetail } from "@/lib/quiz/encounter";
import { useSession } from "@/lib/supabase/use-session";

import { Notice } from "./notice";

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

/**
 * The checks every page after the quiz needs: an attempt id in the URL, a signed-in player,
 * and an attempt that belongs to them. Renders `children` with the attempt once all pass.
 */
export function AttemptGate({
  attemptId,
  title,
  path,
  children,
}: {
  attemptId: string | null;
  title: string;
  /** This page, to come back to after signing in. */
  path: string;
  children: (attempt: QuizAttemptDetail) => React.ReactNode;
}) {
  const session = useSession();

  const attempt = useQuery({
    queryKey: attemptQueryKey(attemptId),
    enabled: session.status === "signed-in" && attemptId !== null,
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

  if (attemptId === null) {
    return (
      <TakeTheQuiz title="Take the quiz first">
        The dragons need to know you before one steps out of the fog.
      </TakeTheQuiz>
    );
  }

  if (session.status === "loading") return <Notice title={title}>…</Notice>;

  if (session.status === "signed-out") {
    const next = encodeURIComponent(`${path}?attempt=${attemptId}`);
    return (
      <Notice title={title}>
        <p>Sign in to carry on where you left off.</p>
        <Link
          href={`/login?next=${next}`}
          className="bg-accent inline-block rounded-lg px-4 py-2 font-medium text-white"
        >
          Sign in
        </Link>
      </Notice>
    );
  }

  if (attempt.isPending) return <Notice title={title}>Loading…</Notice>;

  if (attempt.isError) {
    return (
      <Notice title="This page didn't load">
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

  return children(attempt.data);
}

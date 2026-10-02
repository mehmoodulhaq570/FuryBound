"use client";

import { useReducedMotion } from "motion/react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { AttemptGate } from "@/components/quiz/attempt-gate";
import { Notice } from "@/components/quiz/notice";
import { hasSeenReveal, markRevealSeen, type QuizAttemptDetail } from "@/lib/quiz/encounter";

import { NameDragon } from "./name-dragon";
import { Reveal } from "./reveal";

function RevealOrRedirect({ attempt }: { attempt: QuizAttemptDetail }) {
  const router = useRouter();
  const reduceMotion = useReducedMotion() ?? false;
  // Read once: marking it seen at the end of this visit must not cut the animation short.
  const [seen] = useState(() => hasSeenReveal(attempt.id));
  const { match } = attempt;
  const onSeen = useCallback(() => markRevealSeen(attempt.id), [attempt.id]);

  // No dragon yet: the encounter isn't done.
  useEffect(() => {
    if (!match) router.replace(`/academy/encounter?attempt=${attempt.id}`);
  }, [match, attempt.id, router]);

  if (!match) return <Notice title="Into the fog">…</Notice>;

  return (
    <Reveal
      attempt={attempt}
      match={match}
      reduceMotion={reduceMotion}
      seen={seen}
      onSeen={onSeen}
      naming={<NameDragon attemptId={attempt.id} speciesName={match.top.name} />}
    />
  );
}

export function RevealFlow({ attemptId }: { attemptId: string | null }) {
  return (
    <AttemptGate attemptId={attemptId} title="The dragon chooses" path="/academy/reveal">
      {(attempt) => <RevealOrRedirect attempt={attempt} />}
    </AttemptGate>
  );
}

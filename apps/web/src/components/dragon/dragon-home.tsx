"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { Notice } from "@/components/quiz/notice";
import { fetchMyDragon, myDragonQueryKey } from "@/lib/dragon/my-dragon";
import { useSession } from "@/lib/supabase/use-session";

import { CarePanel } from "./care-panel";
import { DragonCard } from "./dragon-card";

/** Signed-in check → the player's dragon, or a nudge to go and find one. */
export function DragonHome() {
  const session = useSession();
  const userId = session.status === "signed-in" ? session.userId : null;

  const dragon = useQuery({
    queryKey: myDragonQueryKey(userId),
    enabled: userId !== null,
    queryFn: fetchMyDragon,
  });

  if (session.status === "loading") return <Notice title="Your dragon">…</Notice>;

  if (session.status === "signed-out") {
    return (
      <Notice title="Your dragon">
        <p>Sign in to see your dragon.</p>
        <Link
          href="/login?next=/dragon"
          className="bg-accent inline-block rounded-lg px-4 py-2 font-medium text-white"
        >
          Sign in
        </Link>
      </Notice>
    );
  }

  if (dragon.isPending) return <Notice title="Your dragon">Loading…</Notice>;

  if (dragon.isError) {
    return (
      <Notice title="Your dragon didn't load">
        <p>Is the API running? ({dragon.error.message})</p>
        <button type="button" onClick={() => dragon.refetch()} className="text-accent underline">
          Try again
        </button>
      </Notice>
    );
  }

  if (dragon.data === null) {
    return (
      <Notice title="No dragon yet">
        <p>Take the quiz and meet the dragons. One of them will choose you.</p>
        <Link
          href="/academy/quiz"
          className="bg-accent inline-block rounded-lg px-4 py-2 font-medium text-white"
        >
          Find your dragon
        </Link>
      </Notice>
    );
  }

  return (
    <DragonCard
      dragon={dragon.data}
      care={userId && <CarePanel dragon={dragon.data} userId={userId} />}
    />
  );
}

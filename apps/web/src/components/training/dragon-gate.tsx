"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { Notice } from "@/components/quiz/notice";
import { fetchMyDragon, myDragonQueryKey, type PlayerDragon } from "@/lib/dragon/my-dragon";
import { useSession } from "@/lib/supabase/use-session";

/** Signed in and has a dragon? Then render `children` with it; otherwise say what's missing. */
export function DragonGate({
  title,
  path,
  children,
}: {
  title: string;
  /** This page, to come back to after signing in. */
  path: string;
  children: (dragon: PlayerDragon, userId: string) => React.ReactNode;
}) {
  const session = useSession();
  const userId = session.status === "signed-in" ? session.userId : null;
  const dragon = useQuery({
    queryKey: myDragonQueryKey(userId),
    enabled: userId !== null,
    queryFn: fetchMyDragon,
  });

  if (session.status === "loading") return <Notice title={title}>…</Notice>;
  if (session.status === "signed-out") {
    return (
      <Notice title={title}>
        <p>Sign in to train your dragon.</p>
        <Link
          href={`/login?next=${encodeURIComponent(path)}`}
          className="bg-accent inline-block rounded-lg px-4 py-2 font-medium text-white"
        >
          Sign in
        </Link>
      </Notice>
    );
  }
  if (dragon.isPending) return <Notice title={title}>Loading…</Notice>;
  if (dragon.isError) {
    return (
      <Notice title="This page didn't load">
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
        <p>Find your dragon first; then you can train it.</p>
        <Link
          href="/academy/quiz"
          className="bg-accent inline-block rounded-lg px-4 py-2 font-medium text-white"
        >
          Find your dragon
        </Link>
      </Notice>
    );
  }
  return children(dragon.data, userId!);
}

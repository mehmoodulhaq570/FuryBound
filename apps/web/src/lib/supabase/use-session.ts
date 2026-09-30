"use client";

import { useEffect, useState } from "react";

import { createClient } from "./client";

export type SessionState =
  | { status: "loading" }
  | { status: "signed-out" }
  | { status: "signed-in"; userId: string; email: string | undefined };

/** Tracks the Supabase auth session in the browser. */
export function useSession(): SessionState {
  const [state, setState] = useState<SessionState>({ status: "loading" });

  useEffect(() => {
    const supabase = createClient();
    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      setState(
        session
          ? { status: "signed-in", userId: session.user.id, email: session.user.email }
          : { status: "signed-out" },
      );
    });
    return () => data.subscription.unsubscribe();
  }, []);

  return state;
}

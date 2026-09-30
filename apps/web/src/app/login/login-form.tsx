"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { createClient } from "@/lib/supabase/client";
import { useSession } from "@/lib/supabase/use-session";

// Placeholder email + password form for Phase 0. The plan's Supabase Auth UI
// (magic link / OAuth) replaces this once the product flow exists.
export function LoginForm() {
  const router = useRouter();
  const session = useSession();
  const [mode, setMode] = useState<"sign-in" | "sign-up">("sign-in");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const credentials = {
      email: String(form.get("email")),
      password: String(form.get("password")),
    };

    setBusy(true);
    setError(null);
    const supabase = createClient();
    const { error } =
      mode === "sign-in"
        ? await supabase.auth.signInWithPassword(credentials)
        : await supabase.auth.signUp(credentials);
    setBusy(false);

    if (error) {
      setError(error.message);
      return;
    }
    router.push("/");
    router.refresh();
  }

  async function signOut() {
    await createClient().auth.signOut();
    router.refresh();
  }

  if (session.status === "signed-in") {
    return (
      <div className="space-y-4">
        <p className="text-muted">Signed in as {session.email ?? session.userId}.</p>
        <button
          type="button"
          onClick={signOut}
          className="border-line hover:bg-surface rounded-lg border px-4 py-2"
        >
          Sign out
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <label className="block space-y-1">
        <span className="text-sm font-medium">Email</span>
        <input
          name="email"
          type="email"
          required
          autoComplete="email"
          className="border-line bg-surface w-full rounded-lg border px-3 py-2"
        />
      </label>
      <label className="block space-y-1">
        <span className="text-sm font-medium">Password</span>
        <input
          name="password"
          type="password"
          required
          minLength={6}
          autoComplete={mode === "sign-in" ? "current-password" : "new-password"}
          className="border-line bg-surface w-full rounded-lg border px-3 py-2"
        />
      </label>

      {error && (
        <p role="alert" className="text-bad text-sm">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={busy}
        className="bg-accent w-full rounded-lg px-4 py-2 font-medium text-white disabled:opacity-60"
      >
        {busy ? "…" : mode === "sign-in" ? "Sign in" : "Create account"}
      </button>

      <button
        type="button"
        onClick={() => setMode(mode === "sign-in" ? "sign-up" : "sign-in")}
        className="text-muted hover:text-foreground w-full text-sm"
      >
        {mode === "sign-in" ? "No account? Create one" : "Have an account? Sign in"}
      </button>
    </form>
  );
}

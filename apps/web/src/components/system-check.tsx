"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api/client";
import { useSession } from "@/lib/supabase/use-session";

type Status = "pending" | "ok" | "error" | "skipped";

function Row({ label, status, detail }: { label: string; status: Status; detail: string }) {
  const dot = {
    pending: "bg-muted animate-pulse",
    ok: "bg-ok",
    error: "bg-bad",
    skipped: "bg-line",
  }[status];

  return (
    <li className="flex items-start gap-3 py-3">
      <span className={`mt-1.5 size-2.5 shrink-0 rounded-full ${dot}`} aria-hidden />
      <div className="min-w-0">
        <p className="font-medium">
          {label} <span className="sr-only">({status})</span>
        </p>
        <p className="text-muted font-mono text-sm break-words">{detail}</p>
      </div>
    </li>
  );
}

export function SystemCheck() {
  const session = useSession();

  const health = useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/health");
      if (error || !data) throw new Error("API did not respond");
      return data;
    },
    retry: false,
  });

  const signedIn = session.status === "signed-in";
  const me = useQuery({
    queryKey: ["me", signedIn ? session.userId : null],
    enabled: signedIn,
    queryFn: async () => {
      const { data, error, response } = await api.GET("/api/v1/me");
      if (error || !data) throw new Error(`HTTP ${response.status}`);
      return data;
    },
    retry: false,
  });

  const healthStatus: Status = health.isPending ? "pending" : health.isSuccess ? "ok" : "error";
  const authStatus: Status = session.status === "loading" ? "pending" : signedIn ? "ok" : "skipped";
  const meStatus: Status = !signedIn
    ? "skipped"
    : me.isPending
      ? "pending"
      : me.isSuccess
        ? "ok"
        : "error";

  return (
    <section className="border-line bg-surface rounded-xl border p-5">
      <h2 className="text-lg font-semibold">System check</h2>
      <ul className="divide-line divide-y">
        <Row
          label="API reachable"
          status={healthStatus}
          detail={health.isSuccess ? "GET /api/v1/health → ok" : (health.error?.message ?? "…")}
        />
        <Row
          label="Signed in with Supabase"
          status={authStatus}
          detail={
            signedIn ? (session.email ?? session.userId) : "Not signed in. Use Sign in above."
          }
        />
        <Row
          label="Protected API route"
          status={meStatus}
          detail={
            me.isSuccess
              ? `GET /api/v1/me → ${me.data.id}`
              : signedIn
                ? (me.error?.message ?? "…")
                : "Needs a signed-in user."
          }
        />
      </ul>
    </section>
  );
}

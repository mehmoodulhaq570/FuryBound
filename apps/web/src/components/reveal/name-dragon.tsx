"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useId, useState } from "react";

import { api } from "@/lib/api/client";
import { fetchMyDragon, myDragonQueryKey } from "@/lib/dragon/my-dragon";
import { NAME_LENGTH, nameProblem } from "@/lib/dragon/name";
import { useSession } from "@/lib/supabase/use-session";

/** Name the dragon that chose you, which adopts it. Players who already have one get a link. */
export function NameDragon({ attemptId, speciesName }: { attemptId: string; speciesName: string }) {
  const session = useSession();
  const userId = session.status === "signed-in" ? session.userId : null;
  const router = useRouter();
  const queryClient = useQueryClient();
  const inputId = useId();
  const [name, setName] = useState("");
  const [touched, setTouched] = useState(false);

  const mine = useQuery({
    queryKey: myDragonQueryKey(userId),
    enabled: userId !== null,
    queryFn: fetchMyDragon,
  });

  const adopt = useMutation({
    mutationFn: async () => {
      const { data, error } = await api.POST("/api/v1/dragons", {
        body: { attempt_id: attemptId, name },
      });
      if (error || !data) throw new Error(error?.detail?.toString() ?? "Could not adopt");
      return data;
    },
    onSuccess: (dragon) => {
      queryClient.setQueryData(myDragonQueryKey(userId), dragon);
      router.push("/dragon");
    },
  });

  if (mine.isPending) return null;

  if (mine.data) {
    return (
      <Link
        href="/dragon"
        className="bg-accent block w-full rounded-lg px-4 py-2 text-center font-medium text-white"
      >
        Visit {mine.data.name}
      </Link>
    );
  }

  const problem = nameProblem(name);
  const shown = touched ? problem : null;
  const error = shown ?? (adopt.isError ? adopt.error.message : null);

  return (
    <form
      className="space-y-2"
      onSubmit={(e) => {
        e.preventDefault();
        setTouched(true);
        if (!problem) adopt.mutate();
      }}
    >
      <label htmlFor={inputId} className="block font-medium">
        Name your {speciesName}
      </label>
      <div className="flex gap-2">
        <input
          id={inputId}
          value={name}
          maxLength={NAME_LENGTH.max}
          autoComplete="off"
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${inputId}-error` : undefined}
          onChange={(e) => {
            setName(e.target.value);
            adopt.reset();
          }}
          onBlur={() => setTouched(name !== "")}
          className="bg-background border-line focus-visible:outline-accent min-w-0 flex-1 rounded-lg border px-3 py-2"
        />
        <button
          type="submit"
          disabled={adopt.isPending}
          className="bg-accent rounded-lg px-4 py-2 font-medium text-white disabled:opacity-60"
        >
          {adopt.isPending ? "Naming…" : "Name"}
        </button>
      </div>
      {error && (
        <p id={`${inputId}-error`} role="alert" className="text-bad text-sm">
          {error}
        </p>
      )}
    </form>
  );
}

"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";

import { api } from "@/lib/api/client";
import type { Academy } from "@/lib/dragon-book/academy";
import type { DragonCard, Movie } from "@/lib/dragon-book/types";
import { useSession } from "@/lib/supabase/use-session";

import { DragonBook } from "./dragon-book";

/** The Dragon Book, in Academy mode for signed-in players (full reference otherwise). */
export function AcademyBook({ cards, movies }: { cards: DragonCard[]; movies: Movie[] }) {
  const session = useSession();
  const userId = session.status === "signed-in" ? session.userId : null;

  const discoveries = useQuery({
    queryKey: ["discoveries", userId],
    enabled: userId !== null,
    queryFn: async () => {
      const { data, error, response } = await api.GET("/api/v1/discoveries");
      if (error || !data) throw new Error(`HTTP ${response.status}`);
      return data;
    },
  });

  const academy = useMemo<Academy | null>(() => {
    // If the API can't be reached, the full book is still useful.
    if (!userId || !discoveries.data) return null;
    return {
      discovered: new Map(
        discoveries.data
          .filter((d) => d.entity_kind === "species")
          .map((d) => [d.entity_id, d.discovered_at]),
      ),
    };
  }, [userId, discoveries.data]);

  return <DragonBook cards={cards} movies={movies} academy={academy} />;
}

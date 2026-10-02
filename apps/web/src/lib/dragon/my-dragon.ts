import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

export type PlayerDragon = components["schemas"]["PlayerDragon"];
export type Labelled = components["schemas"]["Labelled"];

export function myDragonQueryKey(userId: string | null) {
  return ["my-dragon", userId] as const;
}

/** The player's dragon, or null if they haven't adopted one yet. */
export async function fetchMyDragon(): Promise<PlayerDragon | null> {
  const { data, error, response } = await api.GET("/api/v1/dragons/me");
  if (response.status === 404) return null;
  if (error || !data) throw new Error(`HTTP ${response.status}`);
  return data;
}

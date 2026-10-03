import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

export type IslandState = components["schemas"]["IslandState"];
export type HabitatLayout = components["schemas"]["HabitatLayout"];
export const islandKey = (id: string) => ["island", id] as const;

export async function fetchIsland(id: string) {
  const { data, error } = await api.GET("/api/v1/dragons/{dragon_id}/island", {
    params: { path: { dragon_id: id } },
  });
  if (error || !data) throw new Error("Couldn't open your island. Try again.");
  return data;
}

export async function collectTreasure(id: string, treasure: string) {
  const { data, error } = await api.POST("/api/v1/dragons/{dragon_id}/treasures/{treasure}", {
    params: { path: { dragon_id: id, treasure } },
  });
  if (error || !data) throw new Error(error?.detail?.toString() ?? "Couldn't save this keepsake");
  return data;
}

export async function saveLayout(id: string, layout: HabitatLayout) {
  const { data, error } = await api.POST("/api/v1/dragons/{dragon_id}/habitat-layout", {
    params: { path: { dragon_id: id } },
    body: layout,
  });
  if (error || !data)
    throw new Error(error?.detail?.toString() ?? "Couldn't save your arrangement");
  return data;
}

import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

export type Experience = components["schemas"]["Experience"];
export type AdventureState = components["schemas"]["AdventureState"];
export type AdventureChoice = components["schemas"]["AdventureChoice"]["choice"];
export type Decoration = components["schemas"]["DecorationChoice"]["decoration"];
export const experienceKey = (dragonId: string) => ["experience", dragonId] as const;

export async function fetchExperience(dragonId: string): Promise<Experience> {
  const { data, error, response } = await api.GET("/api/v1/dragons/{dragon_id}/experience", {
    params: { path: { dragon_id: dragonId } },
  });
  if (error || !data) throw new Error(`Couldn't load your adventures (HTTP ${response.status})`);
  return data;
}

export async function setDecoration(dragonId: string, decoration: Decoration): Promise<Experience> {
  const { data, error } = await api.POST("/api/v1/dragons/{dragon_id}/decoration", {
    params: { path: { dragon_id: dragonId } },
    body: { decoration },
  });
  if (error || !data) throw new Error(error?.detail?.toString() ?? "Couldn't change the habitat");
  return data;
}

export async function startAdventure(dragonId: string): Promise<AdventureState> {
  const { data, error } = await api.POST("/api/v1/dragons/{dragon_id}/adventure", {
    params: { path: { dragon_id: dragonId } },
  });
  if (error || !data) throw new Error(error?.detail?.toString() ?? "Couldn't start the rescue");
  return data;
}

export async function chooseAdventure(
  dragonId: string,
  runId: string,
  choice: AdventureChoice,
): Promise<AdventureState> {
  const { data, error } = await api.POST("/api/v1/dragons/{dragon_id}/adventure/{run_id}/choice", {
    params: { path: { dragon_id: dragonId, run_id: runId } },
    body: { choice },
  });
  if (error || !data) throw new Error(error?.detail?.toString() ?? "Couldn't save your choice");
  return data;
}

import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

export type TrainingOverview = components["schemas"]["TrainingOverview"];
export type TrainingActivity = components["schemas"]["TrainingActivity"];
export type TrainingResult = components["schemas"]["TrainingResult"];

export const trainingKey = (dragonId: string | null) => ["training", dragonId] as const;
export const historyKey = (dragonId: string | null) => ["training-history", dragonId] as const;

export async function fetchTraining(dragonId: string): Promise<TrainingOverview> {
  const { data, error, response } = await api.GET("/api/v1/dragons/{dragon_id}/training", {
    params: { path: { dragon_id: dragonId } },
  });
  if (error || !data) throw new Error(`HTTP ${response.status}`);
  return data;
}

export async function fetchHistory(dragonId: string) {
  const { data, error, response } = await api.GET("/api/v1/dragons/{dragon_id}/history", {
    params: { path: { dragon_id: dragonId } },
  });
  if (error || !data) throw new Error(`HTTP ${response.status}`);
  return data;
}

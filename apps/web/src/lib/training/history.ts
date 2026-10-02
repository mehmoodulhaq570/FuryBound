import type { components } from "@/lib/api/schema";

export type HistoryEntry = components["schemas"]["HistoryEntry"];
export type StatPoint = { label: string; value: number };

/**
 * One stat over time: where it started (before the first session), then its value after
 * each session. Stats a session didn't change keep their value.
 */
export function statSeries(history: HistoryEntry[], stat: string): StatPoint[] {
  if (history.length === 0) return [];
  const first = history[0];
  const start = (first.stats_after[stat] ?? 0) - (first.stat_deltas[stat] ?? 0);
  return [
    { label: "Start", value: start },
    ...history.map((h) => ({
      label: new Date(h.completed_at).toLocaleString(undefined, {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      }),
      value: h.stats_after[stat] ?? start,
    })),
  ];
}

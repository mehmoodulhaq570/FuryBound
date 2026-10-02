import { describe, expect, it } from "vitest";

import { statSeries, type HistoryEntry } from "./history";

const entry = (deltas: Record<string, number>, after: Record<string, number>): HistoryEntry => ({
  id: crypto.randomUUID(),
  activity: "flight",
  completed_at: "2026-10-05T10:00:00Z",
  score: 80,
  xp_gained: 68,
  stat_deltas: deltas,
  stats_after: after,
});

describe("statSeries", () => {
  it("starts from the value before the first session", () => {
    const history = [
      entry({ speed: 3 }, { speed: 33, firepower: 20 }),
      entry({ firepower: 2 }, { speed: 33, firepower: 22 }),
    ];
    expect(statSeries(history, "speed").map((p) => p.value)).toEqual([30, 33, 33]);
    expect(statSeries(history, "firepower").map((p) => p.value)).toEqual([20, 20, 22]);
    expect(statSeries(history, "speed")[0].label).toBe("Start");
  });

  it("is empty without training", () => {
    expect(statSeries([], "speed")).toEqual([]);
  });
});

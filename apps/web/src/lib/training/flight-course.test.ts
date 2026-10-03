import { describe, expect, it } from "vitest";

import { courseScore, steer } from "./flight-course";

describe("Flight course", () => {
  it("never gives negative points for missed gates, or more than 100 for perfect ones", () => {
    expect(courseScore([0, 0, 0])).toBe(100);
    expect(courseScore([0.9, -0.9])).toBe(0);
    expect(courseScore([0, 0.9])).toBe(50);
    expect(courseScore([])).toBe(0);
  });
  it("rewards a more accurate line and keeps steering inside the playable sky", () => {
    expect(courseScore([0.04, -0.05])).toBeGreaterThan(courseScore([0.2, -0.25]));
    expect(steer(0.14, -1)).toBe(0.14);
    expect(steer(0.86, 1)).toBe(0.86);
    expect(steer(0.5, -1)).toBe(0.4);
  });
});

import { describe, expect, it } from "vitest";

import {
  accuracyScore,
  flightScore,
  markerPosition,
  memoryScore,
  obedienceScore,
  rhythmScore,
} from "./scoring";

describe("flight", () => {
  it("rewards presses near the middle of the zone", () => {
    expect(flightScore([0, 0, 0])).toBe(100);
    expect(flightScore([0.125])).toBe(50);
    expect(flightScore([0.4, -0.3])).toBe(0);
    expect(flightScore([])).toBe(0);
  });

  it("sweeps the marker across and back", () => {
    expect(markerPosition(0, 1000)).toBe(0);
    expect(markerPosition(250, 1000)).toBe(0.5);
    expect(markerPosition(500, 1000)).toBe(1);
    expect(markerPosition(750, 1000)).toBe(0.5);
  });
});

describe("speed (rhythm)", () => {
  const beats = [600, 1200, 1800];

  it("scores taps on the beat", () => {
    expect(rhythmScore(beats, [600, 1200, 1800])).toBe(100);
    expect(rhythmScore(beats, [750, 1350, 1950])).toBe(50);
  });

  it("gives nothing for missed beats, and doesn't reward mashing", () => {
    expect(rhythmScore(beats, [])).toBe(0);
    expect(rhythmScore(beats, [600])).toBe(33);
    // One tap can't count for two beats.
    expect(rhythmScore([600, 650], [620])).toBe(47);
  });
});

describe("accuracy", () => {
  it("weighs hits by speed and misses as zero", () => {
    expect(accuracyScore([0, 0], 1000)).toBe(100);
    expect(accuracyScore([1000, null], 1000)).toBe(25);
  });
});

describe("memory", () => {
  it("scales the longest sequence remembered", () => {
    expect(memoryScore(2, 3, 8)).toBe(0);
    expect(memoryScore(3, 3, 8)).toBe(17);
    expect(memoryScore(8, 3, 8)).toBe(100);
  });
});

describe("obedience", () => {
  it("rewards quick right answers", () => {
    expect(obedienceScore([{ correct: true, ms: 0 }], 2000)).toBe(100);
    expect(obedienceScore([{ correct: true, ms: 2000 }], 2000)).toBe(50);
    expect(obedienceScore([{ correct: false, ms: 100 }], 2000)).toBe(0);
  });
});

import { describe, expect, it } from "vitest";

import { nameProblem } from "./name";

describe("nameProblem", () => {
  it.each(["Toothless", "  Ember  Wing ", "O'Malley", "Sky-Fang", "Åsa"])("accepts %j", (name) => {
    expect(nameProblem(name)).toBeNull();
  });

  it.each([
    ["", "characters"],
    ["A", "characters"],
    ["A".repeat(21), "characters"],
    ["R2D2", "letters"],
    ["Fang!", "letters"],
    ["Sky--Fang", "letters"],
  ])("refuses %j", (name, reason) => {
    expect(nameProblem(name)).toContain(reason);
  });
});

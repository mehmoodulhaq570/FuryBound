import { describe, expect, it } from "vitest";

import { BUILDS, shapeOf } from "./shapes";

const fingerprint = (id: string | null) => JSON.stringify(shapeOf(id));

describe("species shapes", () => {
  it("draws every matchable species differently", () => {
    const shapes = Object.keys(BUILDS).map(fingerprint);
    expect(new Set(shapes).size).toBe(shapes.length);
  });

  it("falls back to a generic dragon for other species", () => {
    expect(fingerprint("thunderdrum")).toBe(fingerprint(null));
    expect(fingerprint("thunderdrum")).not.toBe(fingerprint("night_fury"));
  });

  it("only uses well-formed paths", () => {
    for (const id of [...Object.keys(BUILDS), null]) {
      const { left, center } = shapeOf(id);
      for (const d of [...left, ...center]) expect(d).toMatch(/^M[\d.\s\-a-zA-Z]+Z$/);
    }
  });
});

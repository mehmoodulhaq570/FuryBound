import { existsSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import dragons from "@data/dragons.json";

import { speciesImage } from "./images";
import ids from "./species-images.json";

describe("species artwork", () => {
  it("has a file for every listed species, and only species are listed", () => {
    const species = new Set(dragons.filter((d) => d.kind === "species").map((d) => d.id));
    for (const id of ids) {
      expect(species.has(id)).toBe(true);
      expect(existsSync(join(process.cwd(), "public", "dragons", `${id}.webp`))).toBe(true);
    }
  });

  it("points at the image, or null without one", () => {
    expect(speciesImage("night_fury")).toBe("/dragons/night_fury.webp");
    expect(speciesImage("toothless")).toBeNull(); // named dragons use their species' art
    expect(speciesImage(null)).toBeNull();
  });
});

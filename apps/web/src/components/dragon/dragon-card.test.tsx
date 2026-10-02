import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { PlayerDragon } from "@/lib/dragon/my-dragon";

import { DragonCard } from "./dragon-card";

const dragon: PlayerDragon = {
  id: "d1",
  name: "Ember",
  species_id: "deadly_nadder",
  species_name: "Deadly Nadder",
  rarity: "common",
  compatibility: 91,
  color_variant: "sky blue",
  color_hex: "#4a90c8",
  personality: [{ id: "courage", label: "Courage", value: 72 }],
  stats: [{ id: "speed", label: "Speed", value: 33 }],
  needs: [
    { id: "hunger", label: "Hunger", value: 30 },
    { id: "energy", label: "Energy", value: 80 },
    { id: "happiness", label: "Happiness", value: 60 },
  ],
  mood: { id: "hungry", label: "Hungry" },
  thought: "Ember keeps sniffing your satchel.",
  foods: ["fish", "eel"],
  quirks: [{ id: "hoards_shiny", label: "Hoards shiny things" }],
  likes: ["chicken", "shiny things"],
  dislikes: ["eel"],
  trust: 20,
  level: 1,
  xp: 0,
  xp_to_next: 100,
  stage: "newborn",
  stage_label: "Newborn",
  created_at: "2026-10-02T12:00:00Z",
};

const meter = (name: string) => screen.getByRole("meter", { name }).getAttribute("aria-valuenow");

describe("DragonCard", () => {
  it("shows who the dragon is", () => {
    render(<DragonCard dragon={dragon} />);

    expect(screen.getByRole("heading", { level: 1, name: "Ember" })).toBeTruthy();
    expect(screen.getByText(/Sky blue Deadly Nadder/)).toBeTruthy();
    expect(screen.getByText("91%")).toBeTruthy();
    expect(screen.getByText("Hoards shiny things")).toBeTruthy();
    expect(screen.getByText("Hungry")).toBeTruthy();
    expect(screen.getByText("Ember keeps sniffing your satchel.")).toBeTruthy();
    expect(screen.getByText("shiny things")).toBeTruthy();
    expect(screen.getByText("eel")).toBeTruthy();
  });

  it("shows the species artwork and a swatch of the dragon's own colour", () => {
    const { container } = render(<DragonCard dragon={dragon} />);
    const art = screen.getByRole("img", { name: "Artwork of a Deadly Nadder" });
    expect(art.getAttribute("src")).toContain("deadly_nadder.webp");
    const swatch = container.querySelector<HTMLElement>("span[aria-hidden][style]");
    expect(swatch?.style.background).toBe("rgb(74, 144, 200)");
  });

  it("falls back to the silhouette for a species without artwork", () => {
    const { container } = render(
      <DragonCard dragon={{ ...dragon, species_id: "no_art_yet", species_name: "Mystery" }} />,
    );
    expect(screen.queryByRole("img", { name: /Artwork/ })).toBeNull();
    expect(container.querySelector("svg[data-species='no_art_yet']")).toBeTruthy();
  });

  it("shows needs, trust, stats and personality as meters", () => {
    render(<DragonCard dragon={dragon} />);

    expect(meter("Hunger")).toBe("30");
    expect(meter("Trust")).toBe("20");
    expect(meter("Speed")).toBe("33");
    expect(meter("Courage")).toBe("72");
  });
});

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { DragonMatch } from "@/lib/quiz/encounter";

import { MatchResult } from "./match-result";

const dragon = (id: string, name: string, compatibility: number): DragonMatch => ({
  species_id: id,
  name,
  rarity: "uncommon",
  summary: `${name} summary.`,
  compatibility,
  explanation: `Why ${name}.`,
});

describe("MatchResult", () => {
  it("shows the dragon that chose you and the runners-up", () => {
    render(
      <MatchResult
        match={{
          top: dragon("deadly_nadder", "Deadly Nadder", 91),
          runners_up: [
            dragon("gronckle", "Gronckle", 84),
            dragon("thunderdrum", "Thunderdrum", 80),
          ],
        }}
      />,
    );

    expect(screen.getByRole("heading", { level: 1, name: "Deadly Nadder" })).toBeTruthy();
    expect(screen.getByText("91%")).toBeTruthy();
    expect(
      screen
        .getByRole("meter", { name: "Compatibility with Deadly Nadder" })
        .getAttribute("aria-valuenow"),
    ).toBe("91");
    expect(screen.getByText("Why Deadly Nadder.")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Gronckle" }).getAttribute("href")).toBe(
      "/dragon-book/gronckle",
    );
    expect(screen.getByText("Thunderdrum")).toBeTruthy();
  });
});

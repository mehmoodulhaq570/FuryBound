import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { DragonCard, Movie } from "@/lib/dragon-book/types";

import { DragonBook } from "./dragon-book";

const MOVIES: Movie[] = [
  { movie_id: "httyd1", title: "How to Train Your Dragon", year: 2010, ordinal: 1 },
  { movie_id: "httyd2", title: "How to Train Your Dragon 2", year: 2014, ordinal: 2 },
];

const CARDS: DragonCard[] = [
  {
    id: "night_fury",
    kind: "species",
    name: "Night Fury",
    speciesName: null,
    speciesId: "night_fury",
    dragonClass: "Strike",
    size: "medium",
    appearances: [{ movie: "httyd1", type: "on_screen" }],
    confidence: "high",
  },
  {
    id: "stormcutter",
    kind: "species",
    name: "Stormcutter",
    speciesName: null,
    speciesId: "stormcutter",
    dragonClass: "Sharp",
    size: "large",
    appearances: [{ movie: "httyd2", type: "on_screen" }],
    confidence: "medium",
  },
];

function names() {
  return screen.queryAllByRole("heading", { level: 2 }).map((h) => h.textContent);
}

describe("DragonBook", () => {
  it("shows every card, linking to each dragon's page", () => {
    render(<DragonBook cards={CARDS} movies={MOVIES} />);

    expect(names()).toEqual(["Night Fury", "Stormcutter"]);
    expect(screen.getByText("Showing 2 of 2")).toBeTruthy();
    expect(screen.getByRole("link", { name: /Night Fury/ }).getAttribute("href")).toBe(
      "/dragon-book/night_fury",
    );
  });

  it("narrows the list as filters are chosen, and clears them", () => {
    render(<DragonBook cards={CARDS} movies={MOVIES} />);

    fireEvent.change(screen.getByLabelText("Film"), { target: { value: "httyd2" } });
    expect(names()).toEqual(["Stormcutter"]);

    fireEvent.change(screen.getByPlaceholderText(/Search/), { target: { value: "night" } });
    expect(names()).toEqual([]);
    expect(screen.getByText(/No dragons match/)).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(names()).toEqual(["Night Fury", "Stormcutter"]);
  });

  it("hides franchise classes when asked", () => {
    render(<DragonBook cards={CARDS} movies={MOVIES} />);
    expect(screen.getAllByText("franchise").length).toBe(2);

    fireEvent.click(screen.getByLabelText(/Show franchise facts/));

    expect(screen.queryAllByText("franchise")).toHaveLength(0);
    expect((screen.getByLabelText("Class (franchise)") as HTMLSelectElement).disabled).toBe(true);
  });
});

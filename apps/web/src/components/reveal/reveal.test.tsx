import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { DragonMatch, QuizAttemptDetail, QuizMatch } from "@/lib/quiz/encounter";

import { Reveal, TIMING } from "./reveal";

const dragon = (id: string, name: string, compatibility: number): DragonMatch => ({
  species_id: id,
  name,
  rarity: "uncommon",
  summary: `${name} summary.`,
  compatibility,
  explanation: `Why ${name}.`,
});

const match: QuizMatch = {
  top: dragon("deadly_nadder", "Deadly Nadder", 91),
  runners_up: [dragon("gronckle", "Gronckle", 84), dragon("thunderdrum", "Thunderdrum", 80)],
};

const attempt: QuizAttemptDetail = {
  id: "attempt-1",
  quiz_version: "quiz_test",
  traits: [{ id: "courage", label: "Courage", score: 75, low: "Careful.", high: "Fearless." }],
  match,
};

const chosen = () => screen.queryByRole("heading", { level: 1, name: "Deadly Nadder" });

function renderReveal(props: { reduceMotion?: boolean; seen?: boolean; onSeen?: () => void }) {
  return render(
    <Reveal
      attempt={attempt}
      match={match}
      reduceMotion={props.reduceMotion ?? false}
      seen={props.seen ?? false}
      onSeen={props.onSeen ?? vi.fn()}
    />,
  );
}

describe("Reveal", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("circles, peels away, then shows the dragon that chose you", () => {
    const onSeen = vi.fn();
    renderReveal({ onSeen });

    expect(screen.getByText("Three dragons circle overhead…")).toBeTruthy();
    expect(chosen()).toBeNull();

    act(() => vi.advanceTimersByTime(TIMING.circling));
    expect(screen.getByText("Two of them peel away…")).toBeTruthy();
    expect(chosen()).toBeNull();
    expect(onSeen).not.toHaveBeenCalled();

    act(() => vi.advanceTimersByTime(TIMING.peel));
    expect(chosen()).toBeTruthy();
    expect(screen.getByRole("status").textContent).toBe(
      "It chose you: Deadly Nadder, 91% compatible.",
    );
    expect(onSeen).toHaveBeenCalled();
  });

  it("can be skipped", () => {
    renderReveal({});
    fireEvent.click(screen.getByRole("button", { name: "Skip" }));
    expect(chosen()).toBeTruthy();
  });

  it.each([
    ["with reduced motion", { reduceMotion: true }],
    ["once already seen", { seen: true }],
  ])("goes straight to the result %s", (_, props) => {
    renderReveal(props);
    expect(chosen()).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Skip" })).toBeNull();
  });

  it("shows the compatibility, traits and runners-up", () => {
    renderReveal({ seen: true });

    expect(screen.getByText("91%")).toBeTruthy();
    expect(
      screen
        .getByRole("meter", { name: "Compatibility with Deadly Nadder" })
        .getAttribute("aria-valuenow"),
    ).toBe("91");
    expect(screen.getByText("Why Deadly Nadder.")).toBeTruthy();
    expect(screen.getByRole("meter", { name: "Courage" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Gronckle" }).getAttribute("href")).toBe(
      "/dragon-book/gronckle",
    );
    expect(screen.getByText("Thunderdrum")).toBeTruthy();
  });
});

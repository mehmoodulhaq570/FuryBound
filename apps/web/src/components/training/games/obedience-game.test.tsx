import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { COMMANDS, ObedienceGame } from "./obedience-game";

describe("ObedienceGame", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(Math, "random").mockReturnValue(0); // always "Fly", after the shortest wait
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("scores right answers and reports when all commands are done", () => {
    const onFinish = vi.fn();
    render(<ObedienceGame onFinish={onFinish} />);

    for (let round = 0; round < 8; round++) {
      act(() => vi.advanceTimersByTime(500));
      expect(screen.getByRole("status").textContent).toBe(`${COMMANDS[0]}!`);
      fireEvent.click(screen.getByRole("button", { name: "Fly" }));
    }

    expect(onFinish).toHaveBeenCalledOnce();
    const [score, meta] = onFinish.mock.calls[0];
    expect(score).toBeGreaterThan(90);
    expect(meta).toEqual({ correct: 8 });
  });

  it("counts a missed command as wrong", () => {
    const onFinish = vi.fn();
    render(<ObedienceGame onFinish={onFinish} />);
    for (let round = 0; round < 8; round++) act(() => vi.advanceTimersByTime(500 + 2000));
    expect(onFinish).toHaveBeenCalledWith(0, { correct: 0 });
  });
});

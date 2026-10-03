import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FlightGame } from "./flight-game";

let tick: (ms: number) => void;
vi.mock("./use-timers", () => ({
  gameButton: "button",
  useFrames: (fn: (ms: number) => void) => {
    tick = fn;
  },
}));

function fly(from: number, until: number) {
  act(() => {
    for (let ms = from; ms <= until; ms += 16) tick(ms);
  });
}

describe("FlightGame", () => {
  beforeEach(() => vi.clearAllMocks());
  it("automatically finishes six gates exactly once without requiring a perfect flight", () => {
    const onFinish = vi.fn();
    render(<FlightGame onFinish={onFinish} />);
    fly(0, 24000);
    expect(onFinish).toHaveBeenCalledOnce();
    expect(onFinish.mock.calls[0][0]).toBeGreaterThanOrEqual(0);
    expect(onFinish.mock.calls[0][0]).toBeLessThanOrEqual(100);
    expect(onFinish.mock.calls[0][1].offsets).toHaveLength(6);
    fly(24016, 30000);
    expect(onFinish).toHaveBeenCalledOnce();
  });
  it("pauses game time and resumes without jumping over gates", () => {
    const onFinish = vi.fn();
    render(<FlightGame onFinish={onFinish} />);
    fly(0, 1000);
    fireEvent.click(screen.getByRole("button", { name: "Pause" }));
    fly(1016, 180000);
    expect(onFinish).not.toHaveBeenCalled();
    fireEvent.keyDown(window, { key: "Escape" });
    fly(180016, 204000);
    expect(onFinish).toHaveBeenCalledOnce();
    expect(onFinish.mock.calls[0][2]).toBeGreaterThanOrEqual(21800);
    expect(onFinish.mock.calls[0][2]).toBeLessThan(22000);
  });
  it("cleans up keyboard controls when leaving the game", () => {
    const remove = vi.spyOn(window, "removeEventListener");
    const { unmount } = render(<FlightGame onFinish={vi.fn()} />);
    fireEvent.keyDown(window, { key: "ArrowUp" });
    unmount();
    expect(remove).toHaveBeenCalledWith("keydown", expect.any(Function));
    remove.mockRestore();
  });
});

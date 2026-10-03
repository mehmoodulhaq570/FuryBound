import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { RescueInteraction } from "./rescue-interaction";

describe("visual rescue", () => {
  it("requires all knots to be loosened before offering the server completion", () => {
    const complete = vi.fn();
    render(<RescueInteraction method="untie" pending={false} onComplete={complete} />);
    expect(screen.queryByRole("button", { name: "Guide the dragon to safety" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Loosen knot 1" }));
    fireEvent.click(screen.getByRole("button", { name: "Loosen knot 2" }));
    expect(complete).not.toHaveBeenCalled();
    expect(screen.queryByRole("button", { name: "Guide the dragon to safety" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Loosen knot 3" }));
    fireEvent.click(screen.getByRole("button", { name: "Guide the dragon to safety" }));
    expect(complete).toHaveBeenCalledOnce();
  });
  it("blocks repeated completion while saving", () => {
    const complete = vi.fn();
    const view = render(<RescueInteraction method="lift" pending={false} onComplete={complete} />);
    for (let i = 0; i < 3; i++)
      fireEvent.click(screen.getByRole("button", { name: "Lift together" }));
    view.rerender(<RescueInteraction method="lift" pending onComplete={complete} />);
    fireEvent.click(screen.getByRole("button", { name: "Saving your rescue…" }));
    expect(complete).not.toHaveBeenCalled();
  });
});

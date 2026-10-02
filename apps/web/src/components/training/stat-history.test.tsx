import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatHistory } from "./stat-history";

const stats = [
  { id: "speed", label: "Speed" },
  { id: "agility", label: "Agility" },
];

describe("StatHistory", () => {
  it("invites training when there's no history", () => {
    render(<StatHistory history={[]} stats={stats} />);
    expect(screen.getByText(/Train once/)).toBeTruthy();
  });

  it("shows each stat's latest value and change, and a table", () => {
    render(
      <StatHistory
        stats={stats}
        history={[
          {
            id: "s1",
            activity: "flight",
            completed_at: "2026-10-05T10:00:00Z",
            score: 90,
            xp_gained: 74,
            stat_deltas: { speed: 3, agility: 2 },
            stats_after: { speed: 33, agility: 22 },
          },
        ]}
      />,
    );
    expect(screen.getAllByText("Speed")).toHaveLength(2); // chart title and table header
    expect(screen.getByText("+3")).toBeTruthy();
    fireEvent.click(screen.getByText("Show as a table"));
    expect(screen.getAllByRole("row")).toHaveLength(3); // header, start, one session
  });
});

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { PlayerDragon } from "@/lib/dragon/my-dragon";

import { CarePanel } from "./care-panel";

const post = vi.fn();
vi.mock("@/lib/api/client", () => ({ api: { POST: (...args: unknown[]) => post(...args) } }));

const dragon = {
  id: "d1",
  name: "Ember",
  foods: ["fish", "eel"],
} as PlayerDragon;

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  render(
    <QueryClientProvider client={queryClient}>
      <CarePanel dragon={dragon} userId="u1" />
    </QueryClientProvider>,
  );
  return queryClient;
}

describe("CarePanel", () => {
  beforeEach(() => post.mockReset());

  it("feeds the chosen food and shows the dragon's reaction", async () => {
    const fed = { ...dragon, mood: { id: "happy", label: "Happy" } };
    post.mockResolvedValue({
      data: { message: "Ember gobbles the fish and hums happily.", dragon: fed },
    });
    const queryClient = renderPanel();

    fireEvent.click(screen.getByRole("button", { name: "fish" }));

    expect(await screen.findByText("Ember gobbles the fish and hums happily.")).toBeTruthy();
    expect(post).toHaveBeenCalledWith("/api/v1/dragons/{dragon_id}/feed", {
      params: { path: { dragon_id: "d1" } },
      body: { food: "fish" },
    });
    // The page's copy of the dragon is updated, so the bars move.
    expect(queryClient.getQueryData(["my-dragon", "u1"])).toEqual(fed);
  });

  it("shows a refusal in the dragon's words", async () => {
    post.mockResolvedValue({ error: { detail: "Ember flops down. It's too tired to play." } });
    renderPanel();

    fireEvent.click(screen.getByRole("button", { name: "Play" }));

    expect(await screen.findByText("Ember flops down. It's too tired to play.")).toBeTruthy();
    expect(post).toHaveBeenCalledWith("/api/v1/dragons/{dragon_id}/play", {
      params: { path: { dragon_id: "d1" } },
    });
  });
});

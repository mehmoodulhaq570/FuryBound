import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { PlayerDragon } from "@/lib/dragon/my-dragon";

import { LivingHabitat } from "./living-habitat";

const post = vi.fn();
const timers: (() => void)[] = [];
vi.mock("@/lib/api/client", () => ({
  api: {
    POST: (...args: unknown[]) => post(...args),
    GET: async () => ({
      data: { treasures: [], lookout_unlocked: false, xp_reward: 0, layout: { positions: {} } },
    }),
  },
}));
vi.mock("@/components/training/games/use-timers", () => ({
  useTimers: () => (fn: () => void) => timers.push(fn),
}));
const dragon = {
  id: "d1",
  name: "Ember",
  species_id: "night_fury",
  color_hex: "#507282",
  foods: ["fish", "eel"],
  mood: { id: "happy", label: "Happy" },
} as PlayerDragon;
function setup() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const view = render(
    <QueryClientProvider client={client}>
      <LivingHabitat dragon={dragon} userId="u1" />
    </QueryClientProvider>,
  );
  return { ...view, client };
}
async function arrive() {
  await act(async () => {
    timers.shift()?.();
  });
}

describe("playable habitat", () => {
  beforeEach(() => {
    post.mockReset();
    timers.length = 0;
  });
  it("walks to the basket and only eats after the server accepts feeding", async () => {
    post.mockResolvedValue({ data: { dragon, message: "Ember enjoys the fish." } });
    const { container, client } = setup();
    fireEvent.click(screen.getByRole("button", { name: "Open food basket" }));
    fireEvent.click(screen.getByRole("button", { name: "fish" }));
    expect(post).not.toHaveBeenCalled();
    expect(container.querySelector('svg[data-pose="walk"]')).toBeTruthy();
    await arrive();
    expect(await screen.findByText("Ember enjoys the fish.")).toBeTruthy();
    expect(post).toHaveBeenCalledOnce();
    expect(post).toHaveBeenCalledWith("/api/v1/dragons/{dragon_id}/feed", {
      params: { path: { dragon_id: "d1" } },
      body: { food: "fish" },
    });
    expect(container.querySelector('svg[data-pose="eat"]')).toBeTruthy();
    expect(client.getQueryData(["my-dragon", "u1"])).toEqual(dragon);
  });
  it("shows a refusal without pretending the dragon went to sleep", async () => {
    post.mockResolvedValue({ error: { detail: "Ember is already wide awake." } });
    const { container } = setup();
    fireEvent.click(screen.getByRole("button", { name: "Let Ember rest in the nest" }));
    await arrive();
    expect(await screen.findByText("Ember is already wide awake.")).toBeTruthy();
    expect(container.querySelector('svg[data-pose="sleep"]')).toBeNull();
  });
  it("petting and walking are free interactions with no care or XP request", () => {
    setup();
    fireEvent.click(screen.getByRole("button", { name: "Pet Ember" }));
    fireEvent.keyDown(screen.getByRole("button", { name: "Guide your dragon across the meadow" }), {
      key: "ArrowRight",
    });
    expect(post).not.toHaveBeenCalled();
  });
  it("chasing a ball calls the existing play action once on arrival", async () => {
    post.mockResolvedValue({ data: { dragon, message: "Ember brings the ball back." } });
    setup();
    fireEvent.click(screen.getByRole("button", { name: "Throw a ball" }));
    fireEvent.click(screen.getByRole("button", { name: "Throw the ball in the meadow" }));
    await arrive();
    expect(await screen.findByText("Ember brings the ball back.")).toBeTruthy();
    expect(post).toHaveBeenCalledExactlyOnceWith("/api/v1/dragons/{dragon_id}/play", {
      params: { path: { dragon_id: "d1" } },
    });
  });
});

import { beforeEach, describe, expect, it } from "vitest";

import {
  encounterAsQuiz,
  encounterStorageKey,
  hasSeenReveal,
  markRevealSeen,
  toChoices,
  type Encounter,
} from "./encounter";

const encounter: Encounter = {
  version: "encounter_test",
  scenes: [
    {
      id: "first_contact",
      prompt: "A dragon appears.",
      options: [{ id: "reach_out", label: "Reach out" }],
    },
    { id: "offering", prompt: "It sniffs your bag.", options: [{ id: "fish", label: "A fish" }] },
    { id: "startle", prompt: "Thunder!", options: [{ id: "calm_it", label: "Calm it" }] },
  ],
};

describe("encounter helpers", () => {
  it("plays the scenes as quiz questions, in order", () => {
    const quiz = encounterAsQuiz(encounter);
    expect(quiz.version).toBe("encounter_test");
    expect(quiz.questions.map((q) => q.id)).toEqual(["first_contact", "offering", "startle"]);
  });

  it("turns the runner's answers into the API body", () => {
    expect(
      toChoices(encounter, { first_contact: "reach_out", offering: "fish", startle: "calm_it" }),
    ).toEqual({
      encounter_version: "encounter_test",
      first_contact: "reach_out",
      offering: "fish",
      startle: "calm_it",
    });
  });

  it("refuses to submit with a scene missing", () => {
    expect(() => toChoices(encounter, { first_contact: "reach_out", offering: "fish" })).toThrow(
      "startle",
    );
  });

  it("keeps each attempt's progress separate", () => {
    expect(encounterStorageKey("a")).not.toBe(encounterStorageKey("b"));
  });

  describe("reveal seen", () => {
    beforeEach(() => localStorage.clear());

    it("is remembered per attempt", () => {
      expect(hasSeenReveal("a")).toBe(false);
      markRevealSeen("a");
      expect(hasSeenReveal("a")).toBe(true);
      expect(hasSeenReveal("b")).toBe(false);
    });
  });
});

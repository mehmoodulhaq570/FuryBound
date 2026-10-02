import type { components } from "@/lib/api/schema";

import type { Quiz } from "./progress";

export type Encounter = components["schemas"]["Encounter"];
export type EncounterChoices = components["schemas"]["EncounterChoices"];
export type QuizAttemptDetail = components["schemas"]["QuizAttemptDetail"];
export type QuizMatch = components["schemas"]["QuizMatch"];
export type DragonMatch = components["schemas"]["DragonMatch"];
type SceneId = Encounter["scenes"][number]["id"];

/** Scenes look just like quiz questions (a prompt and options), so the quiz runner plays them. */
export function encounterAsQuiz(encounter: Encounter): Quiz {
  return { version: encounter.version, questions: encounter.scenes };
}

export function attemptQueryKey(attemptId: string | null) {
  return ["quiz-attempt", attemptId] as const;
}

/** Where a finished attempt's dragon is revealed. */
export function revealPath(attemptId: string): string {
  return `/academy/reveal?attempt=${attemptId}`;
}

/** One saved progress per attempt, so an old attempt's picks never leak into a new one. */
export function encounterStorageKey(attemptId: string): string {
  return `dragon-academy:encounter-progress:${attemptId}`;
}

/** The runner's answers (scene id → option id) as the API's request body. */
export function toChoices(encounter: Encounter, answers: Record<string, string>): EncounterChoices {
  const pick = (scene: SceneId) => {
    const option = answers[scene];
    if (!option) throw new Error(`No choice for ${scene}`);
    return option;
  };
  return {
    encounter_version: encounter.version,
    first_contact: pick("first_contact"),
    offering: pick("offering"),
    startle: pick("startle"),
  };
}

// Whether this attempt's reveal has played, so a reload goes straight to the result.
// Storage can be unavailable (private mode); then the animation just plays again.
const revealedKey = (attemptId: string) => `dragon-academy:revealed:${attemptId}`;

export function hasSeenReveal(attemptId: string): boolean {
  try {
    return localStorage.getItem(revealedKey(attemptId)) === "1";
  } catch {
    return false;
  }
}

export function markRevealSeen(attemptId: string): void {
  try {
    localStorage.setItem(revealedKey(attemptId), "1");
  } catch {
    // Not fatal.
  }
}

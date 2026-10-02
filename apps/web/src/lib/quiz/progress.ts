import type { components } from "@/lib/api/schema";

export type Quiz = components["schemas"]["Quiz"];
export type QuizQuestion = components["schemas"]["QuizQuestion"];
export type QuizAttempt = components["schemas"]["QuizAttempt"];
export type TraitScore = components["schemas"]["TraitScore"];

/** Where a player is in the quiz: the question on screen and the answers so far. */
export type Progress = {
  version: string;
  index: number;
  answers: Record<string, string>;
};

export type Action = { type: "answer"; questionId: string; optionId: string } | { type: "back" };

export function initialProgress(quiz: Quiz): Progress {
  return { version: quiz.version, index: 0, answers: {} };
}

/** Pure state transitions, so the quiz logic is testable without rendering. */
export function reduce(quiz: Quiz, state: Progress, action: Action): Progress {
  switch (action.type) {
    case "answer": {
      const answers = { ...state.answers, [action.questionId]: action.optionId };
      // Stays on the last question; the caller submits once every question is answered.
      return { ...state, answers, index: Math.min(state.index + 1, quiz.questions.length - 1) };
    }
    case "back":
      return { ...state, index: Math.max(state.index - 1, 0) };
  }
}

export function isComplete(quiz: Quiz, state: Progress): boolean {
  return quiz.questions.every((q) => q.id in state.answers);
}

/** Saved progress is only reused if it belongs to this quiz version and every answer exists. */
export function isValidProgress(quiz: Quiz, value: unknown): value is Progress {
  if (typeof value !== "object" || value === null) return false;
  const p = value as Partial<Progress>;
  if (p.version !== quiz.version || typeof p.index !== "number") return false;
  if (p.index < 0 || p.index >= quiz.questions.length) return false;
  if (typeof p.answers !== "object" || p.answers === null) return false;
  const options = new Map(quiz.questions.map((q) => [q.id, q.options.map((o) => o.id)]));
  return Object.entries(p.answers).every(([q, o]) => options.get(q)?.includes(o) ?? false);
}

// Progress survives a reload in the same tab. Storage can be unavailable (private mode),
// so every access is guarded and the quiz still works without it.
export const QUIZ_STORAGE_KEY = "dragon-academy:quiz-progress";

export function loadProgress(key = QUIZ_STORAGE_KEY): unknown {
  try {
    const raw = sessionStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveProgress(progress: Progress | null, key = QUIZ_STORAGE_KEY): void {
  try {
    if (progress) sessionStorage.setItem(key, JSON.stringify(progress));
    else sessionStorage.removeItem(key);
  } catch {
    // Not fatal: the player just loses progress on reload.
  }
}

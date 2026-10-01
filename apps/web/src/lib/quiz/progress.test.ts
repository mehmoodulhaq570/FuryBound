import { describe, expect, it } from "vitest";

import { initialProgress, isComplete, isValidProgress, reduce, type Quiz } from "./progress";

const quiz: Quiz = {
  version: "quiz_test",
  questions: [
    {
      id: "q1",
      prompt: "One?",
      options: [
        { id: "a", label: "A" },
        { id: "b", label: "B" },
      ],
    },
    {
      id: "q2",
      prompt: "Two?",
      options: [
        { id: "a", label: "A" },
        { id: "b", label: "B" },
      ],
    },
  ],
};

describe("quiz progress", () => {
  it("records an answer and moves to the next question", () => {
    const state = reduce(quiz, initialProgress(quiz), {
      type: "answer",
      questionId: "q1",
      optionId: "b",
    });
    expect(state).toEqual({ version: "quiz_test", index: 1, answers: { q1: "b" } });
  });

  it("stays on the last question once it's answered", () => {
    let state = reduce(quiz, initialProgress(quiz), {
      type: "answer",
      questionId: "q1",
      optionId: "a",
    });
    state = reduce(quiz, state, { type: "answer", questionId: "q2", optionId: "a" });
    expect(state.index).toBe(1);
    expect(isComplete(quiz, state)).toBe(true);
  });

  it("goes back without losing answers, but not before the first question", () => {
    let state = reduce(quiz, initialProgress(quiz), {
      type: "answer",
      questionId: "q1",
      optionId: "a",
    });
    state = reduce(quiz, state, { type: "back" });
    expect(state).toEqual({ version: "quiz_test", index: 0, answers: { q1: "a" } });
    expect(reduce(quiz, state, { type: "back" }).index).toBe(0);
  });

  it("changing an earlier answer replaces it", () => {
    let state = reduce(quiz, initialProgress(quiz), {
      type: "answer",
      questionId: "q1",
      optionId: "a",
    });
    state = reduce(quiz, state, { type: "back" });
    state = reduce(quiz, state, { type: "answer", questionId: "q1", optionId: "b" });
    expect(state.answers).toEqual({ q1: "b" });
    expect(isComplete(quiz, state)).toBe(false);
  });

  it("only restores saved progress that fits this quiz", () => {
    const good = { version: "quiz_test", index: 1, answers: { q1: "a" } };
    expect(isValidProgress(quiz, good)).toBe(true);
    expect(isValidProgress(quiz, { ...good, version: "quiz_old" })).toBe(false);
    expect(isValidProgress(quiz, { ...good, index: 5 })).toBe(false);
    expect(isValidProgress(quiz, { ...good, answers: { q1: "z" } })).toBe(false);
    expect(isValidProgress(quiz, { ...good, answers: { q9: "a" } })).toBe(false);
    expect(isValidProgress(quiz, null)).toBe(false);
  });
});

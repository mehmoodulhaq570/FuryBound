import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Quiz } from "@/lib/quiz/progress";

import { QuizRunner } from "./quiz-runner";

const quiz: Quiz = {
  version: "quiz_test",
  questions: [
    {
      id: "q1",
      prompt: "A dragon is stuck in a net.",
      options: [
        { id: "a", label: "Cut it free" },
        { id: "b", label: "Watch it" },
      ],
    },
    {
      id: "q2",
      prompt: "You have a free day.",
      options: [
        { id: "a", label: "Explore caves" },
        { id: "b", label: "Read in the library" },
      ],
    },
  ],
};

const progress = () => screen.getByRole("progressbar", { name: "Quiz progress" });

describe("QuizRunner", () => {
  beforeEach(() => sessionStorage.clear());

  it("shows one question at a time and submits every answer at the end", () => {
    const onComplete = vi.fn();
    render(<QuizRunner quiz={quiz} onComplete={onComplete} />);

    expect(screen.getByText("Question 1 of 2")).toBeTruthy();
    expect(screen.queryByText("You have a free day.")).toBeNull();
    expect(progress().getAttribute("aria-valuenow")).toBe("0");

    fireEvent.click(screen.getByRole("button", { name: "Watch it" }));
    expect(screen.getByText("Question 2 of 2")).toBeTruthy();
    expect(progress().getAttribute("aria-valuenow")).toBe("1");
    expect(onComplete).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Explore caves" }));
    expect(onComplete).toHaveBeenCalledWith({ q1: "b", q2: "a" });
  });

  it("goes back to change an answer", () => {
    const onComplete = vi.fn();
    render(<QuizRunner quiz={quiz} onComplete={onComplete} />);

    fireEvent.click(screen.getByRole("button", { name: "Cut it free" }));
    fireEvent.click(screen.getByRole("button", { name: "← Back" }));
    expect(screen.getByRole("button", { name: "Cut it free" }).getAttribute("aria-pressed")).toBe(
      "true",
    );

    fireEvent.click(screen.getByRole("button", { name: "Watch it" }));
    fireEvent.click(screen.getByRole("button", { name: "Read in the library" }));
    expect(onComplete).toHaveBeenCalledWith({ q1: "b", q2: "b" });
  });

  it("picks up saved progress after a reload", () => {
    const first = render(<QuizRunner quiz={quiz} onComplete={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Cut it free" }));
    first.unmount();

    render(<QuizRunner quiz={quiz} onComplete={vi.fn()} />);
    expect(screen.getByText("Question 2 of 2")).toBeTruthy();
  });
});

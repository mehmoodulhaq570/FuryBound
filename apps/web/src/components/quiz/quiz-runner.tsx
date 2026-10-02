"use client";

import { useEffect, useReducer, useRef } from "react";

import {
  initialProgress,
  isComplete,
  isValidProgress,
  loadProgress,
  QUIZ_STORAGE_KEY,
  reduce,
  saveProgress,
  type Action,
  type Progress,
  type Quiz,
} from "@/lib/quiz/progress";

/** The words that differ between the quiz and the encounter scenes. */
export type RunnerWording = { step: string; progress: string; submitting: string };

const QUIZ_WORDING: RunnerWording = {
  step: "Question",
  progress: "Quiz progress",
  submitting: "Reading your answers…",
};

/** One question per screen with a progress bar. Calls `onComplete` once all are answered. */
export function QuizRunner({
  quiz,
  onComplete,
  submitting = false,
  storageKey = QUIZ_STORAGE_KEY,
  wording = QUIZ_WORDING,
}: {
  quiz: Quiz;
  onComplete: (answers: Record<string, string>) => void;
  submitting?: boolean;
  storageKey?: string;
  wording?: RunnerWording;
}) {
  // Only rendered in the browser (after the sign-in check), so reading storage here is safe:
  // a reload in the same tab picks up where the player left off.
  const [state, dispatch] = useReducer(
    (s: Progress, a: Action) => reduce(quiz, s, a),
    quiz,
    (q) => {
      const saved = loadProgress(storageKey);
      return isValidProgress(q, saved) ? saved : initialProgress(q);
    },
  );
  const heading = useRef<HTMLHeadingElement>(null);

  useEffect(() => saveProgress(state, storageKey), [state, storageKey]);

  // Move focus to the new question so keyboard and screen-reader users follow along.
  const first = useRef(true);
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    heading.current?.focus();
  }, [state.index]);

  const total = quiz.questions.length;
  const question = quiz.questions[state.index];
  const answered = Object.keys(state.answers).length;
  const complete = isComplete(quiz, state);
  const chosen = state.answers[question.id];
  const onLast = state.index === total - 1;

  function choose(optionId: string) {
    dispatch({ type: "answer", questionId: question.id, optionId });
    const answers = { ...state.answers, [question.id]: optionId };
    if (onLast && isComplete(quiz, { ...state, answers })) onComplete(answers);
  }

  return (
    <div className="mx-auto max-w-xl space-y-8">
      <div className="space-y-2">
        <div className="text-muted flex justify-between text-sm">
          <span>
            {wording.step} {state.index + 1} of {total}
          </span>
          <span>{answered} answered</span>
        </div>
        <div
          role="progressbar"
          aria-label={wording.progress}
          aria-valuemin={0}
          aria-valuemax={total}
          aria-valuenow={answered}
          className="bg-line h-2 overflow-hidden rounded-full"
        >
          <div
            className="bg-accent h-full rounded-full transition-[width] duration-300 motion-reduce:transition-none"
            style={{ width: `${(answered / total) * 100}%` }}
          />
        </div>
      </div>

      <fieldset className="space-y-4" disabled={submitting}>
        <legend className="contents">
          <h1
            ref={heading}
            tabIndex={-1}
            className="text-2xl font-semibold tracking-tight outline-none"
          >
            {question.prompt}
          </h1>
        </legend>
        <ul className="space-y-3">
          {question.options.map((option) => {
            const selected = chosen === option.id;
            return (
              <li key={option.id}>
                <button
                  type="button"
                  aria-pressed={selected}
                  onClick={() => choose(option.id)}
                  className={`bg-surface focus-visible:outline-accent w-full rounded-xl border px-5 py-4 text-left transition-colors focus-visible:outline-2 disabled:opacity-60 ${
                    selected ? "border-accent" : "border-line hover:border-accent"
                  }`}
                >
                  {option.label}
                </button>
              </li>
            );
          })}
        </ul>
      </fieldset>

      <div className="flex items-center justify-between text-sm">
        <button
          type="button"
          onClick={() => dispatch({ type: "back" })}
          disabled={state.index === 0 || submitting}
          className="text-muted hover:text-foreground disabled:invisible"
        >
          ← Back
        </button>
        {submitting ? (
          <span className="text-muted" role="status">
            {wording.submitting}
          </span>
        ) : (
          complete &&
          onLast && (
            <button
              type="button"
              onClick={() => onComplete(state.answers)}
              className="bg-accent rounded-lg px-4 py-2 font-medium text-white"
            >
              Finish
            </button>
          )
        )}
      </div>
    </div>
  );
}

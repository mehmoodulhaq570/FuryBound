import { useCallback, useEffect, useRef } from "react";

/** setTimeout that's cancelled when the game unmounts (e.g. the player navigates away). */
export function useTimers() {
  const ids = useRef<ReturnType<typeof setTimeout>[]>([]);
  useEffect(() => () => ids.current.forEach(clearTimeout), []);
  return useCallback((fn: () => void, ms: number) => {
    ids.current.push(setTimeout(fn, ms));
  }, []);
}

/** Calls `fn` with the time since mount on every animation frame, until unmount. */
export function useFrames(fn: (elapsedMs: number) => void, running = true) {
  const latest = useRef(fn);
  useEffect(() => {
    latest.current = fn;
  });
  useEffect(() => {
    if (!running) return;
    const start = performance.now();
    let id = requestAnimationFrame(function tick(now) {
      latest.current(now - start);
      id = requestAnimationFrame(tick);
    });
    return () => cancelAnimationFrame(id);
  }, [running]);
}

/** What every game reports when it ends (the page adds the session id and duration). */
export type GameProps = { onFinish: (score: number, meta: Record<string, unknown>) => void };

export const gameButton =
  "bg-surface border-line hover:border-accent focus-visible:outline-accent rounded-xl border px-4 py-3 font-medium transition-colors focus-visible:outline-2 disabled:opacity-50";

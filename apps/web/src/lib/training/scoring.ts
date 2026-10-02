/**
 * Scoring for the five Phase 5 training activities (Plan §9.6). Each returns 0-100. Pure, so
 * the games stay thin and the rules are tested on their own.
 */

const clamp01 = (x: number) => Math.min(1, Math.max(0, x));
const mean = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);
const toScore = (x: number) => Math.round(clamp01(x) * 100);

/**
 * Flight (timing bar): how far each press landed from the middle of the target zone, as a
 * share of the bar (0 = dead centre). Within `tolerance` of the centre scores something.
 */
export function flightScore(offsets: number[], tolerance = 0.25): number {
  return toScore(mean(offsets.map((d) => 1 - Math.abs(d) / tolerance)));
}

/** Where the marker is (0-1) at `ms`: it sweeps across and back once per `periodMs`. */
export function markerPosition(ms: number, periodMs: number): number {
  const phase = (ms % periodMs) / periodMs;
  return phase < 0.5 ? phase * 2 : 2 - phase * 2;
}

/**
 * Speed (rhythm): each beat is matched with the nearest unused tap; being `windowMs` or
 * more off (or missing it) scores nothing for that beat. Extra taps cost nothing.
 */
export function rhythmScore(beatsMs: number[], tapsMs: number[], windowMs = 300): number {
  const unused = [...tapsMs];
  const perBeat = beatsMs.map((beat) => {
    let best = -1;
    for (let i = 0; i < unused.length; i++) {
      if (best === -1 || Math.abs(unused[i] - beat) < Math.abs(unused[best] - beat)) best = i;
    }
    if (best === -1) return 0;
    const error = Math.abs(unused[best] - beat);
    if (error >= windowMs) return 0;
    unused.splice(best, 1);
    return 1 - error / windowMs;
  });
  return toScore(mean(perBeat));
}

/**
 * Accuracy (targets): each target is a reaction time, or null if it was missed. A hit is
 * worth between half (at the last moment) and full marks (instantly).
 */
export function accuracyScore(reactionsMs: (number | null)[], windowMs: number): number {
  return toScore(mean(reactionsMs.map((rt) => (rt === null ? 0 : 1 - 0.5 * (rt / windowMs)))));
}

/** Memory: the longest sequence repeated correctly, between the shortest and longest asked. */
export function memoryScore(longest: number, shortest: number, maxLength: number): number {
  if (longest < shortest) return 0;
  return toScore((longest - shortest + 1) / (maxLength - shortest + 1));
}

/**
 * Obedience (commands): a right answer is worth between half (slow) and full marks (fast);
 * a wrong or missing one is worth nothing.
 */
export function obedienceScore(rounds: { correct: boolean; ms: number }[], limitMs: number) {
  return toScore(mean(rounds.map((r) => (r.correct ? 1 - 0.5 * Math.min(1, r.ms / limitMs) : 0))));
}

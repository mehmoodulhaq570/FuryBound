/** A reproducible six-gate course, inside the existing training score contract. */
export const FLIGHT_GATES = [0.48, 0.28, 0.63, 0.38, 0.72, 0.46];
export const GATE_INTERVAL_MS = 3400;
export const FLIGHT_LEAD_IN_MS = 1400;
export const GATE_HALF_GAP = 0.16;

export function courseScore(offsets: number[]): number {
  if (!offsets.length) return 0;
  const sum = offsets.reduce(
    (total, offset) => total + Math.max(0, 1 - Math.abs(offset) / 0.32),
    0,
  );
  return Math.round((sum / offsets.length) * 100);
}

export function steer(height: number, direction: number): number {
  return Math.min(0.86, Math.max(0.14, height + direction * 0.1));
}

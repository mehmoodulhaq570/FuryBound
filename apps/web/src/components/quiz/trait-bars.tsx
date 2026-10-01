import type { TraitScore } from "@/lib/quiz/progress";

/** A player's 0-100 trait scores as labelled bars. */
export function TraitBars({ traits }: { traits: TraitScore[] }) {
  return (
    <ul className="space-y-3">
      {traits.map((t) => (
        <li key={t.id} className="space-y-1">
          <div className="flex justify-between text-sm">
            <span className="font-medium">{t.label}</span>
            <span className="text-muted">{t.score}</span>
          </div>
          <div
            role="meter"
            aria-label={t.label}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={t.score}
            aria-valuetext={`${t.score} out of 100: ${t.score >= 50 ? t.high : t.low}`}
            className="bg-line h-2 overflow-hidden rounded-full"
          >
            <div className="bg-accent h-full rounded-full" style={{ width: `${t.score}%` }} />
          </div>
          <p className="text-muted text-xs">{t.score >= 50 ? t.high : t.low}</p>
        </li>
      ))}
    </ul>
  );
}

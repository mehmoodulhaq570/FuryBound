"use client";

import { useState } from "react";

import { statSeries, type HistoryEntry, type StatPoint } from "@/lib/training/history";

const W = 200;
const H = 64;
const PAD = 6;

/** One stat's line, 0-100 on a shared scale, with a crosshair readout on hover. */
function MiniLine({ title, points }: { title: string; points: StatPoint[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const x = (i: number) => PAD + (i * (W - 2 * PAD)) / Math.max(1, points.length - 1);
  const y = (v: number) => H - PAD - (v / 100) * (H - 2 * PAD);
  const path = points.map((p, i) => `${i ? "L" : "M"}${x(i)} ${y(p.value)}`).join("");
  const last = points.length - 1;
  const shown = hover ?? last;
  const delta = points[last].value - points[0].value;

  return (
    <figure className="bg-surface border-line space-y-1 rounded-xl border p-3">
      <figcaption className="flex items-baseline justify-between text-sm">
        <span className="font-medium">{title}</span>
        <span>
          <span className="font-semibold">{points[shown].value}</span>
          {hover === null && delta !== 0 && (
            <span className="text-muted ml-1 text-xs">
              {delta > 0 ? "+" : ""}
              {delta}
            </span>
          )}
          {hover !== null && <span className="text-muted ml-1 text-xs">{points[hover].label}</span>}
        </span>
      </figcaption>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full touch-none overflow-visible"
        aria-hidden="true"
        onPointerMove={(e) => {
          const box = e.currentTarget.getBoundingClientRect();
          const rel = ((e.clientX - box.left) / box.width) * W;
          const i = Math.round(((rel - PAD) / (W - 2 * PAD)) * last);
          setHover(Math.min(last, Math.max(0, i)));
        }}
        onPointerLeave={() => setHover(null)}
      >
        {/* Recessive baseline and top guide (0 and 100). */}
        <line x1={PAD} x2={W - PAD} y1={y(0)} y2={y(0)} className="stroke-line" strokeWidth={1} />
        <line
          x1={PAD}
          x2={W - PAD}
          y1={y(100)}
          y2={y(100)}
          className="stroke-line"
          strokeWidth={1}
          strokeDasharray="2 3"
        />
        {hover !== null && (
          <line
            x1={x(hover)}
            x2={x(hover)}
            y1={PAD / 2}
            y2={H - PAD / 2}
            className="stroke-muted"
            strokeWidth={1}
          />
        )}
        <path
          d={path}
          fill="none"
          className="stroke-accent"
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
        <circle
          cx={x(shown)}
          cy={y(points[shown].value)}
          r={4}
          className="fill-accent stroke-surface"
          strokeWidth={2}
        />
        {/* A wide invisible target, so the pointer never has to land on the 2px line. */}
        <rect x={0} y={0} width={W} height={H} fill="transparent" />
      </svg>
    </figure>
  );
}

/**
 * How the dragon's stats grew with training: small multiples (one line per stat, one hue,
 * a shared 0-100 scale), plus the same numbers as a table.
 */
export function StatHistory({
  history,
  stats,
}: {
  history: HistoryEntry[];
  stats: { id: string; label: string }[];
}) {
  if (history.length === 0) {
    return (
      <p className="border-line text-muted rounded-xl border border-dashed p-6 text-center text-sm">
        Train once and your dragon&apos;s progress shows up here.
      </p>
    );
  }
  const series = stats.map((s) => ({ ...s, points: statSeries(history, s.id) }));
  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {series.map((s) => (
          <MiniLine key={s.id} title={s.label} points={s.points} />
        ))}
      </div>
      <details className="text-sm">
        <summary className="text-muted cursor-pointer">Show as a table</summary>
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-left">
            <thead className="text-muted">
              <tr>
                <th className="py-1 pr-3 font-normal">When</th>
                {series.map((s) => (
                  <th key={s.id} className="py-1 pr-3 font-normal">
                    {s.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {series[0].points.map((p, i) => (
                <tr key={i} className="border-line border-t">
                  <td className="py-1 pr-3">{p.label}</td>
                  {series.map((s) => (
                    <td key={s.id} className="py-1 pr-3">
                      {s.points[i].value}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}

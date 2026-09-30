import type { Size } from "@/lib/dragon-book/types";

const SCALE: Record<Size, number> = { tiny: 0.55, small: 0.7, medium: 0.85, large: 1, titan: 1 };

/**
 * Placeholder art: an original, generic winged silhouette, scaled by size.
 * No film designs (Plan.md §16). Replaced when there's real artwork.
 */
export function Silhouette({ size, className = "" }: { size: Size | null; className?: string }) {
  const scale = size ? SCALE[size] : 0.85;
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden>
      <g
        transform={`translate(32 34) scale(${scale}) translate(-32 -34)`}
        fill="currentColor"
        stroke="currentColor"
      >
        <path
          stroke="none"
          d="M32 40c-5 0-8.5-2.5-10.5-6.5L6 22.5l9.5 1.5L13 15l11 9c2-3.5 4.8-5.5 8-5.5s6 2 8 5.5l11-9-2.5 9 9.5-1.5-15.5 11C40.5 37.5 37 40 32 40z"
        />
        <path fill="none" strokeWidth="3" strokeLinecap="round" d="M32 39c1.5 7-2 12.5-9 15.5" />
        <circle stroke="none" cx="32" cy="17" r="4.5" />
      </g>
    </svg>
  );
}

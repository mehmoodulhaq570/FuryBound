import { shapeOf } from "@/lib/art/shapes";

/**
 * A species' silhouette (original placeholder art, see lib/art/shapes.ts). It's drawn in
 * the current text colour unless `color` is given; `scale` shrinks it for smaller dragons.
 * `outline` adds a faint edge, so dark colours stay visible on a dark background.
 */
export function DragonSilhouette({
  speciesId,
  className,
  color,
  scale = 1,
  outline = false,
}: {
  speciesId: string | null;
  className?: string;
  color?: string;
  scale?: number;
  outline?: boolean;
}) {
  const { left, center } = shapeOf(speciesId);
  const paths = (items: string[]) => items.map((d, i) => <path key={i} d={d} />);
  return (
    <svg
      viewBox="0 0 100 100"
      aria-hidden="true"
      className={className}
      style={color ? { color } : undefined}
      data-species={speciesId ?? "generic"}
    >
      <g
        transform={`translate(50 50) scale(${scale}) translate(-50 -50)`}
        fill="currentColor"
        {...(outline && {
          stroke: "var(--foreground)",
          strokeOpacity: 0.35,
          strokeWidth: 0.8,
          strokeLinejoin: "round" as const,
        })}
      >
        <g>{paths(left)}</g>
        <g transform="matrix(-1 0 0 1 100 0)">{paths(left)}</g>
        {paths(center)}
      </g>
    </svg>
  );
}

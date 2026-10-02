import { DragonSilhouette } from "@/components/art/dragon-silhouette";
import type { Size } from "@/lib/dragon-book/types";

const SCALE: Record<Size, number> = { tiny: 0.55, small: 0.7, medium: 0.85, large: 1, titan: 1 };

/** A species' silhouette, scaled by its size. Named dragons use their species' shape. */
export function Silhouette({
  speciesId,
  size,
  className = "",
}: {
  speciesId: string;
  size: Size | null;
  className?: string;
}) {
  return (
    <DragonSilhouette
      speciesId={speciesId}
      scale={size ? SCALE[size] : 0.85}
      className={className}
    />
  );
}

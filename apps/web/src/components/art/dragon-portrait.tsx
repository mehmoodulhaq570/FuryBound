import Image from "next/image";

import { speciesImage } from "@/lib/art/images";

import { DragonSilhouette } from "./dragon-silhouette";

/**
 * A species' artwork (original, README "Artwork"), or its silhouette when it has none yet.
 * Named dragons use their species' artwork. `sizes` tells the browser how wide it's shown,
 * so a thumbnail downloads a small file.
 */
export function DragonPortrait({
  speciesId,
  speciesName,
  sizes,
  className = "",
  silhouetteClassName,
  priority = false,
}: {
  speciesId: string;
  speciesName: string;
  sizes: string;
  className?: string;
  /** Colour and opacity for the fallback silhouette. */
  silhouetteClassName?: string;
  priority?: boolean;
}) {
  const src = speciesImage(speciesId);
  if (!src) {
    return (
      <DragonSilhouette
        speciesId={speciesId}
        className={`${className} ${silhouetteClassName ?? "text-muted opacity-50"}`}
      />
    );
  }
  return (
    <Image
      src={src}
      alt={`Artwork of a ${speciesName}`}
      width={640}
      height={640}
      sizes={sizes}
      priority={priority}
      className={`bg-surface rounded-xl object-cover ${className}`}
    />
  );
}

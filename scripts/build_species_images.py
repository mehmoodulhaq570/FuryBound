"""Turn the species artwork in dragons_images/ into web-ready images for the app.

dragons_images/ holds the original artwork (large PNGs, kept out of git). Only images named
exactly like a **species** in the catalog are used ("Night Fury.png" -> night_fury.webp);
images of named film dragons (Toothless, Stormfly, ...) are skipped on purpose (README
"Artwork"): their pages show their species' image instead.

Writes apps/web/public/dragons/<species_id>.webp (square, 640 px, WebP) and
apps/web/src/lib/art/species-images.json (the ids that have an image). Rerun after adding
or replacing artwork.

Run from the repo root:  pnpm art:build
"""

import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "dragons_images"
DRAGONS = ROOT / "data" / "build" / "dragons.json"
OUT_DIR = ROOT / "apps" / "web" / "public" / "dragons"
MANIFEST = ROOT / "apps" / "web" / "src" / "lib" / "art" / "species-images.json"

SIZE = 640
QUALITY = 80


def main() -> int:
    entries = json.loads(DRAGONS.read_text(encoding="utf-8"))
    species = {e["name"]: e["id"] for e in entries if e["kind"] == "species"}
    named = {e["name"] for e in entries if e["kind"] != "species"}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    built, skipped, unknown = [], [], []
    for path in sorted(SOURCE.glob("*.png")):
        name = path.stem
        if name in species:
            species_id = species[name]
            with Image.open(path) as img:
                square = img.convert("RGB")
                side = min(square.size)  # centre-crop anything that isn't square
                left, top = (square.width - side) // 2, (square.height - side) // 2
                square = square.crop((left, top, left + side, top + side))
                square = square.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
                square.save(OUT_DIR / f"{species_id}.webp", "WEBP", quality=QUALITY, method=6)
            built.append(species_id)
        elif name in named:
            skipped.append(name)
        else:
            unknown.append(name)

    # Images whose species was renamed or removed would otherwise linger.
    for stale in OUT_DIR.glob("*.webp"):
        if stale.stem not in built:
            stale.unlink()

    MANIFEST.write_text(json.dumps(sorted(built), indent=2) + "\n", encoding="utf-8")
    size_kb = sum(f.stat().st_size for f in OUT_DIR.glob("*.webp")) / 1024
    print(f"Built {len(built)} of {len(species)} species images ({size_kb:.0f} KB in total).")
    if missing := sorted(set(species) - {n for n in species if species[n] in built}):
        print(f"No artwork yet (silhouette shown): {', '.join(missing)}")
    print(f"Skipped {len(skipped)} named-dragon images (species art is used instead).")
    if unknown:
        print(f"Not a species or named dragon in the catalog: {', '.join(unknown)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

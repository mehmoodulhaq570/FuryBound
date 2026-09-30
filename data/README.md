# Data

Each folder holds one of the four data layers from Plan.md §3. Generated data never flows back into canon, franchise or game data.

| Folder | Layer | Edited by |
|---|---|---|
| `research/` | Raw per-film scene logs (notes and timestamps) | Hand |
| `catalog/` | 1–2: canon and franchise facts, as CSV | Hand, reviewed (except the two files below) |
| `game/` | 3: invented balancing values, as YAML | Hand, tuned freely |
| `build/` | Output of `scripts/build_catalog.py` | **Never by hand** |

## How dragon data flows

```
research/httydN_scene_log.md ──pnpm catalog:import──► catalog/appearances.csv, rider_links.csv
catalog/*.csv ──pnpm catalog:build──► build/seed.sql, dragons.json, dragons.csv ──pnpm db:reset──► database
```

- **Scene logs** are where film viewing is recorded. Their checklists and rider tables are the source for `appearances.csv` and `rider_links.csv`, so **edit the logs, not those two CSVs**.
- **Everything else in `catalog/`** (species, individuals, characters, sources, abilities) is edited directly.
- `pnpm catalog:check` validates the catalog; `catalog:build` validates first and refuses to build a broken catalog.

After changing a scene log or a catalog file:

```sh
pnpm catalog:import   # only if a scene log changed
pnpm catalog:build    # validates, then regenerates build/
pnpm db:reset         # rebuilds the local database with the new seed
```

Commit the scene log, the catalog and `build/` together. CI fails if they disagree.

## Current state (2026-09-30)

The catalog was first filled in by Claude from the fan wiki's film pages and general knowledge, **not from watching the films**. Every row carries its `source_ids` and `confidence`; no row cites a `film_*` source yet. Descriptions are drafts (see each row's `notes`). As the films are watched, confirm rows in the scene logs and re-run the steps above.

Templates for the catalog files are in Plan.md, Appendix A.

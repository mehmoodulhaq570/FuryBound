# Changelog

All notable changes to FuryBound / Dragon Academy. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Dates are YYYY-MM-DD. Phases refer to the roadmap in [Plan.md](Plan.md#12-roadmap-phases-08).

## [Unreleased]

### Changed
- **Dragon personalities** (`data/game/species_profiles.yaml`), after a review of the game data:
  - Deathgripper's courage minimum raised from 40 to 60, and Monstrous Nightmare's lowered from 50 to 45, so the scarier dragon asks more of the rider.
  - Light Fury's patience minimum lowered from 55 to 50, so it no longer asks for much more patience than it has itself.
  - Scuttleclaw's curiosity weight lowered from 2.0 to 1.5, so it's no longer the default match for every curious player.
- **Quiz wording** (`data/game/quiz_v1.yaml`). Safe to edit because no players have taken quiz_v1 yet.
  - Q1a, "Cut it free right away": intelligence changed from −4 to +2, so the Hiccup answer no longer works against a Night Fury match.
  - Q9c now reads "Leave fish deep in the woods to lure it away from the village". The old wording implied that feeding the dragon would stop it coming back.
  - Q12c now reads "Sitting up late with a friend who's panicking, even though you haven't studied either", so it's no longer the obviously "good" answer.
- Recalibrated matching (`data/build/matching_calibration.json`). Top-match shares: Scuttleclaw 15.2% → 14.2%, Light Fury 2.1% → 2.5%, Night Fury 0.7% (unchanged). All targets are met.

## Phase 3: Quiz + matching engine (2026-10-01)

### Added
- Game data in `data/game/`: 7 traits, a 12-question quiz, 15 matchable species profiles, 3 complement rules and 3 encounter scenes. All validated on load (Pydantic).
- Matching engine (`apps/api/app/engines/matching.py`): quiz scoring, percentile-based matching, explanations and a displayed compatibility of 60–99%.
- `pnpm match:calibrate`: a Monte Carlo simulation of 100,000 random players. CI runs it with `--check`. The engine refuses a stale calibration.
- 16 matching tests, including 6 personality archetypes.

## Phase 2: Dragon Book (2026-10-01)

### Added
- Dragon Book pages in the web app: a list page with Fuse.js search (word-aware re-ranking) and filters, plus 77 statically generated detail pages.
- Scope badges, confidence meter and fan disclaimer.
- 19 Vitest tests.

## Phase 1: Dragon database (2026-09-30 → 2026-10-01)

### Added
- Scene logs for all three films (`data/research/`), pre-filled and awaiting film verification.
- Catalog CSVs: 50 species, 27 named dragons, 138 appearances, 25 rider links and 10 sources.
- Catalog pipeline: `catalog:import`, `catalog:check` and `catalog:build` (→ `seed.sql`, `dragons.json`, `dragons.csv`).
- Canon tables migration with public-read RLS. The seed loads on `pnpm db:reset`.
- Read-only API: `/movies`, `/species`, `/individuals` and `/search`, with 34 pytest tests.

## Phase 0: Foundations (2026-09-30)

### Added
- Monorepo (pnpm workspace + uv), Next.js web app, FastAPI API and local Supabase.
- GitHub Actions CI with API, Data and Web jobs.
- Lean `pnpm db:start` for low-RAM machines.

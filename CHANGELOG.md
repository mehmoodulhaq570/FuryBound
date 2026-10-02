# Changelog

All notable changes to FuryBound / Dragon Academy. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Dates are YYYY-MM-DD. Phases refer to the roadmap in [Plan.md](Plan.md#12-roadmap-phases-08).

## [Unreleased]

### Added
- **A living dragon** on `/dragon`: needs drift while you're away (hunger +4/h, energy +8/h, happiness −2/h), worked out when you come back. You can **Feed** (6 foods; liked ones please it more, disliked ones cost happiness and trust), **Rest** and **Play**. The dragon refuses with a reason when it's full, wide awake or too tired. A **mood** (Hungry, Tired, Angry, Excited, Curious, Happy; first matching rule wins, Plan §9.7) and an **idle thought** that changes every hour show on the card.
- `data/game/care.yaml` (invented): decay rates, care action effects and refusals, messages and idle thoughts.
- Care engine (`apps/api/app/engines/care.py`, pure): decay, care actions, mood and thoughts. Scared waits for storms in stories; Angry needs the training refusals that arrive in Phase 5.
- **Care API**: `POST /api/v1/dragons/{id}/feed` · `/rest` · `/play` (409 with the dragon's reason when it refuses). `GET /dragons/me` now returns needs as of now, `mood`, `thought` and `foods`.
- `dragon_events` table (migration `20261003120000_dragon_events.sql`): a diary of adopted, fed, rested and played, readable by the owner only.
- Tests: 23 API tests (care rules, mood order, endpoints, needs drift) and 2 web tests for the care panel.

### Fixed
- Datetimes are now sent to Postgres with their time zone (`type_annotation_map` in `db/models.py`).
- **Species silhouettes** (`apps/web/src/lib/art/shapes.ts`, `components/art/dragon-silhouette.tsx`): original placeholder art for each of the 15 matchable species, built from parts (wings, head, tail, legs). For example, the Zippleback has two heads and the Gronckle a club tail. Other species use a generic shape. They're used in the Dragon Book (named dragons take their species' shape), the reveal (the actual top 3 circle overhead) and on `/dragon`, where your dragon is drawn in its own colour. No film designs are copied (Plan §16).
- Dragon Book pages link to the fan wiki ("See what it looks like on the fan wiki"), through the wiki's search so no link goes dead. We link to the wiki and don't copy its images.
- Colour variants in `adoption.yaml` now have a `hex` colour, and `PlayerDragon` returns `color_hex`.
- **Naming and adoption** (Phase 4 start): the reveal now ends with "Name your <dragon>". Naming adopts the top match as your dragon and opens `/dragon`, a first dragon card (name, colour, species, compatibility, level, quirks, likes and dislikes, needs, trust, stats, personality). "My dragon" is in the header. One dragon per player.
- **Dragon API**: `POST /api/v1/dragons` (adopt from a finished attempt; 409 if the encounter isn't done or you already have a dragon, 422 with a reason for a refused name) and `GET /api/v1/dragons/me`.
- `data/game/adoption.yaml` (invented): starting needs and trust, the personality spread (σ = 6), starting stats (30–40% of caps), name rules, 12 quirks and 2–3 colour variants per matchable species. It's separate from the matching data, so editing it needs no recalibration.
- Adoption engine (`apps/api/app/engines/adoption.py`): rolls a dragon reproducibly from the attempt id, and checks names (2–20 letters; spaces, hyphens and apostrophes between; a small whole-word filter for unkind words).
- Migration `20261002120000_profiles_and_dragons.sql`: `profiles` (one is created automatically for every new account, plus a backfill for existing ones), `player_dragons` (owner-only read), and `quiz_attempts.user_id` now references `profiles`.
- Tests: 75 API tests for adoption rules and the dragon endpoints, and 13 web tests for name checks and the dragon card.
- **Quiz page** at `/academy/quiz`: one question per screen, a progress bar, a Back button, and progress that survives a reload in the same tab. When the quiz is done it shows the player's trait bars. Linked from the header and home page.
- **Quiz API**: `GET /api/v1/quiz` (the active quiz without its scores; options shuffled per player but stable across reloads) and `POST /api/v1/quiz/attempts` (scores and saves the answers). Both need sign-in.
- `quiz_attempts` table (migration `20261001120000_quiz_attempts.sql`), so players can only read their own attempts. It references `auth.users` until profiles arrive in Phase 4. The quiz stays in YAML, so there are no quiz tables.
- **Encounter scenes** at `/academy/encounter?attempt=<id>`: the three scenes (first contact, offering, startle) play one per screen after the quiz, then go to the reveal. The quiz-done screen's button ("Step into the fog") now leads there. Progress is kept per attempt.
- **The reveal** at `/academy/reveal?attempt=<id>`: three dragon silhouettes circle overhead, two peel away, and the chosen one dives in. Then "It chose you", the compatibility bar fills, and the explanation, the player's trait bars and the 2 runners-up (linked to the Dragon Book) fade in. It has a Skip button. With reduced motion it only fades; on a reload it shows the result at once. Naming the dragon is a placeholder button until Phase 4.
- **Motion** (animation library) added to the web app.
- **Encounter API**: `GET /api/v1/encounter` (the scenes, without what each option means; shuffled per player), `POST /api/v1/quiz/attempts/{id}/encounter` (runs the matching engine, saves `encounter_signals`, `ranking` and `completed_at`; only once per attempt, 409 after that) and `GET /api/v1/quiz/attempts/{id}` (the attempt and, once finished, its match). Another player's attempt answers 404.
- Sign-in now returns to the page that sent you there (`/login?next=…`).
- Tests: 7 new API tests for the encounter, and 11 web tests for the encounter helpers, the reveal sequence and the reworded runner.
- Tests: 7 API tests for the quiz endpoints and 8 web tests for the quiz screen and its progress logic.

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

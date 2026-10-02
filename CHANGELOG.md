# Changelog

All notable changes to FuryBound / Dragon Academy. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Dates are YYYY-MM-DD. Phases refer to the roadmap in [Plan.md](Plan.md#12-roadmap-phases-08).

## [Unreleased]

## Phase 5: Training (2026-10-02)

### Added
- **Training** at `/train`: your dragon's level and XP, the five activities (locked ones show the stage that unlocks them), and a **progress chart**: one small line chart per stat (shared 0–100 scale, hover readout, table view). "Train" is in the header and on `/dragon`.
- **Five mini-games** at `/train/<activity>`, all simple DOM versions of the Plan's activity contract (score 0–100 + duration):
  - **Flight** (agility, speed): press when the marker is in the glowing zone.
  - **Speed** (speed, stamina): tap on every wingbeat.
  - **Accuracy** (firepower): hit targets on a grid before they vanish. Unlocks at Young.
  - **Memory** (intelligence): repeat a growing sequence of signs. Unlocks at Young.
  - **Obedience** (obedience): answer commands with the right signal, fast. Unlocks at Trained.
- **Progression** (Plan §9.6): XP = (20 + 0.6 × score) × mood multiplier; level curve 100 × L^1.5 up to level 30; stages Newborn → Young (5) → Trained (10) → Elite (20) → Master (30); stat gains shrink near the species' caps. Each session costs energy and hunger, nudges happiness by score and builds trust (more when the dragon's needs were met). A level-up celebration shows new stages and unlocks.
- **Refusals**: an exhausted (energy < 15) or very hungry (hunger > 85) dragon won't train. Refusals are logged, so a low-trust dragon that refused recently is **Angry**.
- **API**: `GET /dragons/{id}/training`, `POST /dragons/{id}/training-sessions`, `POST /training-sessions/{id}/complete` (once per session; the duration must be plausible for the activity and fit inside the session; sessions expire after 30 minutes) and `GET /dragons/{id}/history`. `PlayerDragon` now has `xp`, `xp_to_next` and `stage_label`.
- `data/game/progression.yaml` (every number above) and the pure engine `apps/api/app/engines/training.py`.
- `training_sessions` table (migration `20261005120000_training_sessions.sql`), with the mood and needs at the start and the stats afterwards.
- **Hypothesis** property tests: a higher score never gives less XP, and stats never pass their caps. The API suite is now 184 tests and the web suite 76.

## Phase 4: Your dragon (2026-10-02)

The playable MVP (Milestone M2): sign up → quiz → encounter → reveal → name your dragon → look after it → find it, with needs changed, on your next visit.

### Added
- **Naming and adoption.** The reveal ends with "Name your <dragon>". Naming adopts the top match (one dragon per player) and opens `/dragon`. The dragon is rolled reproducibly from the attempt: species traits with a small personal variation (σ = 6), starting stats at 30–40% of the species' caps, 1–2 quirks and a colour variant. Names are 2–20 letters (spaces, hyphens and apostrophes between), with a small whole-word filter for unkind words.
- **A living dragon** on `/dragon`. Needs drift while you're away (hunger +4/h, energy +8/h, happiness −2/h), worked out when you come back rather than by a background job. **Feed** (6 foods; liked ones please it more, disliked ones cost happiness and trust), **Rest** and **Play**. The dragon refuses with a reason when it's full, wide awake or too tired. The card shows a **mood** (Hungry, Tired, Angry, Excited, Curious or Happy; the first matching rule wins, Plan §9.7) and an **idle thought** that changes every hour.
- **Discoveries (Academy mode)** in the Dragon Book. Signed-in players see dragons they haven't met as "???" with only a silhouette, a "X / 50 species discovered" bar, "new" badges for the last day's discoveries and a Show all switch. Searching doesn't reveal hidden names. The three dragons in the reveal are discovered when the encounter is finished, and named dragons unlock with their species. Logged-out visitors still see the full book.
- **Species silhouettes**: original placeholder art for the 15 matchable species, built from parts (wings, head, tail, legs). For example, the Zippleback has two heads and the Gronckle a club tail. Used in the Dragon Book, the reveal (your actual top 3 circle overhead) and on `/dragon`, where your dragon is drawn in its own colour. No film designs are copied (Plan §16).
- Dragon Book pages link to the fan wiki ("See what it looks like on the fan wiki") through the wiki's search, so no link goes dead.
- **API**: `POST /dragons`, `GET /dragons/me` (needs as of now, mood, thought), `POST /dragons/{id}/feed` · `/rest` · `/play` (409 with the dragon's reason when it refuses) and `GET /discoveries`.
- **Game data** (invented): `data/game/adoption.yaml` (starting values, name rules, 12 quirks, colour variants with hex colours) and `data/game/care.yaml` (decay rates, care effects and refusals, messages, idle thoughts). Both are separate from the matching data, so editing them needs no recalibration.
- **Engines** (pure, no I/O): `engines/adoption.py` and `engines/care.py`.
- **Migrations**: `profiles` (created automatically for every new account, with a back-fill), `player_dragons`, `dragon_events` (a diary of adopted, fed, rested and played) and `discoveries` (back-filled from finished attempts). All are owner-only reads; `quiz_attempts.user_id` now references `profiles`.
- Tests: the API suite is now 165 tests and the web suite 63.

### Fixed
- Datetimes are now sent to Postgres with their time zone (`type_annotation_map` in `db/models.py`).

## Phase 3: Quiz + matching (2026-10-01 → 2026-10-02)

### Added
- Game data in `data/game/`: 7 traits, a 12-question quiz, 15 matchable species profiles, 3 complement rules and 3 encounter scenes. All validated on load (Pydantic).
- Matching engine (`apps/api/app/engines/matching.py`): quiz scoring, percentile-based matching, explanations and a displayed compatibility of 60–99%.
- `pnpm match:calibrate`: a Monte Carlo simulation of 100,000 random players. CI runs it with `--check`. The engine refuses a stale calibration.
- **Quiz** at `/academy/quiz`: one question per screen, a progress bar, a Back button, and progress that survives a reload in the same tab. When the quiz is done it shows the player's trait bars.
- **Encounter** at `/academy/encounter`: three scenes (first contact, offering, startle) after the quiz, one per screen, with progress kept per attempt.
- **The reveal** at `/academy/reveal`: three silhouettes circle overhead, two peel away and the chosen dragon dives in. Then "It chose you", a filling compatibility bar, the explanation, the player's trait bars and 2 runners-up. It has a Skip button, a fade-only version for reduced motion, and shows the result at once on a reload. Built with **Motion**.
- **API**: `GET /quiz` (no scores; options shuffled per player but stable across reloads), `POST /quiz/attempts`, `GET /encounter` (no hints about what each option means), `POST /quiz/attempts/{id}/encounter` (runs the matching engine; only once per attempt, so no rerolls) and `GET /quiz/attempts/{id}`. Another player's attempt answers 404.
- `quiz_attempts` table (migration `20261001120000_quiz_attempts.sql`) with owner-only reads. The quiz itself stays in YAML.
- Sign-in returns to the page that sent you there (`/login?next=…`).
- Tests: 16 matching tests (including 6 personality archetypes), plus API and web tests for the quiz, encounter and reveal.

### Changed
- **Dragon personalities** (`data/game/species_profiles.yaml`), after a review of the game data:
  - Deathgripper's courage minimum raised from 40 to 60, and Monstrous Nightmare's lowered from 50 to 45, so the scarier dragon asks more of the rider.
  - Light Fury's patience minimum lowered from 55 to 50, so it no longer asks for much more patience than it has itself.
  - Scuttleclaw's curiosity weight lowered from 2.0 to 1.5, so it's no longer the default match for every curious player.
- **Quiz wording** (`data/game/quiz_v1.yaml`), before any player had taken it:
  - Q1a, "Cut it free right away": intelligence changed from −4 to +2, so the Hiccup answer no longer works against a Night Fury match.
  - Q9c now reads "Leave fish deep in the woods to lure it away from the village". The old wording implied that feeding the dragon would stop it coming back.
  - Q12c now reads "Sitting up late with a friend who's panicking, even though you haven't studied either", so it's no longer the obviously "good" answer.
- Recalibrated matching. Top-match shares: Scuttleclaw 15.2% → 14.2%, Light Fury 2.1% → 2.5%, Night Fury 0.7% (unchanged). All targets are met.

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

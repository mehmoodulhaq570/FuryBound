# Session overview: FuryBound / Dragon Academy

Summary of the Claude Code sessions of **2026-09-30 → 2026-10-01** (Phase 3 started on 10-01; the quiz page was built late on 10-01). Read this first when picking the project back up. The full plan is [Plan.md](../Plan.md); what changed when is in [CHANGELOG.md](../CHANGELOG.md); tools are in [TECH_STACK.md](../TECH_STACK.md); the data workflow is in [data/README.md](../data/README.md).

## Where things stand

| Phase | Status |
|---|---|
| 0 Foundations | ✅ Done. CI green on GitHub |
| 1 Dragon database | ✅ Code done. ⏳ Film verification by the user (scene logs) |
| 2 Dragon Book | ✅ Done locally (Milestone M1). Not deployed yet |
| 3 Quiz + matching | ✅ Engine, quiz, encounter and reveal done (2026-10-02). Naming moved to Phase 4 |

- **Repo:** https://github.com/mehmoodulhaq570/FuryBound (public, branch `main`). The user commits and pushes **themselves**; don't push.
- **Package / Supabase project name:** `dragon-academy` (the GitHub repo name is FuryBound).

## What was built

**Phase 0: machine and setup fixes**
- Docker Desktop's WSL data moved to `D:\DevTools\docker\wsl`. The disk file had become owned by Administrators (it was moved from an admin shell), so WSL got `E_ACCESSDENIED`; fixed with a user-owned copy. `docker_data.admin-owned.bak` there can be deleted.
- RAM crash: Supabase + WSL filled the 16 GB RAM and Windows grew `C:\pagefile.sys` until C: was full. Fixes: `C:\Users\mehmo\.wslconfig` caps WSL at 4 GB (swap on D:), the page file mostly moved to D: (Windows keeps a fixed 4 GB one on C:), hibernation off.
- The crash corrupted the `storage-api` image (0-byte `package.json`), which broke `supabase start`. The image was re-pulled.
- `.env` files created from the examples, using the standard local Supabase keys.
- `httpx2` in the API's dev dependencies is **legitimate and needed** (the official successor to httpx, by Pydantic; Starlette's TestClient wants it). Don't remove it.

**Phase 1: dragon data** (`data/`, `scripts/`, `supabase/migrations/`)
- Scene logs `data/research/httyd{1,2,3}_scene_log.md`, **pre-filled by Claude** from the fan wiki's film pages (pinned revisions) and general knowledge. Rows are marked `yes?` / `no?` for the user to confirm while watching. No timestamps, because only a viewer can add those.
- `data/research/external_candidates.csv`: names and classes from two fan repos (uokik/how-to-train-your-dragon-api, RomainChamb/httydApi). Both are unlicensed, so descriptions and stats were **not** copied.
- Catalog `data/catalog/*.csv`: 50 species, 27 named dragons, 138 appearances, 25 rider links, 10 sources. Descriptions are Claude's drafts; nine obscure species have none on purpose.
- Pipeline: `pnpm catalog:import` (scene logs → appearances and riders), `catalog:check` (validator), `catalog:build` (→ `data/build/seed.sql`, `dragons.json`, `references.json`, `dragons.csv`). The output is deterministic.
- Migration `20260930150000_canon_tables.sql`: canon tables with public-read RLS. The seed loads on `pnpm db:reset` (`supabase/config.toml` points at `../data/build/seed.sql`).
- API (`apps/api/app/canon.py`, `routers/canon.py`, `db/`, `schemas/`): `/movies`, `/species[/{id}]`, `/individuals[/{id}]`, `/search`. SQLAlchemy 2.1 async + asyncpg. 34 pytest tests run against the seeded database; they skip locally if it's down and fail on CI.

**Phase 2: Dragon Book** (`apps/web/src/app/dragon-book/`, `components/dragon-book/`, `lib/dragon-book/`)
- Static pages built from `@data/dragons.json` (a tsconfig alias to `data/build/`): a list page with Fuse.js search and filters, plus 77 pre-built detail pages (`dynamicParams = false`).
- Search has **word-aware re-ranking** on top of Fuse, because on its own Fuse ranked "Thunderdrum" above "Deadly Nadder" for "nader". A test covers it.
- Franchise classes always carry a "franchise" tag. There's a confidence meter everywhere and a fan disclaimer in the footer.
- 19 Vitest tests, including checks of the real `dragons.json` against the TypeScript types.

**Phase 3: quiz + matching engine** (`data/game/`, `apps/api/app/engines/`, `apps/api/scripts/calibrate_matching.py`)
- `traits.yaml` (7 traits), `quiz_v1.yaml` (12 questions; every trait touched 9–12 times), `species_profiles.yaml` (15 matchable species), `complements.yaml` (3 rules), `encounter_v1.yaml` (the 3 scenes). All validated on load by `engines/game_data.py` (Pydantic).
- `engines/matching.py`: pure quiz scoring + matching per Plan §9.3, explanations, displayed 60–99% compatibility.
- `pnpm match:calibrate`: 100,000 random players, writes `data/build/matching_calibration.json`. CI (Data job) runs `--check`. It takes ~2–3 minutes. The engine refuses a stale calibration (fingerprint of the game data).
- 16 tests in `tests/test_matching.py`, including 6 archetype fixtures (cautious scholar, reckless daredevil, loyal friend, lone wolf, curious explorer, calm homebody). No database needed.
- Current shares: Scuttleclaw 14.2% (highest) … Light Fury 2.5%, Night Fury 0.7%.
- 2026-10-01 review fixes: Deathgripper courage min 40→60, Nightmare 50→45; Light Fury patience min 55→50; Scuttleclaw curiosity weight 2.0→1.5; Q1a intelligence −4→+2; Q9c and Q12c reworded.

**Phase 3: quiz page** (2026-10-01; see CHANGELOG.md "Unreleased")
- Migration `20261001120000_quiz_attempts.sql`: `quiz_attempts` with an owner-only select RLS policy. The API writes through the postgres connection.
- API: `app/quiz.py` (service), `routers/quiz.py`, `schemas/quiz.py`. `GET /api/v1/quiz` returns the quiz without deltas, options shuffled with a seed of user id + version + question (stable across reloads). `POST /api/v1/quiz/attempts` checks the version (409 if stale) and the answers (422), then saves the answers + min–max trait scores and returns `{id, quiz_version, traits[]}`. The `QuizAttemptRow` model is in `db/models.py`.
- `tests/test_quiz.py`: 7 tests. The 2 without a database pass; **the 5 database tests haven't run yet** (Docker was closed). They insert a throwaway `auth.users` row.
- Web: `/academy/quiz` → `components/quiz/quiz-flow.tsx` (sign-in check, TanStack Query, submit) → `quiz-runner.tsx` (one question per screen, progress bar, Back, focus moves to each new question) → `trait-bars.tsx` (reusable for the result screen). The pure logic is in `lib/quiz/progress.ts`; progress is kept in `sessionStorage` and only reused if it fits the quiz version.
- `/login?next=…` returns to the page you came from (same-site paths only). The header and home page link to the quiz.
- 27 web tests pass (8 new). API types were regenerated with `pnpm gen:api-types`.

**Phase 3: encounter scenes** (2026-10-02)
- API: `GET /encounter`, `POST /quiz/attempts/{id}/encounter` (locks the row; 409 if done or the quiz/encounter version changed; 422 for an unknown option), `GET /quiz/attempts/{id}` (`match` is null until finished). `ranking` stores the top 3 as `{species_id, raw, compatibility, explanation}`; names come from the `species` table, rarity and summary from the profiles. `get_calibration()` (cached) in `matching.py`.
- Web: `/academy/encounter?attempt=<id>` → `components/encounter/encounter-flow.tsx`. It **reuses `QuizRunner`** (scenes have the same shape as questions; new `storageKey` and `wording` props). A finished attempt redirects to the reveal. `Notice` is in `components/quiz/notice.tsx`; `AttemptGate` (`components/quiz/attempt-gate.tsx`) does the id / sign-in / ownership checks for both pages.
- Reveal: `/academy/reveal?attempt=<id>` → `components/reveal/` (`reveal-flow.tsx` → `reveal.tsx` with phases circling → peel → landed, timings in `TIMING`; `reveal-stage.tsx` is the Motion animation; `silhouette.tsx` is a generic SVG dragon, the same for all species until there's art). Reduced motion = fades only. "Seen" is kept in localStorage per attempt, so a reload skips the animation. Motion 14 installed.
- **Decision (2026-10-02):** naming the dragon moves to the start of Phase 4 (it needs `player_dragons` + `POST /dragons`). The reveal has a disabled "Naming your dragon is coming next" button.
- All 64 API tests pass, including the 5 quiz database tests that hadn't run before. 33 web tests pass, but only with `vitest run --maxWorkers=1` when RAM is tight (the default run timed out starting workers).
- The user played quiz → encounter in the browser (got a Light Fury, 90%) before the reveal existed. **The reveal animation hasn't been seen in a browser yet.**

## Decisions and deviations from Plan.md

- **Local Supabase only** during development, so the user can learn it. Hosted Supabase comes at launch.
- **Option 1 data:** all pre-filled rows go into the catalog (including low-confidence ones), labelled with confidence and sources, instead of waiting for film verification.
- `appearances` and `rider_links` also carry `source_ids` and `confidence`. Plan §8.3 didn't have them, but they're needed so every fact is traceable.
- Scene logs are the source of truth for `appearances.csv` and `rider_links.csv`: **edit the logs, not those two CSVs**.
- Species and individual ids share one namespace (`/dragon-book/<id>`). The validator enforces the Plan's `the_` rule (`light_fury` vs `the_light_fury`).
- **Player traits are converted to percentiles before matching** (exact, assuming random answers), because summed quiz scores cluster in the middle and the strong-personality dragons could never win. The Plan's min–max scores are still used for display.
- Dropped `base_stats`; only `stat_caps` (a new dragon starts at 30–40% of caps). Removed two complement rules (restless→patience, timid→courage) that pulled everyone toward a few dragons.
- Matchable pool: on-screen, trainable film species minus titans, the Night Light hatchlings and the Seashocker. Legendary target is 0.5–3% (the Plan's "≥3%" for every species can't also hold for legendaries). Calibration script lives in `apps/api/scripts/` (not root `scripts/`) because it imports the engine.
- No quiz_versions / quiz_questions / quiz_options tables: the quiz stays in YAML. `quiz_attempts.user_id` references `auth.users` until `profiles` arrives in Phase 4.
- CI has three jobs: API (starts `supabase db start` and loads the seed if it's empty), Data (catalog check, and checks that scene logs, catalog and build agree), and Web.

## Working with this user

- They're learning as they build. Explain in **plain language with analogies** (Supabase = kitchen, Docker = room, images = flat-packed appliances, CLI = handyman). Keep tables short.
- They prefer "just asking, don't do anything yet" questions to be answered without acting.
- PC limits: 16 GB RAM (often under 1 GB free), a small C: drive. Run `pnpm db:start` (lean), not `db:start:full`. Web tests and builds are slow when RAM is tight.
- Shell: PowerShell on Windows. Git Bash's `pnpm` path is broken (Anaconda PATH), so run pnpm from PowerShell.
- Docker Desktop must be running before `pnpm db:start`; it's often closed after a restart.

## Next steps

> **Resume here (2026-10-02):** Phase 3 is functionally done (quiz → encounter → reveal). **First:** watch the reveal in the browser and tune `TIMING` / the stage if it feels off. **Next:** Phase 4 starting with naming (`player_dragons`, `POST /dragons`), or Phase 3 polish (item 3 below). The user commits themselves.

1. ✅ Quiz wording and dragon personality review (done 2026-10-01). After any later edit to `data/game/`, run `pnpm match:calibrate` and the tests, and add a line to CHANGELOG.md.
2. **Phase 3 UI:** ✅ quiz page. ✅ encounter scenes. ✅ reveal. Naming → Phase 4 (replace the disabled button on the reveal).
3. Polish: extreme personalities only reach ~76–80% compatibility; runner-up explanations fall back to vague text.
4. **User:** watch the films and confirm the scene logs (`yes?` → `yes`, source → `film`), then run `pnpm catalog:import && pnpm catalog:build && pnpm db:reset`.
5. Optional: deploy the Dragon Book (Vercel), keep filters in the URL, and fill in abilities and diet in the catalog.

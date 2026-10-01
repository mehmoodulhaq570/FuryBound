# Session overview: FuryBound / Dragon Academy

Summary of the Claude Code sessions of **2026-09-30 → 2026-10-01**. Read this first when picking the project back up. The full plan is [Plan.md](../Plan.md); tools are in [TECH_STACK.md](../TECH_STACK.md); the data workflow is in [data/README.md](../data/README.md).

## Where things stand

| Phase | Status |
|---|---|
| 0 Foundations | ✅ Done. CI green on GitHub |
| 1 Dragon database | ✅ Code done. ⏳ Film verification by the user (scene logs) |
| 2 Dragon Book | ✅ Done locally (Milestone M1). Not deployed yet |
| 3 Quiz + matching | ⏭️ Next: starts with writing the 12 quiz questions together |

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

## Decisions and deviations from Plan.md

- **Local Supabase only** during development, so the user can learn it. Hosted Supabase comes at launch.
- **Option 1 data:** all pre-filled rows go into the catalog (including low-confidence ones), labelled with confidence and sources, instead of waiting for film verification.
- `appearances` and `rider_links` also carry `source_ids` and `confidence`. Plan §8.3 didn't have them, but they're needed so every fact is traceable.
- Scene logs are the source of truth for `appearances.csv` and `rider_links.csv`: **edit the logs, not those two CSVs**.
- Species and individual ids share one namespace (`/dragon-book/<id>`). The validator enforces the Plan's `the_` rule (`light_fury` vs `the_light_fury`).
- CI has three jobs: API (starts `supabase db start` and loads the seed if it's empty), Data (catalog check, and checks that scene logs, catalog and build agree), and Web.

## Working with this user

- They're learning as they build. Explain in **plain language with analogies** (Supabase = kitchen, Docker = room, images = flat-packed appliances, CLI = handyman). Keep tables short.
- They prefer "just asking, don't do anything yet" questions to be answered without acting.
- PC limits: 16 GB RAM (often under 1 GB free), a small C: drive. Run `pnpm db:start` (lean), not `db:start:full`. Web tests and builds are slow when RAM is tight.
- Shell: PowerShell on Windows. Git Bash's `pnpm` path is broken (Anaconda PATH), so run pnpm from PowerShell.
- Docker Desktop must be running before `pnpm db:start`; it's often closed after a restart.

## Next steps

1. **Phase 3: quiz + matching.** Write the 7 trait definitions and 12 quiz questions (Plan §9.2), `species_profiles.yaml`, `engines/matching.py`, and the calibration script.
2. **User:** watch the films and confirm the scene logs (`yes?` → `yes`, source → `film`), then run `pnpm catalog:import && pnpm catalog:build && pnpm db:reset`.
3. Optional: deploy the Dragon Book (Vercel), keep filters in the URL, and fill in abilities and diet in the catalog.
4. Confirm or override the open decisions in Plan §18 before Phase 3 (the defaults are fine).

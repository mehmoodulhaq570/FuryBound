# Session overview: FuryBound / Dragon Academy

Summary of the Claude Code sessions of **2026-09-30 → 2026-10-03**. Read this first when picking the project back up. The full plan is [Plan.md](../Plan.md); what changed when is in [CHANGELOG.md](../CHANGELOG.md) (one section per phase); tools are in [TECH_STACK.md](../TECH_STACK.md); the data workflow is in [data/README.md](../data/README.md); setup and commands are in [README.md](../README.md).

## Where things stand

| Phase | Status |
|---|---|
| 0 Foundations | ✅ Done. CI green on GitHub |
| 1 Dragon database | ✅ Code done. ⏳ Film verification by the user (scene logs) |
| 2 Dragon Book | ✅ Done (Milestone M1). Not deployed |
| 3 Quiz + matching | ✅ Engine, quiz, encounter and animated reveal |
| 4 Profile + your dragon | ✅ Profiles, naming/adoption, species silhouettes, care + mood, discoveries. **Milestone M2 (MVP) reached in code**; not deployed |
| 5 Training | ✅ Engine, sessions API, 5 DOM mini-games, XP/levels/stages, refusals, progress chart (2026-10-02). **Not yet tried in a browser** |
| 6 AI companion | 🔨 **6a done (2026-10-03):** Ollama provider, structured memory, prompt, streaming chat, `/chat`. ⏭️ **6b:** AI-extracted memories (pgvector), Dragon's Journal, eval suite |

- **Tests:** 211 API (pytest, incl. Hypothesis property tests) + 88 web (Vitest), all passing on 2026-10-03. API lint/format/mypy and web lint/format/typecheck also pass.
- **Repo:** https://github.com/mehmoodulhaq570/FuryBound (public, branch `main`). The user commits and pushes **themselves**; don't push.
- **Names:** package and Supabase project `dragon-academy`; GitHub repo FuryBound; the app is called "Dragon Academy".
- **Docs refreshed 2026-10-02:** README rewritten as a professional project README; CHANGELOG regrouped into Phase 3 and Phase 4 sections (Unreleased is empty).

## The player flow (all built)

`/login` → `/academy/quiz` (12 questions) → "Step into the fog" → `/academy/encounter?attempt=<id>` (3 scenes) → `/academy/reveal?attempt=<id>` (top 3 circle, 2 peel away, "It chose you", name it) → `/dragon` (card, mood, thought, needs, feed/rest/play) → `/train` (level/XP, activities, progress chart) → `/train/<activity>` (mini-game → result, level-up) and `/dragon-book` (Academy mode: "???" for unmet dragons).

## What was built, by area

**Machine and setup (Phase 0)**
- Docker Desktop's WSL data is in `D:\DevTools\docker\wsl` (`docker_data.admin-owned.bak` there can be deleted). `C:\Users\mehmo\.wslconfig` caps WSL at 4 GB; the page file is mostly on D:; hibernation is off.
- `httpx2` in the API's dev dependencies is **legitimate and needed** (Starlette's TestClient wants it). Don't remove it.

**Dragon data (Phase 1)**: `data/`, `scripts/`, `supabase/migrations/`
- Scene logs `data/research/httyd{1,2,3}_scene_log.md` were pre-filled by Claude from the fan wiki (pinned revisions) and general knowledge; rows marked `yes?` / `no?` await the user's film check. Catalog: 50 species, 27 named dragons, 138 appearances, 25 rider links, 10 sources.
- Pipeline: `catalog:import` → `catalog:check` → `catalog:build` (→ `data/build/seed.sql`, `dragons.json`, `references.json`). Read-only canon API: `/movies`, `/species`, `/individuals`, `/search`.

**Dragon Book (Phase 2)**: `apps/web/src/app/dragon-book/`, `components/dragon-book/`, `lib/dragon-book/`
- Static pages from `@data/dragons.json`; Fuse.js search with word-aware re-ranking; 77 pre-built detail pages; confidence meters and franchise tags.
- Academy mode (Phase 4): `lib/dragon-book/academy.ts` (pure), `DragonBook` takes `academy`, `LockedCard`, `academy-book.tsx` (session + `GET /discoveries`). Searching never reveals a locked name.
- Each detail page links to the fan wiki via `Special:Search?go=Go`, so no link goes dead.

**Game data** (`data/game/`, all invented, validated on load)
- `traits.yaml`, `quiz_v1.yaml`, `species_profiles.yaml` (15 matchable species), `complements.yaml`, `encounter_v1.yaml`: these feed matching. **After editing them, run `pnpm match:calibrate`** (~2–3 min; CI checks it).
- `adoption.yaml` (starting values, name rules, 12 quirks, colour variants with hex) and `care.yaml` (decay rates, care effects and refusals, messages, idle thoughts): separate on purpose, so no recalibration is needed. Quirks, colours and thoughts are Claude's drafts for the user to review.

**Engines** (`apps/api/app/engines/`, pure and deterministic)
- `matching.py`: percentile-based matching, explanations, 60–99% compatibility, `get_calibration()`. Current shares: Scuttleclaw 14.2% (highest) … Light Fury 2.5%, Night Fury 0.7%.
- `adoption.py`: `roll_dragon` seeded by `adoption version + attempt id`; `clean_name` (whole-word blocklist, so "Cassandra" passes).
- `care.py`: `decay`, `care` → `CareOutcome` or `Refused`, `mood` (Plan §9.7 table; Scared waits for stories, Angry for Phase 5 refusals), `thought` (seeded by dragon id + hour).

**API services** (`apps/api/app/`)
- `quiz.py` (quiz, attempts, encounter; `own_attempt` locks with `FOR UPDATE`; finishing the encounter calls `discover()`), `dragons.py` (`Rulebook` = game + adoption + care; adopt, get, `look_after`), `discoveries.py`.
- All player tables are written by the API's postgres connection; RLS gives players owner-only **select**.
- `db/models.py`: `Base.type_annotation_map` makes every datetime timezone-aware (a bug before 2026-10-02).
- Shared test fixtures (`player`, `quiz_client`, `auth_headers`, `first_answers`, `_sql`, `_rows`) are in `tests/conftest.py`. `player` inserts a throwaway `auth.users` row; a trigger creates its profile.

**Web** (`apps/web/src/`)
- Quiz: `components/quiz/` (`quiz-flow`, `quiz-runner` with `storageKey`/`wording` props so the encounter reuses it, `trait-bars`, `notice`, `attempt-gate` for the id / sign-in / ownership checks).
- Encounter: `components/encounter/encounter-flow.tsx` (a finished attempt redirects to the reveal; it invalidates `["discoveries"]`).
- Reveal: `components/reveal/` (`reveal-flow` → `reveal` with phases circling → peel → landed and `TIMING`; `reveal-stage` uses Motion; `name-dragon` is passed in as the `naming` slot). Reduced motion = fades only; "seen" is kept in localStorage per attempt.
- Dragon: `components/dragon/` (`dragon-home`, `dragon-card` with a `care` slot, `care-panel`); `lib/dragon/` (`my-dragon.ts`, `name.ts`).
- Art: `lib/art/shapes.ts` (`BUILDS`: wings/head/tail/legs/body per species, generic fallback) → `components/art/dragon-silhouette.tsx`. To preview shapes, render them to HTML and screenshot with headless Chrome. Fade silhouettes with `opacity-*`, not `text-x/40`.

**Training (Phase 5)**
- `data/game/progression.yaml` (all numbers and messages; minimum plausible durations per activity) + `engines/training.py` (pure: `xp_to_next`, `stage_for`, `unlocked`, `check_can_train` → `Locked`/`Refused`, `check_duration` → `Implausible`, `complete` → `TrainingOutcome`).
- `app/training.py` (`overview`, `start`, `finish`, `history`) + `routers/training.py`. `Rulebook` now also holds `progression`. `dragons.state()` (needs + mood at a time) and `dragons.mine()` are shared helpers. Starting stores the mood and needs on the session. Finishing locks session + dragon (`FOR UPDATE`), checks expiry (30 min) and duration (in range and ≤ elapsed + 5 s), applies XP / stats / costs / trust, and logs `trained` and `level_up` events. A refusal logs a `refused` event (this feeds the Angry mood).
- `xp` on `player_dragons` is progress within the current level (it resets on level-up); `stage` is updated on level-up.
- Web: `components/training/` (`dragon-gate.tsx` = signed in + has a dragon; `train-home.tsx` with `XpBar`/`ActivityList`; `train-activity.tsx` with intro → playing (`TimedGame` times from mount) → result + level-up celebration; `stat-history.tsx` = small multiples, one hue, shared 0–100 scale, crosshair, table view, following the dataviz skill), `games/` (5 games + `use-timers.ts` with `useTimers`/`useFrames`, which clean up on unmount), `lib/training/` (`scoring.ts` pure scoring, `history.ts`, `api.ts`).
- Hypothesis was added as an API dev dependency.

**Species artwork** (2026-10-02)
- `scripts/build_species_images.py` (`pnpm art:build`, Pillow as an API dev dependency) → `apps/web/public/dragons/<species_id>.webp` (640 px, quality 80, about 53 KB each) + `apps/web/src/lib/art/species-images.json`. Files are matched to species by exact catalog name.
- `lib/art/images.ts` (`speciesImage`) + `components/art/dragon-portrait.tsx` (next/image, or the silhouette as fallback). Used in Dragon Book cards and detail pages, the reveal result and runners-up, and the `/dragon` card (+ a colour swatch).
- Screenshots of `/dragon-book` and `/dragon-book/toothless` checked; the reveal and `/dragon` need sign-in, so the user should check those.

**Phase 6a: chat** (2026-10-03)
- The user chose **Ollama** (free) now and Gemini later. The machine had only ~0.5 GB of RAM free, so the default is the user's existing **Ollama cloud model `nemotron-3-super:cloud`** (runs remotely through the local Ollama API). It's a *thinking* model, so requests send `think: false` (`OLLAMA_THINK`), or it spends the whole budget thinking. Verified with real prompts: in character, follows the format, uses memory, says it isn't Toothless. A rule was added after it said "hunger 78".
- `app/ai/providers.py` (`LLMProvider` protocol; `OllamaProvider` with an injectable httpx transport for tests; `FakeProvider(replies, fail=)`, which records `calls`; `get_llm` reads `app.state.llm`, created in the lifespan by `make_llm`, and tests get the fake). `app/ai/prompts.py` (`build_messages`, `check_reply`, `fallback`). `app/engines/memory.py` (`summarize` → `MemorySummary.lines()`; computed on demand, not stored in `memory_summary`). `app/chat.py` (`prepare` validates, applies the daily limit and saves the user message; `stream_reply` streams SSE and saves the reply with a **new session** from `app.state.sessionmaker`, because the request's session may be closed while streaming).
- `app.state.settings` now holds the app's own settings (routes should read it rather than `get_settings()` when tests need custom values).
- Web: `/chat` → `components/chat/chat-page.tsx` (history query, Narrated/Talking toggle kept in localStorage, `api.POST(..., { parseAs: "stream" })` + `TextDecoderStream` + `sseReader`, a `DragonReply` that renders actions and thoughts), `lib/chat/parse.ts` (the stream event types are written by hand there, since OpenAPI doesn't describe streams).
- Not done in 6a: token counts (Ollama returns them but the provider doesn't pass them on yet), Gemini, the eval suite. **The chat hasn't been tried in a browser yet.**

**Gameplay steps 2–5** (completed by Codex, authorized by the user; 2026-10-03)
- **Experience API**: `app/experience.py`, `routers/experience.py`, `schemas/experience.py`, registered in `main.py`. Achievements (`first_flight`, `care`, `ace`, `rescue`) unlock habitat decorations (camp, lanterns, flowers, pennant, beacon); a journal built from `dragon_events`; `next_milestone`; a one-time **Misty Cove rescue** (approach → a real flight training session owned by the mission → untie or lift; rewards XP, trust and the Scuttleclaw discovery; can't be farmed). All state lives in `dragon_events` (`habitat_decorated`, `rescue_mission`, `rescued`); no migration. Six API tests cover ownership, locked cosmetics, ordering, reward claims, expired sessions and exhausted dragons. The earlier lint/type errors are fixed.
- **Flight game redesign**: `components/training/games/flight-game.tsx` (+ `flight-game.module.css`) and `lib/training/flight-course.ts` (six fixed gates, `courseScore`, `steer`). `GameProps` gained `speciesId`, `color` and `agility`; `train-activity.tsx` passes them and invalidates `["experience", dragonId]`.
- **Habitat UI**: `components/dragon/dragon-habitat.tsx` + `habitat.module.css`: animated SVG dragon in its colour, care reactions, needs, earned decorations, primary flight/care action, rescue and chat links. Existing detailed profile is expandable. `components/experience/progress-panel.tsx` shows four achievements, the next stage's XP target and a diary on `/dragon` and `/train`.
- **Rescue UI**: `/adventure` and `components/experience/adventure-home.tsx`. Server state resumes after reload; flight completion uses the existing training endpoint; failed saves can be retried; expired unfinished flights get new sessions. The existing training curve, care rules, species artwork and chat implementation were preserved. Five web tests cover course scoring, steering, finishing once, pause timing and cleanup.
- Documented in CHANGELOG (Unreleased: "Changed" + "Gameplay additions") and README. No commits or pushes.
- **Browser validation:** signed in with a disposable local account, adopted a dragon, used care, completed the rescue flight, reloaded both unfinished and completed missions, persisted a beacon decoration, checked the training progress panel and the 390 px mobile habitat (no horizontal overflow). No page errors. The review account and its data were removed; existing accounts were preserved. Flight reports active duration so pauses do not exceed the activity's duration limit.

**Migrations** (applied locally with `supabase migration up`, which keeps the user's account; `db:reset` would wipe it)
`20260930063434_init_extensions` · `20260930150000_canon_tables` · `20261001120000_quiz_attempts` · `20261002120000_profiles_and_dragons` · `20261003120000_dragon_events` · `20261004120000_discoveries` (back-filled; the user's account has Light Fury, Stormcutter and Crimson Goregutter) · `20261006120000_chat_messages` (extra columns `mode`, `meta`) · `20261005120000_training_sessions` (extra columns: `mood`, `needs_at_start`, `duration_ms`, `stats_after`).

## Decisions and deviations from Plan.md

- **Local Supabase only** during development, so the user can learn it. Hosted Supabase comes at launch.
- All pre-filled catalog rows are included, labelled with confidence and sources, instead of waiting for film verification. `appearances` and `rider_links` carry `source_ids` and `confidence`. **Edit the scene logs, not `appearances.csv` / `rider_links.csv`.**
- Player traits are converted to **percentiles** before matching (summed scores cluster in the middle). Min–max scores are still used for display.
- Dropped `base_stats` (only `stat_caps`) and two complement rules. Legendary target is 0.5–3%.
- No quiz tables: the quiz stays in YAML. Never edit a quiz or encounter file players have taken; copy it to a new version.
- **One dragon per player** (`player_dragons.user_id` unique); extra columns `compatibility` and `rules_version`.
- Adoption and care data live in their own YAML files, outside the calibration fingerprint.
- **Discoveries are per species**; named dragons unlock with their species; the counter counts species; "new" = discovered in the last 24 h.
- Care refusals are 409s, not events; a dragon can't be fed when full or play when exhausted. **Training** refusals are 409s *and* `refused` events.
- Training: the "activity in likes → +happiness" rule was skipped (likes are foods and things, not activities); "overtraining" isn't defined yet. Scores are computed in the browser and only sanity-checked by duration, as the Plan says.
- **Art:** no film assets or copied designs (Plan §16). The user made 77 original GPT images in `dragons_images/` (gitignored; "original interpretations, not the DreamWorks designs"). Claude reviewed all 50 species images (contact sheets: fine, no text or logos) and **uses only the 50 species images**. The 27 named-dragon images are deliberately unused (e.g. the "Toothless" one is a purple feathered dragon); named dragons show their species' art with a caption. Locked Academy cards and the reveal's circling animation keep silhouettes.
- CI has three jobs: API (starts `supabase db start`, loads the seed if empty), Data (catalog and calibration checks) and Web.

## Working with this user

- They're learning as they build. Explain in **plain language with analogies** (Supabase = kitchen, Docker = room, CLI = handyman, the Dragon Book = sticker album). Keep tables short. When they say "didn't understand", give a simpler version with a short description.
- They prefer "just asking, don't do anything" questions to be answered without acting, often with a plain yes or no first.
- PC limits: 16 GB RAM (often under 1 GB free), a small C: drive. Run `pnpm db:start` (lean). Run web tests with `pnpm exec vitest run --maxWorkers=1` in `apps/web`; the default run can time out starting workers.
- Shell: PowerShell on Windows. Git Bash's `pnpm` path is broken (Anaconda PATH), so run pnpm from PowerShell. Very long Bash heredocs with mixed quotes can fail; write files with the Write tool instead.
- Docker Desktop must be running before `pnpm db:start`; it's often closed after a restart.

## Next steps

> **Resume here (2026-10-03):** Gameplay steps 2–5 are implemented: flight course, interactive habitat, one-time Misty Cove rescue, achievements, decorations and milestone XP. All 211 API and 88 web tests pass, plus lint, format and type checks. Try `/dragon`, `/train/flight` and `/adventure` to review difficulty and presentation. Phase 6a chat is preserved. **Next, if requested: 6b** — memory extraction after chats (`generate_json`), `dragon_memories` with pgvector (`vector(768)`, extension already enabled; needs an embedding model, e.g. `nomic-embed-text` via Ollama), dedup at cosine > 0.9, retrieval score, a memory management `/journal` page (list, pin, delete, wipe), then the eval suite (Plan §13). The gameplay diary already exists and is distinct from AI memory management.
>
> **Earlier (2026-10-02):** Phase 5 (training) is built. The user hasn't checked anything after quiz → encounter in a browser. **First:** have them try `/train` (play Flight and Speed, check the chart and a level-up) plus the earlier untested parts (reveal animation, naming, care, Academy mode), and commit. **Then** choose: Phase 6 (AI companion + memory), polish, or deploying.

1. ✅ **Phase 5: training.** **Next in the Plan: Phase 6, AI companion + memory** (Plan §9.8–9.9: chat with your dragon, Gemini/Ollama, memories with pgvector). Small follow-ups: `DragonHome` could reuse `DragonGate`; nobody has played the games yet, so tune difficulty after the user tries them.
2. **Deploy** (when wanted): hosted Supabase, Vercel for the web app, a host for the API. The Plan's sign-up flow (email confirmation, profile display names) needs a look then.
3. **Polish:** extreme personalities only reach ~76–80% compatibility; runner-up explanations can be vague; filters aren't kept in the URL; abilities and diet are missing from the catalog.
4. **User:** review `adoption.yaml` and `care.yaml` drafts; watch the films and confirm the scene logs (`yes?` → `yes`, source → `film`), then run `pnpm catalog:import && pnpm catalog:build && pnpm db:reset`.
5. After any edit to the matching files in `data/game/`: `pnpm match:calibrate`, the tests, and a CHANGELOG line.

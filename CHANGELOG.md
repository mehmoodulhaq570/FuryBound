# Changelog

All notable changes to FuryBound / Dragon Academy. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Dates are YYYY-MM-DD. Phases refer to the roadmap in [Plan.md](Plan.md#12-roadmap-phases-08).

## [Unreleased]

### Added
- **Talk to your dragon** (Phase 6a) at `/chat`. Replies stream in as they're written. By default the dragon answers the canon way, with what it does (*in italics*) and a short 💭 thought; a **Talking** switch (labelled non-canon fun) lets it speak. "Chat" is in the header and "Talk to …" is on `/dragon`.
- The dragon's **prompt** is built on the server from what the game knows: canon species facts from the database (class marked *franchise* where it applies), its card (stage, personality, quirks, likes, dislikes), its state (mood, needs, trust), its last 3 events, its memory and the last 10 messages. It's told to stay in character, never claim to be a film dragon (it says it isn't Toothless), only use the canon facts given, and show stats through behaviour rather than numbers.
- **Structured memory** (Plan §9.9, tier 1): worked out from the dragon's diary with no AI — favourite food, best activity, foods it was given and dislikes, refusals, how often you fed, played and trained, days together and a daily streak. `GET /dragons/{id}/memory`.
- **AI providers** behind one interface: **Ollama** (a local model, or an Ollama `:cloud` model that runs on Ollama's servers and uses no local RAM; default `nemotron-3-super:cloud` with thinking switched off) and a **fake** one for tests. Gemini can be added later as another implementation. Settings: `LLM_PROVIDER`, `OLLAMA_URL`, `OLLAMA_CHAT_MODEL`, `OLLAMA_THINK`, `CHAT_DAILY_LIMIT`.
- **Guardrails**: messages of up to 500 characters, 100 messages per day per dragon (429 after that), replies cut at about 100 words, and replies that break character ("as an AI…", "I'm Toothless") or fail are replaced with a stock line (*"Ember tilts its head, confused…"*), so chat never breaks the game. Each reply records which model answered, how long it took and whether the fallback was used.
- **API**: `POST /dragons/{id}/chat` (server-sent events: `delta` pieces, then one `done` with the checked, saved reply) and `GET /dragons/{id}/messages`. `chat_messages` table (migration `20261006120000_chat_messages.sql`). Chatting is logged as a `chatted` event.
- Tests: the API suite is now 205 tests (Ollama client against a mocked network, prompt building, reply checks, memory, chat endpoints with a fake AI) and the web suite 83.

### Changed
- **Flight training is now a flight course**: steer your dragon (arrow keys, Climb/Dive, or Space to climb) through six glowing gaps between sea stacks. Your dragon is drawn in its own colour, and missing a gate costs points but never ends the run. The course is fixed (`lib/training/flight-course.ts`), and the score still follows the same 0–100 activity contract. Games can now receive the dragon's species, colour and agility.

### Gameplay additions
- **Playable 2D home**: an original layered side-view dragon supports the 15 adoptable species' main anatomical differences, with walking, blinking, tail and wing motion, eating, sleeping, happy reactions, takeoff and landing. Tap the meadow or use arrow keys to guide it; interact with the food basket, nest, ball and dragon. Optional synthesized sounds start only through player interaction; motion respects the reduced-motion setting. Detailed care controls remain available.
- **Island exploration** at `/island`: fly between home, shore, clearing, cove and lookout. Three persistent keepsakes unlock the lookout and award 40 XP once, using the existing level curve. Owner checks and row locks prevent duplicate rewards, including concurrent requests.
- **Fishing** is a free timing game; sharing a catch uses the existing feeding API and its refusals. Flight has animated wings and collectible sparks; target practice has visible bullseyes, a dragon and hit feedback. The rescue now includes interactive knots or lifting before its existing server completion.
- **Decoration arrangement**: place multiple earned decorations in the habitat and reload to find them in the same positions. Validated server coordinates and unlock checks are persisted in `dragon_events`; no database migration.
- **API**: `GET /dragons/{id}/island`, `POST /dragons/{id}/treasures/{treasure}`, `POST /dragons/{id}/habitat-layout`. Generated API types updated. Free movement and petting do not grant XP or change care stats.
- Validation: 213 API tests passed. All 94 web tests verified (92 passed in the full run; two timed out at 5 seconds and passed a targeted retry with a 20-second limit). Lint, formatting and type checks pass. Desktop and mobile browser checks covered care, exploration, fishing, rescue and saved decorations using disposable accounts.
- **Interactive habitat** at `/dragon`: a coastal nest with idle and mood animations, feed/rest/play reactions, needs, a suggested next activity and links to training, chat and discoveries. The existing dragon profile and stats remain available in an expandable panel. Animations respect reduced motion.
- **Habitat, achievements and the Misty Cove rescue** (`GET /dragons/{id}/experience`, `POST /dragons/{id}/decoration`, `POST /dragons/{id}/adventure`, `POST /dragons/{id}/adventure/{run_id}/choice`), with the playable `/adventure` page and progress panels on `/dragon` and `/train`.
  - Four achievements (first training session, three care actions, a score of 80+, the rescue) each unlock a habitat decoration: lanterns, flowers, a pennant or a beacon (the camp is always available).
  - An adventure journal written from the dragon's diary, and the next stage to reach with the XP still needed.
  - A one-time rescue mission: choose an approach (gentle, bold or clever), fly the flight course through the cove (a real training session), then free a trapped Scuttleclaw by untying or lifting the net. How well it goes depends on the dragon's personality, stats and flight score; it earns XP, trust and the Scuttleclaw discovery, and can't be repeated for more rewards.
  - Stored entirely in `dragon_events` (no new tables).
  - Reloads resume the mission. Expired unfinished flights get a fresh session; failed saves can be retried. Ownership checks and dragon row locks protect choices and one-time rewards.
- **Flight controls** support keyboard and touch, pause/resume, automatic pause when the tab is hidden, and feedback at each gate. Paused time is excluded from the submitted duration. Scores continue through the existing training API and XP curve.
- Six API tests cover experience, earned decorations, mission order, one-time rewards, ownership, expiry and exhausted dragons; five web tests cover course scoring, controls, pause timing and cleanup.

### Fixed
- Routes now read the settings their app was created with (`app.state.settings`), so test settings such as a lower chat limit apply.
- **Species artwork** for all 50 species: original AI-generated interpretations of each species' general traits, colours and personality (README "Artwork"). They deliberately don't reproduce DreamWorks' character designs and contain no logos or film text. All 50 were reviewed before being added.
  - Shown in the Dragon Book (thumbnails on the list; a large image with a caption on each page), on the reveal (the dragon that chose you and the runners-up) and on My dragon (with a swatch of your dragon's own colour).
  - **Named dragons use their species' artwork** (Toothless's page shows the Night Fury image, captioned as species art). The 27 named-dragon images were made but are deliberately not used.
  - Locked "???" cards in Academy mode keep the silhouette, so art isn't spoiled. Any species without an image falls back to its silhouette; the reveal's circling animation still uses silhouettes.
  - `pnpm art:build` (`scripts/build_species_images.py`, Pillow) turns the originals in `dragons_images/` (2–3 MB PNGs, not committed) into 640 px WebP files in `apps/web/public/dragons/` (about 53 KB each, 2.6 MB in total) and writes the list of species with art. Rerun it after adding or replacing an image.

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

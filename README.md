# FuryBound · Dragon Academy

[![CI](https://github.com/mehmoodulhaq570/FuryBound/actions/workflows/ci.yml/badge.svg)](https://github.com/mehmoodulhaq570/FuryBound/actions/workflows/ci.yml)

**A dragon-companion web game built on a sourced dataset of every dragon in the three *How to Train Your Dragon* films.** Take a personality quiz, meet a dragon in the fog, and let it choose you. Then name it, look after it and fill in your Dragon Book.

> **Fan project.** Not affiliated with or endorsed by DreamWorks Animation or Universal Pictures. *How to Train Your Dragon* names and characters belong to their owners. The project uses no film assets: all artwork is original.

---

## Contents

- [Features](#features)
- [How it works](#how-it-works)
- [Tech stack](#tech-stack)
- [Getting started](#getting-started)
- [Development](#development)
- [API](#api)
- [Project structure](#project-structure)
- [Data and sources](#data-and-sources)
- [Artwork](#artwork)
- [Roadmap](#roadmap)
- [Documentation](#documentation)

## Features

| | |
|---|---|
| **Dragon Book** | All 50 species and 27 named dragons from the three films, with search, filters, films and riders per dragon, sources and a confidence rating on every fact. |
| **Personality quiz** | 12 scenario questions score 7 traits (courage, curiosity, loyalty, aggression, patience, independence, intelligence). |
| **The encounter** | Three short scenes (first contact, an offering, a thunderclap). How you meet the dragon shifts the result. |
| **"It chose you"** | An animated reveal: your top three dragons circle overhead, two peel away and one lands, with a compatibility score and the reasons for the match. Works with reduced motion. |
| **Your dragon** | Name it and it's yours: its own personality variation, quirks, colour and starting stats. |
| **Care and mood** | Needs change while you're away. Feed it (it has favourite and hated foods), let it rest, play with it. It has moods and idle thoughts, and it will tell you no. |
| **Training** | Five mini-games (flight, speed, accuracy, memory, obedience) earn XP and raise stats. Your dragon levels up through five stages, unlocks new activities, and refuses when it's exhausted. A chart shows how its stats grew. |
| **Talk to your dragon** | Chat with your dragon. It answers with body language and a thought (or speaks, in the just-for-fun Talking mode), knows its species facts, mood and needs, and remembers what you've done together. Replies stream in as they're written. |
| **Habitat and rescue** | An animated coastal habitat reacts to care and mood. Four achievements unlock decorations, a journal records your story, and `/adventure` offers a one-time Misty Cove rescue with personality-based choices and a playable flight course. |
| **Academy mode** | Signed in, the Dragon Book becomes a collection: dragons you haven't met show as "???" until you discover them. |

## How it works

```
 Browser (Next.js)                         FastAPI                         Supabase (Postgres)
 ─────────────────                         ───────                         ───────────────────
 Dragon Book (static, from dragons.json)
 Quiz → Encounter → Reveal → My dragon ──► /api/v1/...  ── engines ──►    canon tables (seeded)
        TanStack Query, typed client        matching · adoption · care · training     player tables (RLS)
        Supabase Auth (JWT) ───────────────► verifies JWT                  auth.users → profiles
```

- **Four data layers.** Canon facts (sourced from the films) are kept apart from invented game data (`data/game/*.yaml`), player data (Postgres) and generated content. Game-layer values are never presented as film facts.
- **Pure, deterministic engines.** Matching, adoption, care and training are plain Python functions with no I/O: the same input always gives the same dragon, and they're unit-tested in isolation, with property tests (Hypothesis) for promises like "a higher score never gives less XP".
- **Calibrated matching.** A Monte Carlo simulation of 100,000 random players checks that every dragon is a reachable match and that legendary dragons stay rare. CI fails if the game data changes without recalibrating.
- **Lazy simulation.** A dragon's needs are worked out from the time since your last visit when you come back, so nothing runs in the background.
- **One source of truth for types.** The frontend's API types are generated from FastAPI's OpenAPI schema; CI fails if they drift.

## Tech stack

| Area | Tools |
|---|---|
| Web | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4, TanStack Query, Motion, Fuse.js |
| API | Python 3.14, FastAPI, Pydantic, SQLAlchemy 2 (async) + asyncpg, managed with uv |
| Database and auth | Supabase (Postgres with row-level security, Supabase Auth), run locally in Docker |
| Quality | Vitest + Testing Library, pytest + Hypothesis, Ruff, mypy (strict), ESLint, Prettier, pre-commit |
| CI | GitHub Actions: API, Data and Web jobs |

See [TECH_STACK.md](TECH_STACK.md) for versions and the reasons behind each choice.

## Getting started

### Prerequisites

- Node.js 22+ and pnpm 10
- [uv](https://docs.astral.sh/uv/) (installs Python 3.14 for you)
- The [Supabase CLI](https://supabase.com/docs/guides/cli)
- Docker Desktop, **running**, for the local database
- [Ollama](https://ollama.com) for the dragon's chat. The default model, `nemotron-3-super:cloud`, runs on Ollama's servers (run `ollama signin` once); a local model such as `llama3.2:3b` works too (`ollama pull llama3.2:3b`, then set `OLLAMA_CHAT_MODEL`) but needs a few GB of free RAM. Without Ollama the dragon answers with a stock line, and everything else works.

### Setup

```sh
pnpm install                       # web dependencies
uv sync --directory apps/api       # API dependencies
uvx pre-commit install             # git hooks

pnpm db:start                      # local Supabase in Docker: applies migrations and the dragon seed
```

Create the environment files from the examples. `supabase status` prints the local values.

| File | From | Notes |
|---|---|---|
| `apps/web/.env.local` | `apps/web/.env.example` | Set `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` to the **Publishable** key. |
| `apps/api/.env` | `apps/api/.env.example` | The defaults work locally. Set `SUPABASE_JWT_SECRET` only if your project signs tokens with the legacy HS256 secret. |

> **Low on memory?** `pnpm db:start` starts only the Supabase services the app needs. Use `pnpm db:start:full` for everything, including Storage and Realtime.

### Run

In two terminals:

```sh
pnpm dev:api    # API on http://localhost:8000 (interactive docs at /api/v1/docs)
pnpm dev:web    # Web app on http://localhost:3000
```

Then:

1. Open http://localhost:3000 and create an account at **Sign in**.
2. Choose **Find your dragon**: take the quiz, step into the fog and see which dragon chooses you.
3. Name it, then visit **My dragon** to look after it.
4. **Train** it in the mini-games to level it up.
5. Open the **Dragon Book** to see what you've discovered.

Supabase Studio (a database browser) runs at http://localhost:54323.

## Development

| Task | Command |
|---|---|
| Run every check (what CI runs) | `pnpm check` |
| API checks only: lint, format, types, tests | `pnpm check:api` |
| Web checks only: lint, format, types, tests | `pnpm check:web` |
| Regenerate frontend API types after changing the API | `pnpm gen:api-types` |
| New database migration | `supabase migration new <name>` |
| Apply new migrations, keeping local data | `supabase migration up` |
| Rebuild the local database from scratch (migrations + seed) | `pnpm db:reset` |
| Recalibrate matching after editing the quiz or species profiles | `pnpm match:calibrate` |
| Rebuild the species artwork from `dragons_images/` | `pnpm art:build` |
| Scene logs → catalog appearances and riders | `pnpm catalog:import` |
| Validate the dragon catalog | `pnpm catalog:check` |
| Rebuild the seed and dragon exports from the catalog | `pnpm catalog:build` |

**Tests.** The API suite (pytest) runs against the seeded local database and skips database tests if it isn't running (CI never skips them). The web suite uses Vitest. On machines with little free memory, run web tests with one worker: `pnpm --filter web exec vitest run --maxWorkers=1`.

**Conventions.** Commit `apps/api/openapi.json` and `apps/web/src/lib/api/schema.d.ts` together. Never edit a quiz or encounter file that players have taken: copy it to a new version (`quiz_v2.yaml`). Notable changes go in [CHANGELOG.md](CHANGELOG.md).

## API

All routes are under `/api/v1`. Try them at http://localhost:8000/api/v1/docs.

**Public, read-only**

| Method | Path | Returns |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/movies` | The three films |
| GET | `/species` · `/species/{id}` | Species (filter with `?movie=httyd2`), or one with its films, named dragons and sources |
| GET | `/individuals` · `/individuals/{id}` | Named dragons, or one with its species, films, riders and sources |
| GET | `/search?q=` | Species and named dragons by name |

**Signed in** (Supabase JWT in `Authorization: Bearer …`)

| Method | Path | Does |
|---|---|---|
| GET | `/me` | The signed-in user |
| GET | `/quiz` | The active quiz, without scores, options shuffled per player |
| POST | `/quiz/attempts` | Score and save quiz answers |
| GET | `/quiz/attempts/{id}` | An attempt, with its match once finished |
| GET | `/encounter` | The three encounter scenes |
| POST | `/quiz/attempts/{id}/encounter` | Submit encounter choices; ranks the dragons (once per attempt) |
| POST | `/dragons` | Name and adopt the dragon that chose you |
| GET | `/dragons/me` | Your dragon: needs as of now, mood, idle thought, stats |
| POST | `/dragons/{id}/feed` · `/rest` · `/play` | Care actions (409 with the dragon's reason if it refuses) |
| GET | `/dragons/{id}/training` | Level, XP and every activity with its lock state |
| POST | `/dragons/{id}/training-sessions` | Start a session (403 if locked, 409 if the dragon refuses) |
| POST | `/training-sessions/{id}/complete` | Report the activity's score and duration (once): XP, stat gains, level-ups |
| GET | `/dragons/{id}/history` | Finished sessions with the stats after each |
| POST | `/dragons/{id}/chat` | Say something; the reply streams back as server-sent events |
| GET | `/dragons/{id}/messages` | The latest 50 chat messages |
| GET | `/dragons/{id}/memory` | What the dragon remembers from your time together |
| GET | `/dragons/{id}/experience` | Achievements, habitat decoration, journal, next milestone, rescue state |
| POST | `/dragons/{id}/decoration` · `/adventure` · `/adventure/{run_id}/choice` | Decorate the habitat; start and play the Misty Cove rescue |
| GET | `/discoveries` | The dragons you've met |

## Project structure

```
apps/
  web/            Next.js app: Dragon Book, quiz, encounter, reveal, dragon home, training
  api/            FastAPI app
    app/engines/  Pure game engines: matching, adoption, care, training, memory
    app/ai/       AI providers (Ollama, fake) and the dragon's prompt
    app/routers/  HTTP routes          app/schemas/  Request and response models
    tests/        pytest suite         scripts/      Matching calibration
data/
  research/       Scene logs per film (the source of truth for appearances)
  catalog/        Curated CSVs: species, named dragons, appearances, riders, sources
  game/           Invented game data: traits, quiz, species profiles, adoption, care, progression
  build/          Generated: seed.sql, dragons.json, matching calibration
scripts/          Catalog import, validation and build
supabase/         Local Supabase config and SQL migrations (the schema source of truth)
```

## Data and sources

The catalog was first drafted from the fan wiki (pinned revisions) and general knowledge, and is being verified against the films scene by scene. Every species, named dragon, appearance and rider link carries its **sources** and a **confidence** level, and the Dragon Book shows both. Facts from outside the films (such as dragon classes) are marked *franchise*. See [data/README.md](data/README.md) for the workflow.

Game values (personalities, quirks, stats, care rules) are invented for play and live in `data/game/`. They are never presented as film facts.

## Artwork

The project uses **no film assets**: no stills, official renders, logos, music or footage (see [Plan.md](Plan.md) §16).

- **Species artwork.** All 50 species have an original AI-generated image, based on each species' general traits, colours and personality. They are interpretations, not copies: they deliberately don't match the official character designs, so they may look noticeably different from the films. Named dragons (Toothless, Stormfly, ...) are shown with their species' artwork and a caption saying so.
- **Silhouettes.** Original shapes built in code from simple parts (wings, head, tail, legs). They're used where art would spoil a surprise (locked "???" Dragon Book cards, the reveal's circling dragons) and for any species without an image yet.
- **Rules for any artwork added:**
  - One image per **species**, never per named film character (no "Toothless" portrait).
  - No logos, film titles or text in the images.
  - Never generated by asking for an official design by name; describe an original dragon instead.
  - Reviewed before it's added. The originals stay out of git (`dragons_images/` is ignored); `pnpm art:build` turns them into small web images in `apps/web/public/dragons/`.
- Each Dragon Book page links to the fan wiki for anyone who wants to see the film designs.

## Roadmap

| Phase | | Status |
|---|---|---|
| 0 | Foundations: monorepo, CI, local Supabase | ✅ Done |
| 1 | Dragon database: catalog, pipeline, read-only API | ✅ Done (film verification ongoing) |
| 2 | Dragon Book | ✅ Done |
| 3 | Quiz, encounter, matching engine and reveal | ✅ Done |
| 4 | Your dragon: adoption, care, mood, discoveries (**MVP**) | ✅ Done |
| 5 | Training: activities, XP, levels and unlocks | ✅ Done |
| 6 | AI companion with memory | 🔨 Chat and structured memory done; AI memories and the journal next |
| 7 | Mini-games and arena | Planned |
| 8 | AI adventure mode | Planned |

The full plan, with the game design, data model and milestones, is in [Plan.md](Plan.md).

## Documentation

| Document | What's in it |
|---|---|
| [Plan.md](Plan.md) | Vision, game design, data model, API, roadmap and risks |
| [TECH_STACK.md](TECH_STACK.md) | The tools used and why |
| [CHANGELOG.md](CHANGELOG.md) | Notable changes, by phase |
| [data/README.md](data/README.md) | How the dragon catalog is researched, checked and built |

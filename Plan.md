# Dragon Academy — Project Plan

> An interactive AI + game + ML project built on a sourced dataset of every dragon in the three *How to Train Your Dragon* animated films.
> The player enters the world as a new trainer, gets chosen by a dragon, trains it, talks to it, and goes on adventures with it.

**Status:** Planning · **Last updated:** 2026-09-30

---

## Table of contents

1. [Vision](#1-vision)
2. [Scope and canon rules](#2-scope-and-canon-rules)
3. [Core principle: four data layers](#3-core-principle-four-data-layers)
4. [Product overview](#4-product-overview)
5. [System architecture](#5-system-architecture)
6. [Tech stack](#6-tech-stack)
7. [Repository structure](#7-repository-structure)
8. [Data model](#8-data-model)
9. [Feature specifications](#9-feature-specifications)
10. [API design](#10-api-design)
11. [Frontend routes](#11-frontend-routes)
12. [Roadmap (phases 0–8)](#12-roadmap-phases-08)
13. [Testing and quality](#13-testing-and-quality)
14. [Environments and deployment](#14-environments-and-deployment)
15. [Security, privacy, cost, accessibility](#15-security-privacy-cost-accessibility)
16. [Legal and IP](#16-legal-and-ip)
17. [Risks](#17-risks)
18. [Open decisions](#18-open-decisions)
19. [Immediate next steps](#19-immediate-next-steps)
20. [Appendix A: Catalog templates](#appendix-a-catalog-templates)
21. [Appendix B: Starter entity list](#appendix-b-starter-entity-list)

---

## 1. Vision

A dragon database on its own is just a viewer. **Dragon Academy** uses the dataset as the foundation for three things:

| Pillar | What it gives the player | Where the data matters |
|---|---|---|
| **Database** | A trustworthy, searchable Dragon Book (think Pokédex) | Species, individuals, abilities, film appearances, sources |
| **Game** | A dragon of your own to train, level up, race and adventure with | Species base stats, diets, abilities drive gameplay |
| **AI** | A companion that behaves according to its species, mood and history, and remembers you | Canon facts ground the AI; memories personalise it |

The defining moment: **"The dragon chooses you."** A personality quiz plus a short interactive encounter produce a compatibility result, revealed with an animation, instead of a flat "You got a Night Fury."

### Goals

- Canon-accurate: every canon fact in the database traces to a source and a film.
- Playable early: a working MVP after Phase 4 (encyclopedia + quiz + your own dragon).
- Grows in layers: each later phase adds to the same data and engines, with no rewrites.
- Portfolio-worthy: demonstrates data engineering, full-stack, applied ML, LLM engineering and game dev.

### Non-goals

- Reproducing the films' art, music or footage.
- Dragon-vs-dragon combat. Competitions are races, courses and rescues, in keeping with the films' theme.
- Multiplayer at launch (possible later).

---

## 2. Scope and canon rules

### 2.1 Canon scope

Canon is **strictly the three animated films**:

| ID | Title | Year |
|---|---|---|
| `httyd1` | How to Train Your Dragon | 2010 |
| `httyd2` | How to Train Your Dragon 2 | 2014 |
| `httyd3` | How to Train Your Dragon: The Hidden World | 2019 |

**Out of canon scope:** TV series (*Riders/Defenders of Berk*, *Race to the Edge*, *Rescue Riders*, *The Nine Realms*), shorts and specials (*Legend of the Boneknapper Dragon*, *Book of Dragons*, *Gift of the Night Fury*, *Homecoming*), Cressida Cowell's books, the 2025 live-action film, games and *School of Dragons*.

### 2.2 When non-film information is allowed

Some useful information only exists outside the films. It may be stored **only when flagged** with `source_scope = 'franchise'`. It is never presented as film canon. Two examples:

- **Dragon classes** (Strike, Sharp, Boulder, Stoker, Mystery, Tidal, Tracker…) come mostly from franchise material. Verify each one and flag it.
- **Names of the three Night Lights** (the Night Fury × Light Fury hatchlings at the end of *The Hidden World*) come from outside the films. Verify whether any name is spoken or shown on screen.

### 2.3 Appearance types

Each entity's presence in each film gets exactly one of these appearance types:

| Type | Meaning | Example |
|---|---|---|
| `featured` | Named individual with a role in the story | Toothless in all three films |
| `on_screen` | Species or individual clearly seen and identifiable | A species present in a crowd, battle or nest scene |
| `background` | Visible but incidental, only identifiable on close inspection | Dragons in wide shots of Berk |
| `mentioned` | Named in dialogue but not seen | A species named in conversation |
| `pictured` | Seen only as a drawing, carving, book page or object | Entries shown in the Book of Dragons |

### 2.4 Species vs individuals

**Species** and **individuals** are different entities. This matters for the database, the encyclopedia and the matching system.

```
Species:     Night Fury        Individual:  Toothless  (species = night_fury)
Species:     Deadly Nadder     Individual:  Stormfly   (species = deadly_nadder)
```

The player's dragon is always **a new individual of a species**, and never a canon individual. You don't get Toothless; you might get your own Night Fury.

### 2.5 In-world setting

*The Hidden World* ends with dragons leaving humanity. The Academy therefore needs a place in the timeline:

- **Default:** an original island ("the Academy Isle") in an unspecified era while dragons and Vikings live together, broadly between *HTTYD 2* and *The Hidden World*.
- Canon characters may appear only as **cameos** (e.g., as arena rivals or story mentions). Generated content must never rewrite canon events.

---

## 3. Core principle: four data layers

Everything in the project belongs to exactly one layer. This is the most important rule in this plan.

| Layer | Contents | Written by | Changes | Example |
|---|---|---|---|---|
| **1. Canon** | Facts from the three films | You (research), via catalog files | Only through reviewed catalog edits | Toothless is a Night Fury; Hiccup rides him |
| **2. Franchise** | Facts from outside the films, always flagged | You, via catalog files | Same as canon | Night Fury class = Strike |
| **3. Game** | Invented balancing values | You (design), via game config | Tuned freely | Night Fury base speed 95; trait vector; rarity |
| **4. Generated** | Per-player output from gameplay and the AI | System / LLM | Constantly, per player | "Ember likes fish"; story chapters |

**Rules**

1. Generated data never flows back into canon, franchise or game data.
2. The LLM receives canon facts through retrieval and may not invent species facts (abilities, diet, anatomy).
3. The UI always shows which layer a value comes from. Game stats are labelled as Academy ratings, not film facts.
4. The engines (matching, training, mood, story) are **IP-agnostic**: they read species data from the database and hard-code nothing about HTTYD. (See §16.)

---

## 4. Product overview

### 4.1 Feature map

```
                          DRAGON ACADEMY
                               │
          ┌────────────────────┼────────────────────┐
          ↓                    ↓                    ↓
   Discover a Dragon      Train Dragon       Explore Dragons
          │                    │                    │
          ↓                    ↓                    ↓
  Quiz + Encounter       Mini-games + Arena   Dragon Book (Encyclopedia)
          │                    │                    │
          └──────────→   YOUR DRAGON   ←────────────┘
                               │
                 ┌─────────────┼─────────────┐
                 ↓             ↓             ↓
               Stats        Memories     Relationship
                 └─────────────┼─────────────┘
                               ↓
                 AI COMPANION  +  AI ADVENTURES
```

### 4.2 Player journey

1. **Arrive.** Browse the Dragon Book without an account.
2. **Sign up.** Take the personality quiz (about 12 questions).
3. **Encounter.** Play three short interactive scenes: first contact, an offering, a sudden startle.
4. **Reveal.** Three silhouettes circle; two fly away; one lands. *"It chose you."* Then name your dragon.
5. **Home.** Look after your dragon's needs (hunger, energy, happiness), watch its mood, and build trust.
6. **Train.** Play activities and mini-games to gain XP and stats. The dragon levels up through stages and unlocks new content.
7. **Talk.** Chat with your dragon. It remembers what you do together.
8. **Compete.** Race and run courses against canon rider-and-dragon pairs in the Arena.
9. **Adventure.** Play AI-generated branching stories starring your dragon, its personality and your shared history.
10. **Collect.** Dragon Book entries unlock as you encounter species throughout.

---

## 5. System architecture

```
┌────────────────────────────── Browser ──────────────────────────────┐
│  Next.js (App Router) + Tailwind + TanStack Query                    │
│   ├─ Pages: Dragon Book, Quiz, Reveal, Dragon Home, Train, Chat, ... │
│   └─ Phaser canvas (mini-games), Motion (reveal animation)           │
└───────────┬───────────────────────────────────────┬─────────────────┘
            │ Supabase Auth (sign-in, JWT)          │ REST + SSE, Bearer JWT
            ▼                                       ▼
   ┌─────────────────┐              ┌────────────────────────────────────┐
   │  Supabase Auth  │              │  FastAPI                            │
   └─────────────────┘              │   ├─ canon service (read-only)      │
                                    │   ├─ engines/ (pure functions)      │
                                    │   │    matching · training · needs  │
                                    │   │    mood · checks · rewards      │
                                    │   ├─ ai/                            │
                                    │   │    providers · prompts · memory │
                                    │   │    chat · story                 │
                                    │   └─ routers/ (HTTP layer)          │
                                    └──────┬───────────────────┬─────────┘
                                           │ SQL (asyncpg)     │ HTTPS
                                           ▼                   ▼
                              ┌──────────────────────┐  ┌──────────────────┐
                              │ Postgres (Supabase)  │  │ Gemini API (prod)│
                              │  + pgvector          │  │ Ollama (local)   │
                              └──────────────────────┘  └──────────────────┘

 Offline pipeline (Python):
   data/catalog/*.csv ──validate──► build ──► dragons.json · dragons.csv · seed.sql
   data/game/*.yaml   ──validate──► build ──► game seed + calibration report
```

### Key architectural decisions

| Decision | Choice | Why |
|---|---|---|
| Source of truth for canon | CSV files in git, not the database | Reviewable diffs, easy editing, rebuildable DB |
| Who writes to the database | **FastAPI only** | Game logic and scoring stay server-side and cheat-resistant |
| Game logic location | Pure functions in `engines/` with no I/O | Easy to unit-test, property-test and calibrate offline |
| Dragon Book rendering | Static generation from `dragons.json`; discovery state fetched from API | Fast, cheap, SEO-friendly |
| Needs and mood | Computed lazily from timestamps on read | No background jobs or cron needed |
| LLM access | Behind a `LLMProvider` interface | Swap Gemini/Ollama by config; test with a fake |
| Frontend types | Generated from FastAPI's OpenAPI schema | One contract; no hand-written duplicate types |

---

## 6. Tech stack

| Area | Technology | Notes |
|---|---|---|
| Frontend | **Next.js** (App Router, TypeScript) + **Tailwind CSS** | TanStack Query for server state; Zustand for small client state |
| Animation | **Motion** (Framer Motion) | Reveal animation, stat bars, transitions; respects reduced motion |
| Game | **Phaser** | Mini-games in a client-only component (`dynamic(..., { ssr: false })`) |
| Backend | **FastAPI** (Python 3.12+) + **Pydantic v2** | SQLAlchemy 2 (async) + asyncpg |
| Database | **PostgreSQL via Supabase** + **pgvector** | Supabase CLI for local dev and migrations |
| Auth | **Supabase Auth** | FastAPI verifies JWTs against Supabase JWKS |
| AI | **Gemini API** (production), **Ollama** (local and offline dev) | Behind `LLMProvider`; structured JSON outputs |
| ML / analysis | **Python + scikit-learn**, NumPy, pandas | Calibration (Monte Carlo), clustering, weight learning |
| Data pipeline | Python scripts + Pydantic validation | Builds JSON, CSV and SQL seed |
| Images | Original, commissioned or generated artwork | No film assets (see §16) |
| Tooling | **pnpm** (JS), **uv** (Python), Ruff, ESLint, Prettier, pre-commit | |
| Testing | pytest, Hypothesis, httpx, Vitest, Playwright | See §13 |
| CI | GitHub Actions | Lint, typecheck, tests, catalog validation |

---

## 7. Repository structure

```
HTTYD/
├── Plan.md
├── README.md
├── data/
│   ├── research/                 # raw per-film scene logs (notes, timestamps)
│   │   ├── httyd1_scene_log.md
│   │   ├── httyd2_scene_log.md
│   │   └── httyd3_scene_log.md
│   ├── catalog/                  # LAYERS 1–2: canon + franchise facts (hand-edited CSV)
│   │   ├── movies.csv
│   │   ├── species.csv
│   │   ├── individuals.csv
│   │   ├── characters.csv
│   │   ├── abilities.csv
│   │   ├── species_abilities.csv
│   │   ├── appearances.csv
│   │   ├── rider_links.csv
│   │   └── sources.csv
│   ├── game/                     # LAYER 3: invented balancing data
│   │   ├── species_profiles.yaml # traits, base stats, caps, rarity, matchable
│   │   ├── quiz_v1.yaml
│   │   ├── encounter_v1.yaml
│   │   ├── complements.yaml
│   │   ├── quirks.yaml
│   │   ├── progression.yaml      # XP curve, stages, unlocks
│   │   └── rivals.yaml           # arena NPC rider+dragon pairs
│   └── build/                    # GENERATED — never edit by hand
│       ├── dragons.json
│       ├── dragons.csv
│       └── seed.sql
├── scripts/
│   ├── validate_catalog.py
│   ├── build_catalog.py
│   └── calibrate_matching.py
├── apps/
│   ├── web/                      # Next.js + Tailwind + Phaser
│   │   └── src/
│   │       ├── app/              # routes (see §11)
│   │       ├── components/
│   │       ├── game/             # Phaser scenes + GameBridge
│   │       └── lib/api/          # generated OpenAPI types + fetch client
│   └── api/                      # FastAPI
│       ├── app/
│       │   ├── main.py
│       │   ├── config.py
│       │   ├── auth.py           # Supabase JWT verification
│       │   ├── routers/
│       │   ├── engines/          # matching, training, needs, mood, checks
│       │   ├── ai/               # providers, prompts, memory, chat, story
│       │   ├── db/               # SQLAlchemy models, session
│       │   └── schemas/          # Pydantic request/response models
│       └── tests/
├── supabase/
│   ├── config.toml
│   └── migrations/               # schema + RLS policies (single source of schema truth)
└── .github/workflows/ci.yml
```

The initial idea was a folder per dragon (`dragons/species/night_fury`, `dragons/individuals/toothless`). This plan uses **relational CSV tables** instead, because appearances, riders and abilities are many-to-many and change per film. For example, Skullcrusher has different riders in different films. The build script can still emit per-dragon JSON files if needed.

---

## 8. Data model

### 8.1 Catalog files (canon and franchise)

Every fact row carries `source_ids` and a `confidence` of `high`, `medium` or `low`. Full headers are in [Appendix A](#appendix-a-catalog-templates).

| File | One row per | Key columns |
|---|---|---|
| `movies.csv` | Film | `movie_id`, `title`, `year`, `ordinal` |
| `species.csv` | Species | `species_id`, `name`, `class`, `class_scope`, `size`, `diet`, `description` |
| `individuals.csv` | Named dragon | `individual_id`, `name`, `species_id`, `description` |
| `characters.csv` | Human character | `character_id`, `name` |
| `abilities.csv` | Ability | `ability_id`, `name`, `category` |
| `species_abilities.csv` | Species–ability link | `species_id`, `ability_id`, `scope` |
| `appearances.csv` | Entity × film × type | `entity_kind`, `entity_id`, `movie_id`, `appearance_type`, `scope`, `evidence` |
| `rider_links.csv` | Dragon–human link per film | `individual_id`, `character_id`, `movie_id`, `relation` |
| `sources.csv` | Source | `source_id`, `title`, `type`, `url`, `accessed_on` |

**IDs:** lowercase slugs (`night_fury`, `toothless`, `barf_and_belch`). Slugs are stable and human-readable, and serve directly as URL paths and primary keys. When an individual has the same name as its species, the individual's ID gets a `the_` prefix (`light_fury` species, `the_light_fury` individual).

**Descriptions:** always written in your own words (see §16).

### 8.2 Build outputs

`scripts/build_catalog.py` produces the three export formats:

- `dragons.json`: denormalised, one object per species and individual, used by the frontend and the LLM retrieval layer.
- `dragons.csv`: the flat master catalog, for spreadsheets and review.
- `seed.sql`: `INSERT` statements for all canon and game tables.

Example `dragons.json` entry:

```json
{
  "kind": "species",
  "id": "night_fury",
  "name": "Night Fury",
  "class": { "value": "Strike", "scope": "franchise" },
  "abilities": [
    { "id": "plasma_blast", "name": "Plasma blast", "scope": "film" },
    { "id": "stealth", "name": "Stealth / night camouflage", "scope": "film" }
  ],
  "appearances": [
    { "movie": "httyd1", "type": "featured" },
    { "movie": "httyd2", "type": "featured" },
    { "movie": "httyd3", "type": "featured" }
  ],
  "known_individuals": ["toothless"],
  "description": "…written in your own words…",
  "sources": ["film_httyd1", "film_httyd2", "film_httyd3"],
  "confidence": "high"
}
```

### 8.3 Database schema

Schema lives in `supabase/migrations/`. The sketch below is illustrative; types and constraints get finalised in Phase 0/1.

#### Canon and franchise tables (layers 1–2, public read-only)

```sql
create type source_scope    as enum ('film', 'franchise');
create type appearance_type as enum ('featured', 'on_screen', 'background', 'mentioned', 'pictured');
create type confidence      as enum ('high', 'medium', 'low');

create table movies (
  id       text primary key,          -- 'httyd1'
  title    text not null,
  year     int  not null,
  ordinal  int  not null unique
);

create table sources (
  id           text primary key,
  title        text not null,
  type         text not null check (type in ('film', 'official', 'book', 'wiki', 'other')),
  url          text,
  accessed_on  date
);

create table species (
  id           text primary key,      -- 'night_fury'
  name         text not null unique,
  class        text,
  class_scope  source_scope,
  size         text check (size in ('tiny', 'small', 'medium', 'large', 'titan')),
  diet         text,
  description  text,
  notes        text,
  source_ids   text[] not null default '{}',
  confidence   confidence not null default 'medium'
);

create table individuals (
  id           text primary key,      -- 'toothless'
  name         text not null,
  species_id   text not null references species(id),
  description  text,
  notes        text,
  source_ids   text[] not null default '{}',
  confidence   confidence not null default 'medium'
);

create table characters (
  id    text primary key,             -- 'hiccup'
  name  text not null
);

create table abilities (
  id           text primary key,      -- 'plasma_blast'
  name         text not null,
  category     text check (category in ('fire', 'physical', 'sensory', 'defensive', 'utility', 'special')),
  description  text
);

create table species_abilities (
  species_id  text references species(id),
  ability_id  text references abilities(id),
  scope       source_scope not null default 'film',
  primary key (species_id, ability_id)
);

create table appearances (
  id               bigserial primary key,
  entity_kind      text not null check (entity_kind in ('species', 'individual')),
  entity_id        text not null,
  movie_id         text not null references movies(id),
  appearance_type  appearance_type not null,
  scope            source_scope not null default 'film',
  evidence         text,                -- scene description / timestamp note
  confidence       confidence not null default 'medium',
  unique (entity_kind, entity_id, movie_id)
);

create table rider_links (
  individual_id  text references individuals(id),
  character_id   text references characters(id),
  movie_id       text references movies(id),
  relation       text not null check (relation in ('rider', 'owner', 'controller', 'companion')),
  primary key (individual_id, character_id, movie_id)
);
```

#### Game tables (layer 3, public read-only)

```sql
create table species_game_profile (
  species_id     text primary key references species(id),
  matchable      boolean not null default false,
  rarity         text not null check (rarity in ('common', 'uncommon', 'rare', 'legendary')),
  traits         jsonb not null,   -- {"courage":85,"curiosity":90,...} 7 traits, 0–100
  requirements   jsonb not null default '{}',   -- {"patience":{"min":60}}
  approach_pref  text check (approach_pref in ('calm', 'bold', 'gentle', 'playful')),
  base_stats     jsonb not null,   -- {"speed":80,"agility":70,...}
  stat_caps      jsonb not null,
  diet_likes     text[] not null default '{}',
  diet_dislikes  text[] not null default '{}',
  shot_limit     int,              -- arena/target-practice balancing
  color_variants text[] not null default '{}'
);

create table quiz_versions (id text primary key, active boolean not null default false);
create table quiz_questions (
  id          text primary key,
  quiz_id     text references quiz_versions(id),
  ordinal     int  not null,
  prompt      text not null
);
create table quiz_options (
  id            text primary key,
  question_id   text references quiz_questions(id),
  label         text not null,
  trait_deltas  jsonb not null   -- {"courage":10,"patience":-5}
);
```

#### Player tables (layer 4, row-level security on `user_id`)

```sql
create table profiles (
  id            uuid primary key references auth.users(id) on delete cascade,
  display_name  text,
  created_at    timestamptz not null default now()
);

create table quiz_attempts (
  id                 uuid primary key default gen_random_uuid(),
  user_id            uuid not null references profiles(id) on delete cascade,
  quiz_id            text not null references quiz_versions(id),
  answers            jsonb not null,
  trait_scores       jsonb,
  encounter_signals  jsonb,
  ranking            jsonb,   -- [{species_id, raw, display_pct, reasons[]}]
  algorithm_version  text not null,
  created_at         timestamptz not null default now(),
  completed_at       timestamptz
);

create table player_dragons (
  id                uuid primary key default gen_random_uuid(),
  user_id           uuid not null references profiles(id) on delete cascade,
  species_id        text not null references species(id),
  quiz_attempt_id   uuid references quiz_attempts(id),
  name              text not null,
  color_variant     text,
  personality       jsonb not null,   -- species traits + seeded variation
  quirks            text[] not null default '{}',
  likes             text[] not null default '{}',
  dislikes          text[] not null default '{}',
  level             int  not null default 1,
  xp                int  not null default 0,
  stage             text not null default 'newborn',
  stats             jsonb not null,   -- speed, agility, strength, firepower, stamina, intelligence, obedience
  needs             jsonb not null,   -- hunger, energy, happiness
  needs_updated_at  timestamptz not null default now(),
  trust             int  not null default 20 check (trust between 0 and 100),
  memory_summary    jsonb not null default '{}',   -- structured memory (§9.9)
  created_at        timestamptz not null default now()
);

create table dragon_events (
  id          bigserial primary key,
  dragon_id   uuid not null references player_dragons(id) on delete cascade,
  kind        text not null,   -- fed, rested, trained, refused, chatted, competed, story_choice, level_up, discovered
  payload     jsonb not null default '{}',
  created_at  timestamptz not null default now()
);

create table training_sessions (
  id            uuid primary key default gen_random_uuid(),
  dragon_id     uuid not null references player_dragons(id) on delete cascade,
  activity      text not null,
  started_at    timestamptz not null default now(),
  completed_at  timestamptz,
  score         int check (score between 0 and 100),
  xp_gained     int,
  stat_deltas   jsonb,
  client_meta   jsonb
);

create extension if not exists vector;

create table dragon_memories (
  id                uuid primary key default gen_random_uuid(),
  dragon_id         uuid not null references player_dragons(id) on delete cascade,
  kind              text not null check (kind in ('preference', 'fact', 'episode', 'relationship')),
  content           text not null,
  importance        int  not null check (importance between 1 and 10),
  embedding         vector(768),
  source_event_id   bigint references dragon_events(id),
  pinned            boolean not null default false,
  created_at        timestamptz not null default now(),
  last_recalled_at  timestamptz
);

create table chat_messages (
  id          bigserial primary key,
  dragon_id   uuid not null references player_dragons(id) on delete cascade,
  role        text not null check (role in ('user', 'dragon')),
  content     text not null,
  created_at  timestamptz not null default now()
);

create table competition_runs (
  id          uuid primary key default gen_random_uuid(),
  dragon_id   uuid not null references player_dragons(id) on delete cascade,
  event_type  text not null,
  rivals      jsonb not null,
  result      jsonb not null,
  created_at  timestamptz not null default now()
);

create table stories (
  id          uuid primary key default gen_random_uuid(),
  dragon_id   uuid not null references player_dragons(id) on delete cascade,
  title       text,
  status      text not null default 'active' check (status in ('active', 'completed', 'abandoned')),
  state       jsonb not null default '{}',   -- location, flags, running summary
  created_at  timestamptz not null default now()
);

create table story_nodes (
  id            bigserial primary key,
  story_id      uuid not null references stories(id) on delete cascade,
  ordinal       int  not null,
  scene_text    text not null,
  choices       jsonb not null,
  chosen_index  int,
  check_result  jsonb,
  unique (story_id, ordinal)
);

create table discoveries (
  user_id        uuid not null references profiles(id) on delete cascade,
  entity_kind    text not null check (entity_kind in ('species', 'individual')),
  entity_id      text not null,
  via            text not null,   -- quiz, arena, story, training, starter
  discovered_at  timestamptz not null default now(),
  primary key (user_id, entity_kind, entity_id)
);
```

**RLS:** enable row-level security on every player table with `user_id = auth.uid()` (or ownership via `player_dragons`) for `select`. FastAPI is the only writer. RLS is defence in depth in case the frontend ever reads Supabase directly.

**Embedding dimension:** fixed at 768. `nomic-embed-text` (Ollama) is 768-dimensional, and Gemini embedding models can be configured to output 768 dimensions (verify for the chosen model). Embeddings from different models are not comparable, so switching the embedding model means re-embedding all memories.

---

## 9. Feature specifications

### 9.1 Dragon Book (encyclopedia)

**List view:** a grid of cards with name, silhouette or art, class badge (marked *franchise* where applicable) and film chips.

**Search and filters:**
- Search runs client-side (Fuse.js over `dragons.json`), which is fine for a dataset of this size.
- Filters: film, class, species vs individual, appearance type, source scope (film only / include franchise), size.

**Detail view:**
- Name, species (for individuals), class with a scope badge, abilities, diet, size.
- Films with appearance type per film (e.g., *HTTYD 1 — pictured · HTTYD 2 — on screen*).
- Known individuals (for species) and riders per film (for individuals).
- Description, sources and a confidence indicator.
- An **Academy ratings** panel showing game-layer stats, clearly labelled as not film facts.

**Discovery mechanic:**
- Logged-out visitors see the full reference.
- Logged-in players see **Academy mode**: undiscovered entries appear as silhouettes with "???", plus a progress counter (e.g., *23 / 41 discovered*) and "new" badges. A **Show all** toggle is always available.
- Entries are discovered through quiz runner-ups, the starter set, arena rivals, story encounters and training locations.

### 9.2 Personality quiz

**Traits** (both players and species are scored on the same 7 traits, 0–100):

| Trait | Player meaning | Dragon meaning |
|---|---|---|
| Courage | Faces danger, takes risks | Bold, confronts threats |
| Curiosity | Explores, asks questions | Investigates, wanders |
| Loyalty | Sticks with others | Bonds deeply, protective |
| Aggression | Direct, confrontational | Quick to fight or defend |
| Patience | Calm, persistent | Tolerant, slow to anger |
| Independence | Self-reliant | Resists commands, lone |
| Intelligence | Analytical, strategic | Problem-solving, learns fast |

**Format:**
- 12 scenario questions (range 10–15), each with 4 options.
- Option order is randomised per player.
- Each option carries trait deltas from −10 to +15.

**Authoring rules:**
- Every trait is touched by at least 4 questions.
- No option is obviously "the good answer".
- The quiz is versioned (`quiz_v1`). Attempts store the version, so old results stay reproducible.

**Scoring:** sum the deltas per trait, then min–max normalise against the lowest and highest totals achievable for that trait in that quiz version:

```
score_t = 100 × (raw_t − min_possible_t) / (max_possible_t − min_possible_t)
```

**Example question (`quiz_v1.yaml`):**

```yaml
- id: q01_injured_dragon
  prompt: "You discover an injured dragon tangled in a net. What do you do?"
  options:
    - id: a
      label: "Help it immediately"
      deltas: { courage: 10, loyalty: 8, patience: -4 }
    - id: b
      label: "Watch it quietly first"
      deltas: { patience: 10, intelligence: 6, courage: -3 }
    - id: c
      label: "Try to communicate with it"
      deltas: { curiosity: 12, intelligence: 4 }
    - id: d
      label: "Keep your distance and fetch help"
      deltas: { independence: -6, loyalty: 4, courage: -6 }
```

### 9.3 Matching algorithm

The matching engine is a pure Python module (`engines/matching.py`), versioned as `algorithm_version`.

**Inputs:**
- Player trait vector **U**.
- For each species with `matchable = true`: trait vector **D**, trait weights **w**, `requirements`, `approach_pref`, diet likes and dislikes.
- Encounter signals (§9.4).

**Steps (per species):**

1. **Similarity**, from 0 to 1:
   ```
   S = 1 − sqrt( Σ w_t (U_t − D_t)² / Σ w_t ) / 100
   ```
2. **Complement**, from 0 to 1. Some pairings work because they differ. Rules live in `complements.yaml`:
   ```yaml
   - when: { dragon: aggression, gte: 70 }    # fiery dragon…
     reward: { trainer: patience }            # …needs a patient trainer
   - when: { dragon: independence, gte: 75 }
     reward: { trainer: curiosity }
   - when: { dragon: patience, lte: 35 }
     reward: { trainer: patience }
   ```
   `C` is the mean of `trainer_trait / 100` over the rules that fire, or 0.5 when none fire.
3. **Requirement penalty**, from 0 to 0.3:
   ```
   P = min(0.3, Σ max(0, min_t − U_t) / 100 × 0.5)
   ```
4. **Encounter bonus**, from 0 to 1, taken from §9.4 (0.5 is neutral).
5. **Raw score:**
   ```
   raw = 0.70·S + 0.15·C + 0.15·B − P
   ```

**Displayed compatibility.** The raw score is not shown directly, because raw values cluster tightly. Instead, the displayed figure maps the raw score to its percentile among best-match scores from the calibration simulation:

```
compatibility% = 60 + 39 × percentile(raw)      → range 60–99%
```

**Result:**
- The top species, plus 2 runner-ups shown as "also drawn to you". Runner-ups are marked discovered.

**Explanation:**
- The top 3 contributors become sentences, e.g., *"Your high curiosity and loyalty closely match this dragon's; your patience balances its fiery temper."*
- Contributors are high-weight traits with a small |U−D|, plus complement rules that fired.

**Matchable pool (default):**
- Trainable species appearing in the films are matchable.
- Titans and alphas (Red Death, Bewilderbeast) are **not matchable**. They appear in the Dragon Book and stories only.
- Night Fury and Light Fury are matchable at **legendary** rarity (see §18).

**Calibration (`scripts/calibrate_matching.py`):**
- Simulate 100,000 random answer sets (plus random encounter choices).
- Record the distribution of top matches.
- Targets:
  - Every matchable species is the top match in at least 3% of runs.
  - No species exceeds 20%.
  - Each legendary species stays at or below 3%.
- Tune trait vectors and weights until the targets pass. The script outputs a report (table + histogram) and the percentile table used for display.
- Hand-written **archetype fixtures** (e.g., "the cautious scholar", "the reckless daredevil") act as regression tests with expected top-3 results.

**ML extensions (after real data, roughly 200+ attempts):**
- **K-Means** on player trait vectors to discover real player archetypes and inform quiz redesign.
- **Logistic regression** on "Does this match feel right? 👍/👎" feedback to learn better weights for S, C and B.
- These run offline in notebooks or scripts. The live engine stays a transparent formula with learned constants.

### 9.4 "The Dragon Chooses You" encounter and reveal

After the quiz, three short scenes (about 60 seconds total, text plus illustration):

| Scene | Prompt | Options → effect |
|---|---|---|
| **1. First contact** | A young dragon emerges from the fog | *Reach out* (bold) · *Stay still, eyes down* (calm) · *Kneel and speak softly* (gentle) · *Toss a pebble to play* (playful) → matched against the species' `approach_pref` |
| **2. The offering** | You have a satchel of food | *Fish* · *A smooth rock* · *Chicken* · *Bread* → matched against `diet_likes` / `diet_dislikes` |
| **3. The startle** | Thunder cracks overhead | *Calm it* · *Shield it* · *Run for cover* · *Laugh it off* → small trait adjustments (weight 0.2) merged into U |

Encounter bonus:

```
B = 0.5 + 0.25 · approach_match + 0.25 · diet_match     (each match ∈ {−1, 0, +1})
```

Reaction times are recorded for analytics only and **not scored**, so slow readers and assistive-technology users are not penalised.

**Reveal sequence:**
1. Three silhouettes (top 3) circle overhead.
2. Two peel away.
3. The chosen dragon lands, with a compatibility bar animation and the text *"It chose you."*
4. The player names the dragon.

A reduced-motion variant uses fades instead. The reveal plays in a Motion or Phaser scene.

### 9.5 The player's dragon

Created at adoption (`POST /dragons`):

| Attribute | How it's set |
|---|---|
| Species | Top match |
| Name | Chosen by player (2–20 characters, profanity-filtered) |
| Personality | Species trait vector + seeded variation (normal distribution, σ = 6), clamped 0–100, so no two dragons are identical |
| Stats | 30–40% of species `stat_caps`, scaled by `base_stats` |
| Color variant | Random from species `color_variants` |
| Quirks | 1–2 from `quirks.yaml` (e.g., *hoards shiny things*, *afraid of thunder*, *sneezes sparks when excited*) |
| Likes / dislikes | Seeded from species diet plus quirks; grow later through memory |
| Needs | hunger 30, energy 80, happiness 60 |
| Trust | 20 |
| Level / stage | 1 / Newborn |

**Game stats:** Speed · Agility · Strength · Firepower · Stamina · Intelligence · Obedience.
**Relationship meter:** Trust (0–100).

Example dragon card (shown on Dragon Home and the reveal):

```
╔════════════════════════════════════╗
║   EMBER — Deadly Nadder            ║
║   Compatibility: 94%               ║
║                                    ║
║   Speed        ████████░░  82      ║
║   Agility      █████████░  91      ║
║   Firepower    ███████░░░  74      ║
║   Intelligence ██████░░░░  63      ║
║   Obedience    ████░░░░░░  41      ║
║                                    ║
║   Trust ▓▓░░░░░░░░   Mood: Curious ║
╚════════════════════════════════════╝
```

### 9.6 Training and progression

**Activity contract.** Every training activity, from a simple Phase 5 version to a Phaser game in Phase 7, returns the same payload:

```ts
type ActivityResult = {
  sessionId: string;
  activity: "flight" | "accuracy" | "speed" | "memory" | "obedience";
  score: number;        // 0–100
  durationMs: number;
  meta?: Record<string, unknown>;
};
```

The server issues a `sessionId` at start. It accepts exactly one completion per session and checks that `durationMs` falls within the activity's plausible range.

| Activity | Trains | Phase 5 (simple DOM) | Phase 7 (Phaser) |
|---|---|---|---|
| Flight | Agility, Speed | Timing bar | Obstacle course |
| Accuracy | Firepower | Click moving targets | Aim-and-shoot with shot limit |
| Speed | Speed, Stamina | Rhythm tapping | Race vs ghost |
| Memory | Intelligence | Sequence recall 🐟 🪨 🔥 🥚 🌿 | Animated sequence recall |
| Obedience | Obedience, Trust | Command-response reaction | Command course (Fly, Land, Turn, Follow, Stop) |

**Formulas** (tunable in `progression.yaml`):

```
mood_mult        = { excited: 1.2, happy: 1.1, curious: 1.0, hungry: 0.85, tired: 0.8, scared: 0.8, angry: 0.75 }
xp_gained        = round((20 + 0.6 × score) × mood_mult)
xp_to_next(L)    = round(100 × L^1.5)
Δstat            = 4 × (score / 100) × (1 − stat / cap) × mood_mult      # diminishing returns near cap
energy_cost      = 10–20 per session (by activity)
hunger_gain      = +8 per session
happiness        = +5 if score ≥ 70 or activity ∈ likes; −5 if score < 30
trust            = +2 per completed session, +1 extra if dragon's needs were met
```

**Refusals:** when energy is below 15 or hunger is above 85, the dragon refuses to train. The UI explains why ("Ember is exhausted"). Training anyway is impossible, which teaches care.

**Stages and unlocks:**

| Stage | Levels | Unlocks |
|---|---|---|
| Newborn | 1–4 | Flight, Speed activities; feeding, resting |
| Young | 5–9 | Accuracy, Memory activities; chat moods expand |
| Trained | 10–19 | Obedience activity; **Arena**; first adventure |
| Elite | 20–29 | Advanced arena events; new story regions; species signature ability shown in games |
| Master | 30 | Master title, special adventure, full Trainer's Notes in Dragon Book |

Stages are about maturity and training rank. The **species never changes**, since changing it would contradict canon.

**Needs decay** (lazy, applied on every read or write):

```
elapsed_h  = now − needs_updated_at
hunger     = clamp(hunger + 4 × elapsed_h)
energy     = clamp(energy + 8 × elapsed_h)      # recovers while idle
happiness  = clamp(happiness − 2 × elapsed_h)
```

**Actions:**
- **Feed:** hunger decreases; happiness increases more for liked foods; disliked foods cost happiness and trust.
- **Rest:** energy recovers faster.
- **Play:** happiness increases; small energy cost.

### 9.7 Personality and mood

Mood is **deterministic** (no LLM). It is derived from needs, trust, traits and recent events. The first matching rule wins:

| Priority | Mood | Condition |
|---|---|---|
| 1 | Scared | Startle/storm event in last 30 min (story or encounter) |
| 2 | Hungry | hunger > 70 |
| 3 | Tired | energy < 25 |
| 4 | Angry | trust < 25 and a refusal or overtraining in the last hour |
| 5 | Excited | happiness > 75 and energy > 60 |
| 6 | Curious | curiosity trait > 65 (default for curious dragons) |
| 7 | Happy | Default |

Tired is an addition to the original six moods.

Mood drives:
- The dragon's expression and sprite.
- The training `mood_mult`.
- Idle thought lines on Dragon Home (template-based, no LLM cost).
- The AI prompt.

### 9.8 AI companion

**Voice design.** Dragons in the films don't speak human language. The default mode is therefore **Narrated**: a body-language line plus a short thought bubble.

> *Ember nudges the empty fish basket with her snout, then stares at you.*
> 💭 "Two hours of flying. Fish. Now."

An optional **Talking mode** toggle lets the dragon speak directly (labelled as non-canon fun).

**Prompt assembly** (server-side, `ai/prompts.py`):

```
[SYSTEM]  Role and rules: stay in character; Narrated format; max ~80 words; PG;
          never claim to be a canon individual; only use species facts from CANON FACTS;
          if unsure, react with behaviour instead of stating facts.
[CANON FACTS]    Species entry from DB (abilities, diet, class+scope) — retrieved, not invented
[DRAGON CARD]    Name, species, stage, personality traits, quirks, likes/dislikes
[STATE]          Mood, needs, trust, last 3 events
[MEMORIES]       Top-k (k = 6) retrieved memories (§9.9)
[CONVERSATION]   Last 10 turns
[USER]           Player's message
```

**Flow per chat turn:**
1. Build the prompt, then **stream** the reply to the client over SSE.
2. Save the messages and log a `chatted` event.
3. In the background, a cheaper model call extracts memory candidates as structured JSON (§9.9).

**Provider abstraction:**

```python
class LLMProvider(Protocol):
    async def stream_chat(self, messages: list[Message], *, max_tokens: int,
                          temperature: float) -> AsyncIterator[str]: ...
    async def generate_json(self, messages: list[Message],
                            schema: type[BaseModel]) -> BaseModel: ...
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
```

Implementations are `GeminiProvider`, `OllamaProvider` and `FakeProvider` (for tests), selected with `LLM_PROVIDER`.

**Guardrails:**
- Input capped at 500 characters.
- Per-user daily limits (see §15).
- Provider safety settings plus a blocklist.
- Output checks for length, format and forbidden claims.
- On any failure, a canned fallback keeps the game working: *"Ember tilts her head, confused."*

### 9.9 Dragon memory

**Tier 1, structured memory (Phase 6a, deterministic).**
- Aggregated from `dragon_events` into `player_dragons.memory_summary`.
- Captures favourite food (most fed with positive reactions), favourite activity (highest average happiness gain), dislikes (refusals, low-mood activities), hours trained, streaks and trust history.

```yaml
memory:
  likes: [fish]
  dislikes: [thunderstorms]
  favorite_activity: [flying]
  trainer_relationship:
    trust: 87
```

**Tier 2, episodic and semantic memory (Phase 6b, pgvector).**
- After each chat session or story chapter, an extraction call proposes memory candidates:
  `{content, kind, importance 1–10}`.
- Deduplication: if cosine similarity to an existing memory is above 0.9, update that memory instead of inserting a new one.
- **Retrieval score:**
  ```
  score = 0.5 × cosine_relevance + 0.3 × importance / 10 + 0.2 × recency
  recency = exp(−days_since_created_or_recalled / 7)
  ```
- Top 6 go into the prompt, and `last_recalled_at` is updated.

**Player controls:** a **Dragon's Journal** page lists memories in the dragon's voice. Players can **pin** or **delete** any memory, and can wipe all memory.

**Trust is always changed by the server's deterministic rules, never by the LLM.** The LLM may suggest a mood shift; the server clamps it and may ignore it.

### 9.10 Mini-games (Phaser)

**Integration:**
- Phaser mounts in a client-only React component.
- A `GameBridge` passes the dragon's stats in and posts the `ActivityResult` out.
- Controls support keyboard and touch.
- Games use a seeded RNG, so replays can be deterministic.

**Stats → gameplay mapping** (each species plays differently):

| Stat | Effect in games |
|---|---|
| Speed | Scroll/flight speed, race top speed |
| Agility | Turn rate, dodge window |
| Firepower | Projectile size, damage to targets |
| Stamina | Boost meter length, endurance duration |
| Intelligence | Memory-game hints, sequence display time |
| Obedience + Trust | Command compliance chance: at low trust the dragon sometimes ignores you |

**Games:**

| Game | Mechanic | Score |
|---|---|---|
| **Flight Course** | Side-scroller through sea stacks, collect rings | rings% × survival% |
| **Target Practice** | Aim and fire at moving targets with a species shot limit (a nod to the arena scene in the first film) | hits / shots, time bonus |
| **Race** | Race ghost rivals along a course, with stamina boost | Finish position + time |
| **Memory** | Recall growing sequences of 🐟 🪨 🔥 🥚 🌿 | Longest correct sequence |
| **Obedience** | Commands appear (Fly, Land, Turn, Follow, Stop); respond in time; dragon may not comply | Correct responses × compliance |

**Art:** start with original geometric placeholders, then original, commissioned or generated sprites. Never use film assets.

### 9.11 Arena (competitions)

- Unlocks at the **Trained** stage.
- **Events:** Flying race, Obstacle course, Target accuracy, Treasure hunt, Rescue mission, Endurance flight. All are non-violent.
- **Rivals:** canon **rider + dragon pairs** as NPCs defined in `rivals.yaml` (e.g., Astrid & Stormfly, Snotlout & Hookfang, Fishlegs & Meatlug, Ruffnut & Tuffnut with Barf & Belch, Hiccup & Toothless as the final challenge). Toothless cannot fly without Hiccup in the films, so rivals always fly as pairs. Their ratings are game-layer values.
- **Result model:**
  ```
  player_perf = 0.6 × live_minigame_score + 0.4 × stat_rating(event) + noise(σ = 5)
  rival_perf  = rival_rating(event) + noise(σ = 5)
  ```
- **Rewards:** XP, trust, titles, badges, and Dragon Book discoveries (rival species and individuals).

Example race display:

```
HOOKFANG        🐉 ───────────→
STORMFLY        🐉 ─────────────→
EMBER (you)     🐉 ─────────────────→  🏁
```

### 9.12 AI adventure mode

**Structure:**
- An adventure has 3 chapters.
- Each chapter has 3–6 nodes.
- A node is `{scene_text ≤ 150 words, choices: 2–3, each with an optional stat_check}`.

**Engine** (server-side state machine):
1. Assemble context: dragon card, mood, top memories, discovered locations, stage, and a running summary of previous nodes.
2. The LLM generates the next node as JSON against a Pydantic schema.
3. The player picks a choice.
4. The server resolves any stat check **deterministically**:
   ```
   p_success = sigmoid((stat − difficulty) / 10) + trust_bonus    (trust_bonus up to +0.1)
   ```
   The roll uses a seeded RNG, and the result is stored in `check_result`.
5. The outcome feeds the next generation. Chapter end triggers memory extraction and rewards.

**World guardrails:**
- Stories take place around the Academy Isle and original locations.
- Wild dragons encountered are drawn **from the species table**, never invented, and encountering one marks it discovered.
- Canon characters appear as cameos only.
- No retelling or altering of film events.
- PG tone.

**Outputs:**
- XP, trust changes, episodic memories, discoveries and location unlocks.
- Completed adventures are saved as an illustrated **Chronicle** to reread.

Example opening:

> **The Storm Beyond Berk**
> A strange storm has gathered over the northern sea. Ember paces the cliff edge, eyes fixed on the lightning, more excited than afraid…
> **[Fly into the storm]** (Stamina check) · **[Search the nearby island]** · **[Return to the village]**

---

## 10. API design

Base path: `/api/v1`. Auth is a Supabase JWT in `Authorization: Bearer`. Public endpoints need no token.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | — | Liveness |
| GET | `/movies` | — | List films |
| GET | `/species` · `/species/{id}` | — | Canon species (+ game profile) |
| GET | `/individuals` · `/individuals/{id}` | — | Canon individuals |
| GET | `/search?q=` | — | Server-side search (fallback to client search) |
| GET | `/encyclopedia` | ✓ | Entries with the player's discovery state |
| GET | `/quiz` | ✓ | Active quiz version (options shuffled) |
| POST | `/quiz/attempts` | ✓ | Submit answers, returns trait scores |
| POST | `/quiz/attempts/{id}/encounter` | ✓ | Submit encounter choices, returns ranking + explanation |
| POST | `/dragons` | ✓ | Adopt the top match and set its name |
| GET | `/dragons/me` | ✓ | Dragon card: stats, needs (decayed), mood, trust |
| PATCH | `/dragons/{id}` | ✓ | Rename |
| POST | `/dragons/{id}/feed` · `/rest` · `/play` | ✓ | Care actions |
| POST | `/dragons/{id}/training-sessions` | ✓ | Start session, returns `sessionId` |
| POST | `/training-sessions/{id}/complete` | ✓ | Submit `ActivityResult`, returns XP, stat deltas, level-ups |
| GET | `/dragons/{id}/history` | ✓ | Training history for charts |
| POST | `/dragons/{id}/chat` | ✓ | Chat turn (SSE stream) |
| GET | `/dragons/{id}/messages` | ✓ | Chat history |
| GET · PATCH · DELETE | `/dragons/{id}/memories[/{mid}]` | ✓ | Journal: list, pin, delete |
| GET | `/arena/events` | ✓ | Available events + rivals |
| POST | `/arena/runs` | ✓ | Submit run, returns placement + rewards |
| POST | `/stories` | ✓ | Start adventure |
| GET | `/stories/{id}` | ✓ | Story state + nodes |
| POST | `/stories/{id}/choices` | ✓ | Choose, returns check result + next node |
| DELETE | `/me` | ✓ | Delete account and all player data |

TypeScript types for the frontend are generated from `/openapi.json` with `openapi-typescript`.

---

## 11. Frontend routes

| Route | Page | Auth |
|---|---|---|
| `/` | Landing: pitch, "Find your dragon" CTA, featured Dragon Book entries | — |
| `/dragon-book` | Encyclopedia list, search, filters | — |
| `/dragon-book/[id]` | Encyclopedia entry | — |
| `/login` | Supabase Auth UI | — |
| `/academy/quiz` | Personality quiz | ✓ |
| `/academy/encounter` | Three encounter scenes | ✓ |
| `/academy/reveal` | Reveal animation + naming | ✓ |
| `/dragon` | Dragon Home: card, needs, mood, care actions, idle thoughts | ✓ |
| `/train` | Activity picker + training history | ✓ |
| `/train/[activity]` | Activity / mini-game | ✓ |
| `/chat` | Talk to your dragon | ✓ |
| `/journal` | Dragon's memories | ✓ |
| `/arena` · `/arena/[event]` | Competitions | ✓ |
| `/adventures` · `/adventures/[id]` | Adventure list, active story, Chronicle | ✓ |
| `/profile` | Settings, voice mode, data export/delete | ✓ |

---

## 12. Roadmap (phases 0–8)

Estimates assume one developer working part-time. They are rough, and Phase 1 depends heavily on research time.

```
Phase 0  Foundations            ▓░░░░░░░░░░░░░░░░░░░   ~1 wk
Phase 1  Dragon database        ░▓▓▓░░░░░░░░░░░░░░░░   2–3 wks
Phase 2  Dragon Book            ░░░░▓▓░░░░░░░░░░░░░░   1–2 wks   ── M1 "Dragon Book online"
Phase 3  Quiz + matching        ░░░░░░▓▓░░░░░░░░░░░░   2 wks
Phase 4  Profile + your dragon  ░░░░░░░░▓▓░░░░░░░░░░   1–2 wks   ── M2 MVP "It chose you"
Phase 5  Training system        ░░░░░░░░░░▓▓░░░░░░░░   2 wks
Phase 6  AI companion + memory  ░░░░░░░░░░░░▓▓▓░░░░░   2–3 wks   ── M3 "A dragon that remembers"
Phase 7  Mini-games + Arena     ░░░░░░░░░░░░░░░▓▓▓▓░   3–4 wks
Phase 8  AI adventures          ░░░░░░░░░░░░░░░░░░▓▓   2–3 wks   ── M4 "Full Academy"
                                                     total ≈ 16–22 weeks
```

### Phase 0: Foundations (~1 week)

**Build**
- [ ] Monorepo layout (§7), pnpm workspace, uv project, pre-commit (Ruff, ESLint, Prettier).
- [ ] Next.js + Tailwind app with a placeholder layout and theme.
- [ ] FastAPI app with `/health`, settings via env, CORS, structured logging.
- [ ] Supabase project and local stack (`supabase start`); first empty migration; pgvector enabled.
- [ ] Supabase JWT verification in FastAPI (`auth.py`) plus a protected test route.
- [ ] OpenAPI → TypeScript type generation script.
- [ ] GitHub Actions: lint, typecheck, pytest, Vitest.
- [ ] `.env.example` for web and api.

**Done when:** both apps run locally with one command each, CI is green, and a signed-in user can call a protected API route.

### Phase 1: Dragon database (2–3 weeks)

**Research protocol**
1. Watch each film and log every dragon in `data/research/httydN_scene_log.md` with a timestamp, what is seen or said, and the proposed appearance type.
2. Do a second pass per film for background dragons and pictured-only species (the Book of Dragons scene in the first film, carvings, maps).
3. Cross-check names and species against official DreamWorks material. Flag franchise-only facts (`scope = franchise`).
4. Transfer the log into catalog CSVs with `source_ids` and `confidence`.

**Build**
- [ ] Catalog CSVs for all three films (templates in Appendix A).
- [ ] `validate_catalog.py`, which checks:
  - Pydantic row schemas.
  - Enum values.
  - Unique slugs.
  - Foreign keys (every `species_id`, `movie_id`, `character_id` exists).
  - Every fact row has at least one source.
  - Every individual has at least one appearance.
  - A `franchise` scope requires a non-film source.
- [ ] `build_catalog.py` → `dragons.json`, `dragons.csv`, `seed.sql`.
- [ ] Migrations for canon and game tables; seed loads into a fresh database.
- [ ] Read-only endpoints: `/movies`, `/species`, `/individuals`, `/search`.

**Done when:**
- All three films are logged, and the validator passes in CI.
- `supabase db reset` produces a fully seeded database.
- The master list covers every named individual **and** every species by appearance type.

### Phase 2: Dragon Book (1–2 weeks)

**Build**
- [ ] List page with search (Fuse.js) and filters (film, class, kind, appearance type, scope).
- [ ] Detail pages, statically generated from `dragons.json`.
- [ ] Scope badges (*film* / *franchise*), confidence indicator, sources list.
- [ ] Placeholder silhouettes (original art).
- [ ] Mobile-first responsive layout; dark theme.

**Done when:** every entity has a page; filters combine correctly; pages load fast on mobile; franchise facts are visibly flagged.

**Milestone M1: Dragon Book online.**

### Phase 3: Quiz + matching (2 weeks)

**Build**
- [x] Trait definitions and `quiz_v1.yaml` (12 questions), validated against the authoring rules.
- [x] `species_profiles.yaml` for all matchable species (traits, weights, requirements, approach preference, diet, base stats, caps, rarity).
- [x] `engines/matching.py` (pure) + `complements.yaml`.
- [x] `calibrate_matching.py` with a Monte Carlo report and percentile table.
- [x] Archetype fixtures as tests.
- [ ] Quiz UI (progress bar, one question per screen) and encounter scenes (simple illustrated version).
- [ ] Result screen: top match, compatibility %, trait bars, explanation, 2 runner-ups.

**Done when:**
- The calibration meets the distribution targets in §9.3.
- The fixtures pass.
- A new player finishes quiz and encounter in under 3 minutes.

### Phase 4: Profile + your dragon (1–2 weeks)

**Build**
- [ ] Sign-up/login flow and profile creation.
- [ ] Reveal animation (Motion) with reduced-motion variant.
- [ ] Naming and adoption (`POST /dragons`), with seeded personality variation, quirks and colour.
- [ ] Dragon Home: dragon card, needs meters, mood, trust, idle thought lines.
- [ ] Care actions (feed/rest/play); lazy needs decay; deterministic mood engine.
- [ ] Discovery tracking and Academy mode in the Dragon Book.

**Done when:** a new player can go sign-up → quiz → encounter → reveal → name, and find the same dragon, with decayed needs, on their next visit.

**Milestone M2: MVP, "It chose you."** Playable, shareable and demo-ready.

### Phase 5: Training system (2 weeks)

**Build**
- [ ] Training session API (start/complete, plausibility checks, one completion per session).
- [ ] Five simple DOM activities implementing the `ActivityResult` contract.
- [ ] XP, levels, stages, unlocks (`progression.yaml`); level-up celebration.
- [ ] Energy/hunger costs; refusals with explanations.
- [ ] Training history chart (stats over time).

**Done when:**
- Formulas are covered by unit and property tests (e.g., a higher score never yields less XP, and stats never exceed caps).
- Unlocks trigger at the right levels.
- An exhausted dragon refuses to train.

### Phase 6: AI companion + memory (2–3 weeks)

**Build**
- [ ] `LLMProvider` with Gemini, Ollama and Fake implementations.
- [ ] Prompt builder with canon-fact retrieval from the database.
- [ ] Chat endpoint with SSE streaming; chat UI with Narrated/Talking toggle.
- [ ] **6a:** structured memory aggregation from events.
- [ ] **6b:** memory extraction, deduplication, pgvector retrieval.
- [ ] Dragon's Journal page (list/pin/delete).
- [ ] Guardrails, rate limits, fallbacks, token logging.
- [ ] AI eval suite (§13).

**Done when:**
- The eval suite passes its thresholds: format compliance ≥ 95%; canon-fact accuracy ≥ 95%; correct recall of a seeded memory in ≥ 80% of memory cases.
- Deleting a memory removes it from future prompts.

**Milestone M3: "A dragon that remembers."**

### Phase 7: Mini-games + Arena (3–4 weeks)

**Build**
- [ ] Phaser integration (client-only component, `GameBridge`, asset loading).
- [ ] The five Phaser games replace the DOM activities through the same contract.
- [ ] Stats → gameplay mapping; species feel different in play.
- [ ] Arena: events, `rivals.yaml`, result model, rewards, discoveries.
- [ ] Keyboard and touch controls; pause; sound toggle (original or royalty-free audio only).

**Done when:**
- All five games are playable on desktop and mobile at a smooth frame rate on a mid-range laptop.
- Results flow through the training pipeline unchanged.
- The Arena unlocks at the Trained stage.

### Phase 8: AI adventure mode (2–3 weeks)

**Build**
- [ ] Story state machine, node schema, deterministic stat checks.
- [ ] Context assembly with memories, discoveries and a running summary.
- [ ] World guardrails; wild encounters drawn from the species table.
- [ ] Adventure UI; Chronicle view.
- [ ] Rewards, memory extraction per chapter, location unlocks.
- [ ] Daily story caps and caching.

**Done when:**
- A full 3-chapter adventure is playable end to end.
- Choices and checks visibly change outcomes.
- Memories and discoveries persist.
- Story evals show no invented species and no contradictions of canon facts.

**Milestone M4: Full Academy.**

### Later ideas (post-M4)

- A stable of multiple dragons per player.
- Seasonal events.
- Shared leaderboards.
- Friends' dragons visiting.
- Original-dragon mode (§16).
- Voice input.
- An illustrated art pass.

---

## 13. Testing and quality

| Area | Tooling | What's tested |
|---|---|---|
| Catalog data | `validate_catalog.py` in CI | Schemas, enums, foreign keys, sources present, scope rules |
| Build outputs | Snapshot tests | `dragons.json` / `seed.sql` change only when catalog changes |
| Engines | pytest + **Hypothesis** | Matching (fixtures, bounds, determinism); training (monotonicity, caps); needs decay; mood priority; stat checks |
| Calibration | `calibrate_matching.py` in CI (small sample) | Distribution targets still met after profile edits |
| API | pytest + httpx against local Supabase | Auth, ownership, validation, one-completion-per-session |
| Frontend | Vitest + Testing Library | Components, stat bars, filters |
| End-to-end | **Playwright** | Golden path: sign-up → quiz → encounter → reveal → train → chat (with `FakeProvider`) |
| AI evals | Scripted suite (~30 cases), run with Ollama locally and before releases | Format compliance, canon accuracy (e.g., asking a Gronckle about abilities it doesn't have), memory recall, safety refusals, "never claims to be Toothless" |
| Games | Manual playtest checklist + seeded replays | Feel, difficulty, controls, performance |

---

## 14. Environments and deployment

| Piece | Local development | Production |
|---|---|---|
| Web | `pnpm dev` | Vercel |
| API | `uv run uvicorn app.main:app --reload` | Docker on Render / Fly.io / Railway |
| DB + Auth | `supabase start` (local Docker) | Supabase hosted (pgvector enabled) |
| LLM | Ollama (chat model + `nomic-embed-text`) | Gemini API |

**Environment variables**

```
# apps/api/.env
DATABASE_URL=
SUPABASE_URL=
SUPABASE_JWKS_URL=
LLM_PROVIDER=ollama            # ollama | gemini | fake
GEMINI_API_KEY=
GEMINI_CHAT_MODEL=
GEMINI_EMBED_MODEL=
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=
OLLAMA_EMBED_MODEL=nomic-embed-text
EMBED_DIM=768
CORS_ORIGINS=http://localhost:3000
DAILY_CHAT_LIMIT=50
DAILY_STORY_NODE_LIMIT=30

# apps/web/.env.local
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 15. Security, privacy, cost, accessibility

**Security**
- FastAPI verifies Supabase JWTs (JWKS, audience, expiry).
- Every player endpoint checks ownership.
- Only the API writes to the database; RLS is enabled on all player tables.
- Secrets stay server-side; the web app only has the anon key.
- CORS is locked to known origins.
- Rate limits apply per user and per IP.

**Privacy**
- Minimal personal data: email via Supabase Auth plus a display name.
- No email or other personal data is ever sent to the LLM.
- Players can delete memories, chat history, or their whole account (`DELETE /me` cascades).

**Cost control**
- Daily chat and story limits.
- Token budgets per request.
- Canon facts are cached.
- A smaller, cheaper model handles memory extraction.
- Idle thoughts are template-based, not LLM-generated.
- Ollama for all development.
- Token usage is logged per user.

**Accessibility**
- Every game is keyboard-playable.
- Reduced-motion variants for the reveal and animations.
- Colour-contrast-checked stat bars that also show numbers.
- Alt text on art.
- Encounter reaction times are not scored.

**Content**
- PG tone throughout, since the audience includes younger fans.
- Safety settings are on for all generation.

---

## 16. Legal and IP

- *How to Train Your Dragon* names, characters and designs belong to DreamWorks Animation / Universal. Treat this as a **non-commercial fan project** with a visible disclaimer: *"Fan project. Not affiliated with or endorsed by DreamWorks Animation or Universal Pictures."*
- **No film assets:** no stills, official renders, logos, music, sound effects or footage. Use original, commissioned or generated art only, and don't prompt image models to replicate official character designs.
- **Write descriptions in your own words.** Fan wiki text is typically licensed CC BY-SA. Copying it brings attribution and share-alike obligations, so cite sources as references rather than copying text.
- **Keep the engine IP-agnostic** (§3, rule 4). Because all dragon content lives in data files, the same engine could later run an **original-dragons** dataset. That is the path if you ever want a commercial or broadly published version.

---

## 17. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Scope creep | Never ships | Strict phase order; MVP at Phase 4; "Later ideas" list parks new features |
| Canon inaccuracies | Credibility | Sources + confidence on every row; validator; scene logs; franchise flags |
| Everyone gets a Night Fury | Result feels fake | Monte Carlo calibration with distribution targets; legendary rarity |
| LLM invents lore | Breaks canon | Canon facts retrieved from DB; strict prompt rules; canon-accuracy evals; wild dragons drawn from DB |
| LLM cost / latency | Budget, bad UX | Daily limits, streaming, small extraction model, caching, Ollama in dev |
| Game feel takes longer than planned | Phase 7 slips | DOM activities (Phase 5) already make training playable; games replace them one at a time |
| Art bottleneck | Looks unfinished | Stylised silhouettes/geometric art first; art pass later |
| IP complaint | Takedown | Non-commercial, disclaimer, no film assets, IP-agnostic engine |
| Memory feels creepy | Trust | Journal transparency; pin/delete; no personal data in memories |
| Phaser + Next.js SSR issues | Integration bugs | Client-only dynamic import; isolate games behind `GameBridge` |

---

## 18. Open decisions

Each decision has a recommended default so work isn't blocked. Confirm or change these before the relevant phase.

| # | Decision | Recommended default | Needed by |
|---|---|---|---|
| 1 | Can players match with Night Fury / Light Fury? | Yes, as **legendary** (≤ 3% each), framed as your own individual. Titans (Red Death, Bewilderbeast) are never matchable | Phase 3 |
| 2 | Dragon voice | **Narrated** by default; Talking mode as an opt-in toggle | Phase 6 |
| 3 | Dragons per player | **One** for MVP; a stable later | Phase 4 |
| 4 | Retaking the quiz | Allowed. It shows "who else might choose you" and marks runner-ups discovered, but does **not** replace your dragon | Phase 4 |
| 5 | Franchise-only species in the Dragon Book | **No.** Only species from the films; franchise info only as flagged attributes | Phase 1 |
| 6 | Dragon Book without login | **Yes**, full reference; Academy mode (discovery) for logged-in players | Phase 2 |
| 7 | In-world setting | Original **Academy Isle**, era while dragons and Vikings coexist; canon characters as cameos | Phase 3 (encounter text) |
| 8 | Production LLM | **Gemini**; Ollama for dev and evals | Phase 6 |

---

## 19. Immediate next steps

1. **Confirm the open decisions** in §18, or accept the defaults.
2. **Phase 0 scaffolding:** repo layout, both apps, Supabase local, CI.
3. **Start the HTTYD 1 scene log** using the templates in Appendix A. This is the critical path, since every later phase reads this data.
4. In parallel, **draft trait definitions and 12 quiz questions**. This is pure writing and needs no code.

---

## Appendix A: Catalog templates

```csv
# movies.csv
movie_id,title,year,ordinal
httyd1,How to Train Your Dragon,2010,1
httyd2,How to Train Your Dragon 2,2014,2
httyd3,How to Train Your Dragon: The Hidden World,2019,3
```

```csv
# species.csv
species_id,name,class,class_scope,size,diet,description,notes,source_ids,confidence
night_fury,Night Fury,Strike,franchise,medium,fish,"<own words>","",film_httyd1|film_httyd2|film_httyd3,high
```

```csv
# individuals.csv
individual_id,name,species_id,description,notes,source_ids,confidence
toothless,Toothless,night_fury,"<own words>","",film_httyd1|film_httyd2|film_httyd3,high
```

```csv
# characters.csv
character_id,name
hiccup,Hiccup Horrendous Haddock III
```

```csv
# abilities.csv
ability_id,name,category,description
plasma_blast,Plasma blast,fire,"<own words>"
```

```csv
# species_abilities.csv
species_id,ability_id,scope
night_fury,plasma_blast,film
```

```csv
# appearances.csv
entity_kind,entity_id,movie_id,appearance_type,scope,evidence,confidence
individual,toothless,httyd1,featured,film,"Main dragon throughout",high
```

```csv
# rider_links.csv
individual_id,character_id,movie_id,relation
toothless,hiccup,httyd1,rider
```

```csv
# sources.csv
source_id,title,type,url,accessed_on
film_httyd1,How to Train Your Dragon (2010),film,,
```

Multi-value fields (`source_ids`) use `|` as the separator.

---

## Appendix B: Starter entity list

These are the core dragons to seed the catalog. **Every row must be verified during Phase 1** against the films. This list is a starting point, not the finished catalog; background, mentioned and pictured species are added during the scene-log passes. Classes are franchise-scoped.

### Named individuals

| ID | Name | Species | Films | Rider / companion (by film) | Notes |
|---|---|---|---|---|---|
| `toothless` | Toothless | Night Fury | 1, 2, 3 | Hiccup (1–3) | Main dragon; becomes Alpha in 2 |
| `stormfly` | Stormfly | Deadly Nadder | 1, 2, 3 | Astrid (1–3) | |
| `meatlug` | Meatlug | Gronckle | 1, 2, 3 | Fishlegs (1–3) | |
| `hookfang` | Hookfang | Monstrous Nightmare | 1, 2, 3 | Snotlout (1–3) | |
| `barf_and_belch` | Barf & Belch | Hideous Zippleback | 1, 2, 3 | Ruffnut & Tuffnut (1–3) | One individual, two heads |
| `the_red_death` | The Red Death | Red Death | 1 | — | Titan-sized nest queen; not matchable. Name matches the species, so the individual ID gets a `the_` prefix |
| `cloudjumper` | Cloudjumper | Stormcutter | 2, 3 | Valka | |
| `skullcrusher` | Skullcrusher | Rumblehorn | 2, 3 | Stoick (2), Eret (3) | Rider changes by film |
| `grump` | Grump | Hotburple | 2 (3: verify) | Gobber | |
| `valkas_bewilderbeast` | Valka's Bewilderbeast | Bewilderbeast | 2 | — | Sanctuary alpha; not matchable |
| `dragos_bewilderbeast` | Drago's Bewilderbeast | Bewilderbeast | 2 | Drago (controller) | Not matchable |
| `the_light_fury` | The Light Fury | Light Fury | 3 | — (Toothless's mate) | Same naming rule: `light_fury` is the species, `the_light_fury` the individual |
| `night_lights` | The Night Lights (×3) | Night Fury × Light Fury hybrids | 3 | — | End of film; names are from outside the films, so flag them |

### Species (seed; expand from scene logs)

Night Fury · Light Fury · Deadly Nadder · Gronckle · Monstrous Nightmare · Hideous Zippleback · Terrible Terror · Red Death · Stormcutter · Rumblehorn · Hotburple · Bewilderbeast · Deathgripper · *(plus every species found on screen, in the background, mentioned or pictured during Phase 1)*

The "Individual?" column from the original catalog idea becomes the `species` / `individual` split. The "Trainer" column becomes `rider_links` per film, which captures cases like Skullcrusher changing riders between films.

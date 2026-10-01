# Dragon Academy

An interactive AI, game and ML project built on a sourced dataset of every dragon in the three *How to Train Your Dragon* animated films. See [Plan.md](Plan.md) for the full plan and [TECH_STACK.md](TECH_STACK.md) for what it's built with. Notable changes are listed in [CHANGELOG.md](CHANGELOG.md).

**Status:** Phase 2 (Dragon Book). The Dragon Book is live at `/dragon-book`. The dragon catalog is pre-filled; film verification is in progress. See [data/README.md](data/README.md).

## Layout

```
apps/web     Next.js 16 (App Router) + Tailwind 4 + TanStack Query; the Dragon Book
apps/api     FastAPI (Python 3.14, managed with uv); canon endpoints over the database
supabase/    Local Supabase config and SQL migrations (the schema source of truth)
data/        Research notes, catalog CSVs, game YAML, build outputs (see data/README.md)
scripts/     Catalog validation and build scripts (Phase 1+)
```

## Prerequisites

Node 22+, pnpm 10, uv, the Supabase CLI, and Docker Desktop (running) for the local Supabase stack.

## First-time setup

```sh
pnpm install                       # web dependencies
uv sync --directory apps/api       # API dependencies
uvx pre-commit install             # git hooks

pnpm db:start                      # starts local Supabase in Docker; prints URLs and keys
```

Then create the env files from the examples and fill in the values `supabase status` prints:

- `apps/web/.env.local` from `apps/web/.env.example`. Set `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` to the **Publishable** key.
- `apps/api/.env` from `apps/api/.env.example`. The defaults work locally. Set `SUPABASE_JWT_SECRET` only if your Supabase signs tokens with the legacy HS256 secret.

## Run

In two terminals:

```sh
pnpm dev:api    # http://localhost:8000/api/v1/docs
pnpm dev:web    # http://localhost:3000
```

Open http://localhost:3000. The **System check** panel shows whether the API is reachable, whether you're signed in, and whether the protected `/api/v1/me` route accepts your token. Create an account at `/login` to turn all three green.

Supabase Studio runs at http://localhost:54323.

## What's there

**Dragon Book** at http://localhost:3000/dragon-book: every species and named dragon from the three films, with search, filters (film, kind, appearance type, class) and a page per dragon showing its films, riders and sources. It's built from `data/build/dragons.json` and `references.json`, so it only needs `pnpm dev:web`: no API or database.

**API** (try them at http://localhost:8000/api/v1/docs). The dragon endpoints are public and read-only:

| Endpoint | Returns |
|---|---|
| `GET /api/v1/movies` | The three films |
| `GET /api/v1/species` · `/species/{id}` | Species (filter with `?movie=httyd2`), or one with its films, named dragons and sources |
| `GET /api/v1/individuals` · `/individuals/{id}` | Named dragons (same filter), or one with its species, films, riders per film and sources |
| `GET /api/v1/search?q=` | Species and named dragons by name |
| `GET /api/v1/me` | The signed-in user (needs a token) |

The dragon data is a first pass from the fan wiki and general knowledge, not yet checked against the films. Every entry shows a confidence level and its sources; see [data/README.md](data/README.md).

## Common tasks

| Task | Command |
|---|---|
| All checks (what CI runs) | `pnpm check` |
| Regenerate frontend API types after changing the API | `pnpm gen:api-types` |
| New database migration | `supabase migration new <name>` |
| Re-apply all migrations and the dragon seed to local DB | `pnpm db:reset` |
| Scene logs → catalog appearances and riders | `pnpm catalog:import` |
| Check the dragon catalog | `pnpm catalog:check` |
| Rebuild the seed and dragon exports from the catalog | `pnpm catalog:build` |

The frontend's API types are generated from FastAPI's OpenAPI schema. Commit `apps/api/openapi.json` and `apps/web/src/lib/api/schema.d.ts` together; CI fails if they drift.

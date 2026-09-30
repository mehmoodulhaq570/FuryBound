# Dragon Academy

An interactive AI, game and ML project built on a sourced dataset of every dragon in the three *How to Train Your Dragon* animated films. See [Plan.md](Plan.md) for the full plan and [TECH_STACK.md](TECH_STACK.md) for what it's built with.

**Status:** Phase 2 (Dragon Book). The Dragon Book is live at `/dragon-book`. The dragon catalog is pre-filled; film verification is in progress. See [data/README.md](data/README.md).

## Layout

```
apps/web     Next.js 16 (App Router) + Tailwind 4 + TanStack Query
apps/api     FastAPI (Python 3.14, managed with uv)
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

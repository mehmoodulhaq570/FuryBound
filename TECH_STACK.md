# Tech stack

What Dragon Academy is built with as of **Phase 1 (dragon database)**. Versions come from `apps/web/package.json`, `apps/api/pyproject.toml` and the local Supabase stack. See [Plan.md §6](Plan.md#6-tech-stack) for the full planned stack.

## Frontend (`apps/web`)

| Technology | Version | Role |
|---|---|---|
| Next.js (App Router) | 16.3.7 | Web app framework |
| React | 19.2.8 | UI library |
| TypeScript | 5 | Typed JavaScript |
| Tailwind CSS | 4 | Styling |
| TanStack Query | 5 | Server state: fetching and caching API data |
| Zustand | 5 | Small client-side state (installed, not used yet) |
| openapi-fetch | 0.17 | Typed API client |
| openapi-typescript | 7.13 | Generates API types from the backend's OpenAPI schema |
| @supabase/supabase-js, @supabase/ssr | 2.117, 0.12 | Sign-in from the browser |

## Backend (`apps/api`)

| Technology | Version | Role |
|---|---|---|
| Python | 3.14 | Backend language |
| FastAPI | 0.142 | HTTP API, served under `/api/v1` |
| Pydantic Settings | 2.15 | Configuration from environment variables |
| PyJWT (with crypto) | 2.15 | Verifies Supabase access tokens (JWKS, or HS256 locally) |
| structlog | 26.1 | Structured request logging |
| SQLAlchemy (async) | 2.1 | Database queries |
| asyncpg | 0.31 | PostgreSQL driver used by SQLAlchemy |

## Data pipeline (`scripts/`, `data/`)

| Technology | Role |
|---|---|
| Python + Pydantic | `import_scene_logs.py`, `validate_catalog.py` and `build_catalog.py` turn scene logs and catalog CSVs into `seed.sql`, `dragons.json` and `dragons.csv` (see [data/README.md](data/README.md)) |

## Database and auth (`supabase/`)

| Technology | Version | Role |
|---|---|---|
| Supabase CLI | 2.116 | Runs the local stack in Docker; manages migrations |
| PostgreSQL | 17.6 | Database |
| pgvector | 0.8.2 | Vector search for dragon memories (Phase 6) |
| Supabase Auth (GoTrue) | 2.196 | Sign-up and sign-in |
| PostgREST, Kong, Studio, Mailpit | — | REST API, API gateway, admin UI, local test inbox |

`pnpm db:start` runs a lean set of services. Realtime, Storage, image proxy, Edge Functions, analytics and the connection pooler aren't used yet, so they're left out to save memory. `pnpm db:start:full` starts everything.

## Tooling

| Technology | Version | Role |
|---|---|---|
| Node.js | 22+ | JavaScript runtime |
| pnpm | 10.19 | JavaScript package manager and workspace |
| uv | 0.11 | Python package and environment manager |
| Docker Desktop (WSL 2) | Engine 29.7 | Runs the local Supabase stack |
| pre-commit | — | Git hooks: whitespace, YAML/TOML checks, Ruff |

## Code quality and testing

| Technology | Version | Role |
|---|---|---|
| ESLint | 9 | Frontend linting |
| Prettier (+ Tailwind plugin) | 3.9 | Frontend formatting |
| Ruff | 0.16 | Python linting and formatting |
| mypy | 2.3 | Python type checking |
| Vitest | 5 | Frontend unit tests |
| Testing Library + jsdom | 16, 30 | React component tests |
| pytest | 9.1 | Backend tests |
| httpx2 | 2.13 | HTTP client for backend tests |

## CI

| Technology | Role |
|---|---|
| GitHub Actions | Three jobs. **API**: lint, type checks, and tests against a seeded Supabase database; checks the OpenAPI schema is up to date. **Data**: checks the catalog and that scene logs, catalog and build outputs agree. **Web**: lint, type checks, tests; checks the generated API types are up to date |

## Coming in later phases

| Technology | Phase | Role |
|---|---|---|
| Fuse.js | 2 | Client-side Dragon Book search |
| Hypothesis | 3 | Property tests for the game engines |
| scikit-learn, NumPy, pandas | 3 | Matching calibration and analysis |
| Motion | 4 | Reveal animation and transitions |
| Gemini API, Ollama | 6 | AI companion (production and local) |
| Phaser | 7 | Mini-games |
| Playwright | 7+ | End-to-end tests |

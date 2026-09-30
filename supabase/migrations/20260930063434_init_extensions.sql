-- Phase 0: extensions only. Canon, game and player tables arrive in Phase 1+ (Plan.md §8.3).

-- pgvector, for dragon memories (vector(768)) in Phase 6.
create extension if not exists vector with schema extensions;

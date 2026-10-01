-- Layer 4 (player data): quiz attempts. See Plan.md §8.3 and §9.2-9.4.
--
-- Deviations from the Plan's sketch, for now:
-- - user_id references auth.users directly; the profiles table arrives with sign-up in Phase 4.
-- - quiz_id has no foreign key: quizzes live in data/game/quiz_vN.yaml (validated on load),
--   not in quiz_versions / quiz_questions / quiz_options tables.

create table quiz_attempts (
  id                 uuid primary key default gen_random_uuid(),
  user_id            uuid not null references auth.users(id) on delete cascade,
  quiz_id            text not null,
  answers            jsonb not null,   -- {"q01_injured_dragon": "a", ...}
  trait_scores       jsonb,            -- min-max 0-100 per trait, for display
  encounter_signals  jsonb,            -- {"first_contact": "stay_still", ...}
  ranking            jsonb,            -- [{species_id, raw, compatibility, explanation}]
  algorithm_version  text not null,
  created_at         timestamptz not null default now(),
  completed_at       timestamptz       -- set once the encounter is done
);

create index quiz_attempts_user_created on quiz_attempts (user_id, created_at desc);

-- The API writes with the service connection; players may only read their own attempts.
alter table quiz_attempts enable row level security;
create policy "Own attempts" on quiz_attempts
  for select to authenticated using ((select auth.uid()) = user_id);

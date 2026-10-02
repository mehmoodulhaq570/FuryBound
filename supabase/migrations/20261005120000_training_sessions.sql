-- Layer 4 (player data): training sessions (Plan.md §8.3, §9.6).
--
-- The API issues a session when training starts and accepts exactly one completion for it.
-- Extra columns beyond the Plan's sketch:
-- - mood and needs_at_start: the state when it started (they set the XP multiplier and the
--   trust bonus), so a session is scored by how the dragon felt when it began.
-- - stats_after: the dragon's stats once it finished, for the training history chart.

create table training_sessions (
  id              uuid primary key default gen_random_uuid(),
  dragon_id       uuid not null references player_dragons(id) on delete cascade,
  activity        text not null,
  mood            text not null,
  needs_at_start  jsonb not null,
  started_at      timestamptz not null default now(),
  completed_at    timestamptz,
  score           int check (score between 0 and 100),
  duration_ms     int,
  xp_gained       int,
  stat_deltas     jsonb,
  stats_after     jsonb,
  client_meta     jsonb
);

create index training_sessions_dragon_completed on training_sessions (dragon_id, completed_at);

-- The API writes with the service connection; players may only read their own dragon's.
alter table training_sessions enable row level security;
create policy "Own dragon's training" on training_sessions
  for select to authenticated using (
    exists (
      select 1 from player_dragons d
      where d.id = dragon_id and d.user_id = (select auth.uid())
    )
  );

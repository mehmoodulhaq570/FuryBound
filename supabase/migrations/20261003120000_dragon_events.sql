-- Layer 4 (player data): what happened to each dragon, oldest first. See Plan.md §8.3.
-- Care actions write here now (adopted, fed, rested, played); training, chat and stories
-- will later. Mood reads the last hour of it (Plan §9.7).

create table dragon_events (
  id          bigserial primary key,
  dragon_id   uuid not null references player_dragons(id) on delete cascade,
  kind        text not null,   -- adopted, fed, rested, played, (later) trained, refused, ...
  payload     jsonb not null default '{}',
  created_at  timestamptz not null default now()
);

create index dragon_events_dragon_created on dragon_events (dragon_id, created_at desc);

-- The API writes with the service connection; players may only read their own dragon's events.
alter table dragon_events enable row level security;
create policy "Own dragon's events" on dragon_events
  for select to authenticated using (
    exists (
      select 1 from player_dragons d
      where d.id = dragon_id and d.user_id = (select auth.uid())
    )
  );

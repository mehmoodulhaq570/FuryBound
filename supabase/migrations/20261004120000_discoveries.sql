-- Layer 4 (player data): which dragons each player has met (Plan.md §8.3, §9.1).
--
-- For now only species are recorded; a named dragon counts as discovered with its species
-- (Toothless with the Night Fury). entity_kind is kept so individuals can be added later.

create table discoveries (
  user_id        uuid not null references profiles(id) on delete cascade,
  entity_kind    text not null check (entity_kind in ('species', 'individual')),
  entity_id      text not null,
  via            text not null,   -- quiz, arena, story, training, starter
  discovered_at  timestamptz not null default now(),
  primary key (user_id, entity_kind, entity_id)
);

-- The API writes with the service connection; players may only read their own.
alter table discoveries enable row level security;
create policy "Own discoveries" on discoveries
  for select to authenticated using ((select auth.uid()) = user_id);

-- Players who finished the encounter before this existed: their top 3 count as met.
insert into discoveries (user_id, entity_kind, entity_id, via, discovered_at)
select a.user_id, 'species', r.value ->> 'species_id', 'quiz', coalesce(a.completed_at, now())
from quiz_attempts a
cross join lateral jsonb_array_elements(a.ranking) as r(value)
where a.ranking is not null
on conflict do nothing;

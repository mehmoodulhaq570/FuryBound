-- Layer 4 (player data): chat with your dragon (Plan.md §8.3, §9.8).
--
-- Extra columns beyond the Plan's sketch:
-- - mode: narrated (body language + thought) or talking (non-canon fun), per message.
-- - meta: for the dragon's replies, which model answered, how long it took, and whether the
--   fallback line had to be used.

create table chat_messages (
  id          bigserial primary key,
  dragon_id   uuid not null references player_dragons(id) on delete cascade,
  role        text not null check (role in ('user', 'dragon')),
  content     text not null,
  mode        text not null default 'narrated' check (mode in ('narrated', 'talking')),
  meta        jsonb not null default '{}',
  created_at  timestamptz not null default now()
);

create index chat_messages_dragon_created on chat_messages (dragon_id, created_at);

-- The API writes with the service connection; players may only read their own dragon's chat.
alter table chat_messages enable row level security;
create policy "Own dragon's chat" on chat_messages
  for select to authenticated using (
    exists (
      select 1 from player_dragons d
      where d.id = dragon_id and d.user_id = (select auth.uid())
    )
  );

-- Layer 4 (player data): profiles and adopted dragons. See Plan.md §8.3 and §9.5.
--
-- Deviations from the Plan's sketch, for now:
-- - One dragon per player (unique user_id), as /dragons/me implies.
-- - dragon_events, training and discoveries come with the features that use them.

-- ── profiles ─────────────────────────────────────────────────────────────────

create table profiles (
  id            uuid primary key references auth.users(id) on delete cascade,
  display_name  text,
  created_at    timestamptz not null default now()
);

alter table profiles enable row level security;
create policy "Own profile" on profiles
  for select to authenticated using ((select auth.uid()) = id);

-- Every new account gets a profile. Security definer: it runs as the table owner, because
-- the auth service that inserts the user can't write to public tables.
create function public.create_profile_for_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (id) values (new.id);
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.create_profile_for_new_user();

-- Accounts made before this migration.
insert into profiles (id) select id from auth.users on conflict do nothing;

-- Quiz attempts now belong to profiles, as in the Plan.
alter table quiz_attempts drop constraint quiz_attempts_user_id_fkey;
alter table quiz_attempts
  add constraint quiz_attempts_user_id_fkey
  foreign key (user_id) references profiles(id) on delete cascade;

-- ── player_dragons ───────────────────────────────────────────────────────────

create table player_dragons (
  id                uuid primary key default gen_random_uuid(),
  user_id           uuid not null unique references profiles(id) on delete cascade,
  species_id        text not null references species(id),
  quiz_attempt_id   uuid unique references quiz_attempts(id) on delete set null,
  name              text not null check (char_length(name) between 1 and 40),
  color_variant     text,
  personality       jsonb not null,   -- species traits + seeded variation, 0-100 each
  quirks            text[] not null default '{}',   -- quirk ids from data/game/adoption.yaml
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
  compatibility     int  check (compatibility between 0 and 100),   -- shown on the dragon card
  rules_version     text not null,   -- data/game/adoption.yaml version it was rolled with
  created_at        timestamptz not null default now()
);

-- The API writes with the service connection; players may only read their own dragon.
alter table player_dragons enable row level security;
create policy "Own dragon" on player_dragons
  for select to authenticated using ((select auth.uid()) = user_id);

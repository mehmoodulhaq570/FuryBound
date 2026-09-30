-- Phase 1: canon and franchise tables (Plan.md §8.3, layers 1–2).
-- Rows come from data/build/seed.sql, generated from data/catalog/*.csv by scripts/build_catalog.py.
-- Public read-only: anyone may select; only the service role (the API, later) writes.

create type source_scope    as enum ('film', 'franchise');
create type appearance_type as enum ('featured', 'on_screen', 'background', 'mentioned', 'pictured');
create type confidence      as enum ('high', 'medium', 'low');

create table movies (
  id       text primary key,          -- 'httyd1'
  title    text not null,
  year     int  not null,
  ordinal  int  not null unique
);

create table sources (
  id           text primary key,
  title        text not null,
  type         text not null check (type in ('film', 'official', 'book', 'wiki', 'other')),
  url          text,
  accessed_on  date
);

create table species (
  id           text primary key,      -- 'night_fury'
  name         text not null unique,
  class        text,
  class_scope  source_scope,
  size         text check (size in ('tiny', 'small', 'medium', 'large', 'titan')),
  diet         text,
  description  text,
  notes        text,
  source_ids   text[] not null default '{}',
  confidence   confidence not null default 'medium',
  check ((class is null) = (class_scope is null))
);

create table individuals (
  id           text primary key,      -- 'toothless'
  name         text not null,
  species_id   text not null references species(id),
  description  text,
  notes        text,
  source_ids   text[] not null default '{}',
  confidence   confidence not null default 'medium'
);

create table characters (
  id    text primary key,             -- 'hiccup'
  name  text not null
);

create table abilities (
  id           text primary key,      -- 'plasma_blast'
  name         text not null,
  category     text check (category in ('fire', 'physical', 'sensory', 'defensive', 'utility', 'special')),
  description  text
);

create table species_abilities (
  species_id  text references species(id),
  ability_id  text references abilities(id),
  scope       source_scope not null default 'film',
  primary key (species_id, ability_id)
);

-- entity_id points at species.id or individuals.id depending on entity_kind;
-- scripts/validate_catalog.py checks it, since a foreign key can't.
create table appearances (
  id               bigserial primary key,
  entity_kind      text not null check (entity_kind in ('species', 'individual')),
  entity_id        text not null,
  movie_id         text not null references movies(id),
  appearance_type  appearance_type not null,
  scope            source_scope not null default 'film',
  evidence         text,
  source_ids       text[] not null default '{}',
  confidence       confidence not null default 'medium',
  unique (entity_kind, entity_id, movie_id)
);

create table rider_links (
  individual_id  text references individuals(id),
  character_id   text references characters(id),
  movie_id       text references movies(id),
  relation       text not null check (relation in ('rider', 'owner', 'controller', 'companion')),
  source_ids     text[] not null default '{}',
  confidence     confidence not null default 'medium',
  primary key (individual_id, character_id, movie_id)
);

create index individuals_species_id_idx on individuals (species_id);
create index appearances_entity_idx on appearances (entity_kind, entity_id);
create index rider_links_character_id_idx on rider_links (character_id);

-- Row-level security: public read, no public writes.
do $$
declare
  t text;
begin
  foreach t in array array[
    'movies', 'sources', 'species', 'individuals', 'characters',
    'abilities', 'species_abilities', 'appearances', 'rider_links'
  ] loop
    execute format('alter table %I enable row level security', t);
    execute format('create policy "Public read" on %I for select to anon, authenticated using (true)', t);
  end loop;
end $$;

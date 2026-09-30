"""Check the catalog CSVs (Plan.md Phase 1).

Checks: row schemas and enum values, unique ids, foreign keys, every fact row has a known
source, every individual appears in at least one film, franchise-scoped facts cite a
non-film source, and each entity appears at most once per film.

Run from the repo root:  pnpm catalog:check
"""

import sys
from collections import Counter
from typing import cast

from catalog import (
    FILES,
    Ability,
    Appearance,
    Character,
    Individual,
    Movie,
    RiderLink,
    Row,
    Scope,
    Source,
    Species,
    SpeciesAbility,
    columns,
    parse,
    read_rows,
)
from pydantic import ValidationError


def load(errors: list[str]) -> dict[str, list[Row]]:
    tables: dict[str, list[Row]] = {}
    for file_name, model in FILES.items():
        raw = read_rows(file_name)
        header = list(raw[0]) if raw else columns(model)
        if raw and header != columns(model):
            errors.append(f"{file_name}: columns should be {columns(model)}, got {header}")
            tables[file_name] = []
            continue
        rows: list[Row] = []
        for line, r in enumerate(raw, start=2):
            try:
                rows.append(parse(model, r))
            except ValidationError as e:
                for err in e.errors():
                    field = ".".join(str(p) for p in err["loc"]).replace("class_", "class")
                    errors.append(f"{file_name}:{line}: {field}: {err['msg']}")
        tables[file_name] = rows
    return tables


def check(tables: dict[str, list[Row]], errors: list[str]) -> None:
    movies = cast(list[Movie], tables["movies.csv"])
    sources = cast(list[Source], tables["sources.csv"])
    species = cast(list[Species], tables["species.csv"])
    individuals = cast(list[Individual], tables["individuals.csv"])
    characters = cast(list[Character], tables["characters.csv"])
    species_abilities = cast(list[SpeciesAbility], tables["species_abilities.csv"])
    appearances = cast(list[Appearance], tables["appearances.csv"])
    riders = cast(list[RiderLink], tables["rider_links.csv"])

    def unique(file_name: str, keys: list[str]) -> set[str]:
        for key, n in Counter(keys).items():
            if n > 1:
                errors.append(f"{file_name}: id {key!r} is used {n} times")
        return set(keys)

    movie_ids = unique("movies.csv", [m.movie_id for m in movies])
    source_ids = unique("sources.csv", [s.source_id for s in sources])
    species_ids = unique("species.csv", [s.species_id for s in species])
    individual_ids = unique("individuals.csv", [i.individual_id for i in individuals])
    character_ids = unique("characters.csv", [c.character_id for c in characters])
    abilities = cast(list[Ability], tables["abilities.csv"])
    ability_ids = unique("abilities.csv", [a.ability_id for a in abilities])
    unique("species.csv (names)", [s.name for s in species])
    # Species and individuals share one URL space (/dragon-book/<id>); Plan.md §8.1 `the_` rule.
    for clash in sorted(species_ids & individual_ids):
        errors.append(f"individuals.csv: {clash!r} is also a species id; use the_{clash}")
    source_type = {s.source_id: s.type for s in sources}

    def ref(where: str, kind: str, value: str, known: set[str]) -> None:
        if value not in known:
            errors.append(f"{where}: unknown {kind} {value!r}")

    def cited(where: str, ids: list[str]) -> None:
        if not ids:
            errors.append(f"{where}: needs at least one source")
        for i in ids:
            ref(where, "source", i, source_ids)

    for s in species:
        where = f"species.csv: {s.species_id}"
        cited(where, s.source_ids)
        if s.class_ and s.class_scope is None:
            errors.append(f"{where}: class is set but class_scope is empty")
        if s.class_scope is Scope.FRANCHISE and all(
            source_type.get(i) == "film" for i in s.source_ids
        ):
            errors.append(f"{where}: franchise class needs a non-film source")

    for i in individuals:
        where = f"individuals.csv: {i.individual_id}"
        cited(where, i.source_ids)
        ref(where, "species", i.species_id, species_ids)

    for sa in species_abilities:
        where = f"species_abilities.csv: {sa.species_id}/{sa.ability_id}"
        ref(where, "species", sa.species_id, species_ids)
        ref(where, "ability", sa.ability_id, ability_ids)

    entity_ids = {"species": species_ids, "individual": individual_ids}
    for key, n in Counter((a.entity_kind, a.entity_id, a.movie_id) for a in appearances).items():
        if n > 1:
            errors.append(f"appearances.csv: {key[1]} appears {n} times in {key[2]}")
    for a in appearances:
        where = f"appearances.csv: {a.entity_id} in {a.movie_id}"
        ref(where, a.entity_kind, a.entity_id, entity_ids[a.entity_kind])
        ref(where, "movie", a.movie_id, movie_ids)
        cited(where, a.source_ids)
        if a.scope is Scope.FRANCHISE and all(source_type.get(i) == "film" for i in a.source_ids):
            errors.append(f"{where}: franchise scope needs a non-film source")

    appearing = {a.entity_id for a in appearances if a.entity_kind == "individual"}
    for i in individuals:
        if i.individual_id not in appearing:
            errors.append(f"individuals.csv: {i.individual_id} has no film appearance")

    for r in riders:
        where = f"rider_links.csv: {r.individual_id}/{r.character_id} in {r.movie_id}"
        ref(where, "individual", r.individual_id, individual_ids)
        ref(where, "character", r.character_id, character_ids)
        ref(where, "movie", r.movie_id, movie_ids)
        cited(where, r.source_ids)


def main() -> int:
    errors: list[str] = []
    tables = load(errors)
    if not errors:
        check(tables, errors)
    if errors:
        print(f"Catalog has {len(errors)} problem(s):", *errors, sep="\n  ")
        return 1
    counts = ", ".join(f"{len(rows)} {name.removesuffix('.csv')}" for name, rows in tables.items())
    print(f"Catalog OK: {counts}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

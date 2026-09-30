"""Regenerate appearances.csv and rider_links.csv from the per-film scene logs.

The scene logs (data/research/httydN_scene_log.md) are where film viewing gets recorded.
Every checklist row marked `yes` or `yes?` becomes an appearance; every row in the riders
table becomes a rider link. Species, individuals and characters are looked up by name in
the catalog, so they must exist there first.

Run from the repo root:  pnpm catalog:import
"""

import re
import sys

from catalog import MOVIE_IDS, RESEARCH, read_rows, write_rows

INCLUDED = {"yes", "yes?"}
EXCLUDED = {"no", "no?", ""}
SOURCE_IDS = {"film": "film_{movie}", "wiki": "wiki_{movie}", "knowledge": "claude_knowledge"}


def section_tables(text: str, heading: str) -> list[list[dict[str, str]]]:
    """Return the Markdown tables under a `## heading` (up to the next `## `)."""
    match = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not match:
        return []
    tables: list[list[dict[str, str]]] = []
    header: list[str] | None = None
    for line in match.group(1).splitlines():
        if not line.startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = cells
            tables.append([])
        elif not set("".join(cells)) <= set("-: "):
            tables[-1].append(dict(zip(header, cells, strict=True)))
    return tables


def plain_name(name: str) -> str:
    # Drops a trailing note in brackets, as in the Night Lights' checklist row.
    return re.sub(r"\s*\(.*\)$", "", name)


def source_ids(source: str, movie: str) -> str:
    parts = [p.strip() for p in source.split("+")]
    return "|".join(SOURCE_IDS[p].format(movie=movie) for p in parts)


def main() -> int:
    species = {r["name"]: r["species_id"] for r in read_rows("species.csv")}
    individuals = {r["name"]: r["individual_id"] for r in read_rows("individuals.csv")}
    # Logs use first names ("Stoick"); the catalog has full names ("Stoick the Vast").
    characters = {
        r["name"].split()[0].rstrip(","): r["character_id"] for r in read_rows("characters.csv")
    }
    ids = {"species": species, "individual": individuals}

    appearances: list[dict[str, str]] = []
    riders: list[dict[str, str]] = []
    errors: list[str] = []

    for movie in MOVIE_IDS:
        log = RESEARCH / f"{movie}_scene_log.md"
        text = log.read_text(encoding="utf-8")

        for table in section_tables(text, "Checklist"):
            for row in table:
                where = f"{log.name}: {row['Dragon']}"
                seen = row["Seen?"].lower()
                if seen in EXCLUDED:
                    continue
                if seen not in INCLUDED:
                    errors.append(f"{where}: Seen? must be yes, yes?, no or no? (got {seen!r})")
                    continue
                entity_id = ids[row["Kind"]].get(plain_name(row["Dragon"]))
                if entity_id is None:
                    errors.append(f"{where}: no {row['Kind']} with this name in the catalog")
                    continue
                try:
                    sources = source_ids(row["Source"], movie)
                except KeyError:
                    errors.append(f"{where}: unknown Source {row['Source']!r}")
                    continue
                appearances.append(
                    {
                        "entity_kind": row["Kind"],
                        "entity_id": entity_id,
                        "movie_id": movie,
                        "appearance_type": row["Appearance"],
                        "scope": "film",
                        "evidence": row["Notes"],
                        "source_ids": sources,
                        "confidence": row["Confidence"],
                    }
                )

        for table in section_tables(text, "Riders and companions"):
            for row in table:
                if not row["Dragon"]:
                    continue
                where = f"{log.name}: riders: {row['Dragon']}"
                individual_id = individuals.get(plain_name(row["Dragon"]))
                if individual_id is None:
                    errors.append(f"{where}: no individual with this name in the catalog")
                    continue
                relation = row["Relation (rider / owner / controller / companion)"]
                for person in re.split(r"\s+and\s+|,\s*", row["Character"]):
                    character_id = characters.get(person.split()[0]) if person else None
                    if character_id is None:
                        errors.append(f"{where}: no character called {person!r} in the catalog")
                        continue
                    riders.append(
                        {
                            "individual_id": individual_id,
                            "character_id": character_id,
                            "movie_id": movie,
                            "relation": relation,
                            "source_ids": source_ids(row["Source"], movie),
                            "confidence": row["Confidence"],
                        }
                    )

    if errors:
        print("Scene logs have problems; nothing was written:", *errors, sep="\n  ")
        return 1

    write_rows("appearances.csv", appearances)
    write_rows("rider_links.csv", riders)
    print(f"Wrote {len(appearances)} appearances and {len(riders)} rider links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

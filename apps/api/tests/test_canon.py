"""Canon endpoints, against the local database seeded from data/build/seed.sql.

Expected values come from data/build/dragons.json (the same build as the seed) wherever
possible, so these tests keep passing as the catalog is corrected.
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient

Catalog = list[dict[str, Any]]


def _entries(catalog: Catalog, kind: str) -> list[dict[str, Any]]:
    return [e for e in catalog if e["kind"] == kind]


def _movies_of(entry: dict[str, Any]) -> list[str]:
    return [a["movie"] for a in entry["appearances"]]


def test_movies_in_release_order(db_client: TestClient) -> None:
    response = db_client.get("/api/v1/movies")

    assert response.status_code == 200
    assert [m["id"] for m in response.json()] == ["httyd1", "httyd2", "httyd3"]


def test_species_list_matches_catalog(db_client: TestClient, catalog: Catalog) -> None:
    body = db_client.get("/api/v1/species").json()

    expected = sorted(_entries(catalog, "species"), key=lambda e: e["name"])
    assert [s["id"] for s in body] == [e["id"] for e in expected]
    for got, want in zip(body, expected, strict=True):
        assert got["class"] == want["class"]
        assert got["size"] == want["size"]
        assert got["confidence"] == want["confidence"]
        assert got["movies"] == _movies_of(want)


@pytest.mark.parametrize("movie", ["httyd1", "httyd2", "httyd3"])
def test_species_filter_by_movie(db_client: TestClient, catalog: Catalog, movie: str) -> None:
    body = db_client.get("/api/v1/species", params={"movie": movie}).json()

    expected = {e["id"] for e in _entries(catalog, "species") if movie in _movies_of(e)}
    assert {s["id"] for s in body} == expected
    assert all(movie in s["movies"] for s in body)


def test_unknown_movie_filter_returns_nothing(db_client: TestClient) -> None:
    assert db_client.get("/api/v1/species", params={"movie": "httyd9"}).json() == []


def test_species_detail(db_client: TestClient, catalog: Catalog) -> None:
    body = db_client.get("/api/v1/species/night_fury").json()

    want = next(e for e in catalog if e["id"] == "night_fury")
    assert body["name"] == "Night Fury"
    assert body["class"] == {"value": "Strike", "scope": "franchise"}
    assert [i["id"] for i in body["individuals"]] == want["known_individuals"]
    assert [a["movie_id"] for a in body["appearances"]] == _movies_of(want)
    assert [s["id"] for s in body["sources"]] == want["sources"]


def test_individuals_list_matches_catalog(db_client: TestClient, catalog: Catalog) -> None:
    body = db_client.get("/api/v1/individuals").json()

    expected = sorted(_entries(catalog, "individual"), key=lambda e: e["name"])
    assert [i["id"] for i in body] == [e["id"] for e in expected]
    assert all(
        i["species"]["id"] == e["species"]["id"] for i, e in zip(body, expected, strict=True)
    )


def test_individual_detail_has_riders_per_film(db_client: TestClient) -> None:
    body = db_client.get("/api/v1/individuals/skullcrusher").json()

    assert body["species"] == {"id": "rumblehorn", "name": "Rumblehorn"}
    riders = {(r["movie_id"], r["character"]["id"]) for r in body["riders"]}
    assert riders == {("httyd2", "stoick"), ("httyd3", "eret")}


def test_individual_with_two_riders(db_client: TestClient) -> None:
    body = db_client.get("/api/v1/individuals/barf_and_belch").json()

    in_first_film = [r["character"]["id"] for r in body["riders"] if r["movie_id"] == "httyd1"]
    assert in_first_film == ["ruffnut", "tuffnut"]


@pytest.mark.parametrize("path", ["/api/v1/species/no_such_dragon", "/api/v1/individuals/nobody"])
def test_unknown_id_is_404(db_client: TestClient, path: str) -> None:
    response = db_client.get(path)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_malformed_id_is_rejected(db_client: TestClient) -> None:
    assert db_client.get("/api/v1/species/Night-Fury").status_code == 422


def test_search_finds_species_and_individuals(db_client: TestClient) -> None:
    body = db_client.get("/api/v1/search", params={"q": "FURY"}).json()

    found = {(r["kind"], r["id"]) for r in body}
    assert {("species", "night_fury"), ("species", "light_fury")} <= found
    assert ("individual", "the_light_fury") in found
    light = next(r for r in body if r["id"] == "the_light_fury")
    assert light["species"] == {"id": "light_fury", "name": "Light Fury"}


def test_search_ranks_prefix_matches_first(db_client: TestClient) -> None:
    names = [r["name"] for r in db_client.get("/api/v1/search", params={"q": "night"}).json()]

    starts = [n.lower().startswith("night") for n in names]
    assert starts == sorted(starts, reverse=True)
    assert "The Night Lights" in names


def test_search_treats_wildcards_literally(db_client: TestClient) -> None:
    assert db_client.get("/api/v1/search", params={"q": "%"}).json() == []
    assert db_client.get("/api/v1/search", params={"q": "_"}).json() == []


def test_search_respects_limit(db_client: TestClient) -> None:
    body = db_client.get("/api/v1/search", params={"q": "e", "limit": 3}).json()

    assert len(body) == 3


@pytest.mark.parametrize("params", [{}, {"q": ""}, {"q": "x", "limit": 0}, {"q": "x", "limit": 51}])
def test_search_validates_input(db_client: TestClient, params: dict[str, str | int]) -> None:
    assert db_client.get("/api/v1/search", params=params).status_code == 422


def test_canon_is_public(db_client: TestClient) -> None:
    """No token needed (Plan.md §10)."""
    assert db_client.get("/api/v1/species").status_code == 200

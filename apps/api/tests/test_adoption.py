"""Adoption rules (Plan.md §9.5). No database needed."""

import pytest

from app.engines.adoption import (
    Adoption,
    InvalidName,
    clean_name,
    get_adoption,
    load_adoption,
    roll_dragon,
)
from app.engines.game_data import TRAITS, GameData, load_game_data


@pytest.fixture(scope="module")
def data() -> GameData:
    return load_game_data()


@pytest.fixture(scope="module")
def adoption() -> Adoption:
    return get_adoption()


def test_every_matchable_species_has_colors(data: GameData) -> None:
    load_adoption().check_species(data)  # raises if one is missing or unknown


def test_a_dragon_is_reproducible_but_varies_between_players(
    data: GameData, adoption: Adoption
) -> None:
    nadder = next(s for s in data.species if s.id == "deadly_nadder")
    assert roll_dragon(adoption, nadder, "a") == roll_dragon(adoption, nadder, "a")
    personalities = {
        tuple(roll_dragon(adoption, nadder, str(i)).personality.values()) for i in range(20)
    }
    assert len(personalities) > 1


@pytest.mark.parametrize("seed", [str(i) for i in range(50)])
def test_rolled_values_stay_within_the_rules(data: GameData, adoption: Adoption, seed: str) -> None:
    for species in data.species:
        dragon = roll_dragon(adoption, species, seed)
        assert set(dragon.personality) == set(TRAITS)
        assert all(0 <= v <= 100 for v in dragon.personality.values())
        # Six sigma from the species: practically never, so it would point at a bug.
        assert all(abs(dragon.personality[t] - species.traits[t]) <= 36 for t in TRAITS)
        for stat, cap in species.stat_caps.items():
            assert round(cap * 0.30) <= dragon.stats[stat] <= round(cap * 0.40)
        assert 1 <= len(dragon.quirks) <= 2
        assert adoption.color_hex(species.id, dragon.color_variant) is not None
        assert set(species.diet_likes) <= set(dragon.likes)
        assert set(species.diet_dislikes) <= set(dragon.dislikes)
        assert dragon.needs == {"hunger": 30, "energy": 80, "happiness": 60}
        assert dragon.trust == 20


@pytest.mark.parametrize(
    ("raw", "stored"),
    [
        ("Toothless", "Toothless"),
        ("  Ember   Wing ", "Ember Wing"),
        ("O'Malley", "O'Malley"),
        ("Sky-Fang", "Sky-Fang"),
        ("Åsa", "Åsa"),
        ("Cassandra", "Cassandra"),
        ("Scunthorpe", "Scunthorpe"),
    ],
)
def test_good_names_are_tidied(adoption: Adoption, raw: str, stored: str) -> None:
    assert clean_name(adoption, raw) == stored


@pytest.mark.parametrize(
    "raw",
    [
        "A",
        "A" * 21,
        "R2D2",
        "Fang!",
        "--",
        "Sky--Fang",
        "Shit",
        "big shit",
        "Fuck-Face",
    ],
)
def test_bad_names_are_refused(adoption: Adoption, raw: str) -> None:
    with pytest.raises(InvalidName):
        clean_name(adoption, raw)
